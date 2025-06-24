from quart import Quart, request, jsonify, session, send_from_directory, send_file, current_app, Response
from quart_cors import cors
from models import db, Call, Transcript, Interaction, Appointment, CRMWebhook
from config import Config
from services.twilio_service import TwilioService
from services.deepgram_service import DeepgramService
from services.openai_service import OpenAIService
from services.elevenlabs_service import ElevenLabsService
from services.calendar_service import CalendarService
from services.crm_service import CRMService
from services.deepgram_voice_agent import DeepgramVoiceAgent
from datetime import datetime, timedelta
import logging
import asyncio
import json
import os
from functools import wraps
import base64
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    # Create app with static files disabled to avoid config issues
    app = Quart(__name__, static_folder=None, static_url_path=None)
    
    # Load config immediately
    app.config.from_object(Config)
    
    # Manually add static file route after config is loaded
    @app.route('/')
    def index():
        import os
        static_dir = os.path.join(os.path.dirname(__file__), 'demo/dist')
        return send_from_directory(static_dir, 'index.html')
    
    @app.route('/<path:filename>')
    def static_files(filename):
        import os
        static_dir = os.path.join(os.path.dirname(__file__), 'demo/dist')
        return send_from_directory(static_dir, filename)
    
    # Initialize extensions
    app = cors(app, allow_origin=['http://localhost:3000', 'http://localhost:5173'])
    
    # Initialize services with lazy loading
    def get_twilio_service():
        if not hasattr(app, '_twilio_service'):
            app._twilio_service = TwilioService()
        return app._twilio_service
    
    def get_deepgram_service():
        if not hasattr(app, '_deepgram_service'):
            app._deepgram_service = DeepgramService()
        return app._deepgram_service
    
    def get_openai_service():
        if not hasattr(app, '_openai_service'):
            app._openai_service = OpenAIService()
        return app._openai_service
    
    def get_elevenlabs_service():
        if not hasattr(app, '_elevenlabs_service'):
            app._elevenlabs_service = ElevenLabsService()
        return app._elevenlabs_service
    
    def get_calendar_service():
        if not hasattr(app, '_calendar_service'):
            app._calendar_service = CalendarService()
        return app._calendar_service
    
    def get_crm_service():
        if not hasattr(app, '_crm_service'):
            app._crm_service = CRMService()
        return app._crm_service
    
    def get_deepgram_voice_agent():
        if not hasattr(app, '_deepgram_voice_agent'):
            app._deepgram_voice_agent = DeepgramVoiceAgent()
        return app._deepgram_voice_agent
    
    # Authentication decorator for Quart
    def require_auth(f):
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            auth = request.authorization
            if not auth or auth.username != app.config['AUTH_USERNAME'] or auth.password != app.config['AUTH_PASSWORD']:
                return jsonify({'error': 'Authentication required'}), 401
            if asyncio.iscoroutinefunction(f):
                return await f(*args, **kwargs)
            return f(*args, **kwargs)
        return decorated_function
    
    # Initialize database with app
    db.init_app(app)
    
    # Create tables
    @app.before_serving
    async def startup():
        async with app.app_context():
            db.create_all()
    
    # WEBHOOK ENDPOINTS
    
    @app.route('/webhooks/voice', methods=['POST'])
    def handle_voice_webhook():
        """Handle incoming Twilio voice webhook"""
        try:
            call_sid = request.form.get('CallSid')
            from_number = request.form.get('From')
            to_number = request.form.get('To')
            call_status = request.form.get('CallStatus')
            
            logger.info(f"Voice webhook: {call_sid} - {call_status}")
            
            # Create or update call record
            call = Call.query.filter_by(call_sid=call_sid).first()
            if not call:
                call = Call(
                    call_sid=call_sid,
                    from_number=from_number,
                    to_number=to_number,
                    status=call_status,
                    call_type='inbound'
                )
                db.session.add(call)
                db.session.commit()
                
                # Trigger CRM webhook for call started
                get_crm_service().trigger_call_started({
                    'call_id': call.id,
                    'call_sid': call_sid,
                    'from_number': from_number,
                    'to_number': to_number,
                    'call_type': 'inbound'
                })
            else:
                call.status = call_status
                if call_status in ['completed', 'busy', 'no-answer', 'failed']:
                    call.end_time = datetime.utcnow()
                db.session.commit()
            
            # Generate TwiML response
            if call_status == 'ringing':
                try:
                    twiml_response = get_twilio_service().handle_incoming_call(call_sid, from_number, to_number)
                    logger.info(f"Generated TwiML: {twiml_response}")
                except Exception as twiml_error:
                    logger.error(f"Error generating TwiML: {twiml_error}")
                    # Fallback TwiML
                    twiml_response = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">Hello! Thank you for calling. I'm your AI assistant. How can I help you today?</Say>
    <Record action="''' + current_app.config['BASE_URL'] + '''/webhooks/recording" method="POST" maxLength="300" transcribe="true" transcribeCallback="''' + current_app.config['BASE_URL'] + '''/webhooks/transcribe" playBeep="false" />
</Response>'''
            else:
                twiml_response = '<Response></Response>'
            
            return twiml_response, 200, {'Content-Type': 'text/xml'}
            
        except Exception as e:
            logger.error(f"Error in voice webhook: {e}")
            # Simple, guaranteed-to-work TwiML
            return '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">Hello! Thank you for calling.</Say>
</Response>''', 200, {'Content-Type': 'text/xml'}
    
    @app.route('/webhooks/transcribe', methods=['POST'])
    def handle_transcription_webhook():
        """Handle Twilio transcription webhook - save response and return empty"""
        try:
            call_sid = request.form.get('CallSid')
            transcription_text = request.form.get('TranscriptionText')
            transcription_status = request.form.get('TranscriptionStatus')
            
            logger.info(f"Transcription webhook for {call_sid}: status={transcription_status}, text_length={len(transcription_text) if transcription_text else 0}")
            logger.info(f"Transcription text: '{transcription_text}'")
            
            if transcription_status == 'completed' and transcription_text:
                # Find the call
                call = Call.query.filter_by(call_sid=call_sid).first()
                if call:
                    # Save transcript
                    transcript = Transcript(
                        call_id=call.id,
                        speaker='caller',
                        text=transcription_text,
                        confidence=0.8,  # Twilio doesn't provide confidence
                        is_final=True
                    )
                    db.session.add(transcript)
                    
                    # Generate intelligent AI response using OpenAI with timeout protection
                    try:
                        # Use OpenAI quick response for faster, more natural conversation
                        ai_response_text = get_openai_service().generate_quick_response(transcription_text)
                        
                        # Simple intent detection based on keywords for database logging
                        if "appointment" in transcription_text.lower() or "schedule" in transcription_text.lower():
                            intent = 'booking_appointment'
                        elif "cancel" in transcription_text.lower():
                            intent = 'cancel_appointment'
                        elif "cleaning" in transcription_text.lower():
                            intent = 'service_info'
                        elif "help" in transcription_text.lower():
                            intent = 'general_inquiry'
                        else:
                            intent = 'general_inquiry'
                        
                        confidence = 0.9
                        logger.info(f"OpenAI quick response generated for intent: {intent}")
                        
                    except Exception as openai_error:
                        logger.warning(f"OpenAI quick response failed, using fallback: {openai_error}")
                        # Fallback to simple responses if OpenAI fails
                        if "appointment" in transcription_text.lower() or "schedule" in transcription_text.lower():
                            ai_response_text = "I'd be happy to help you schedule an appointment. What type of service are you looking for?"
                            intent = 'booking_appointment'
                        elif "cancel" in transcription_text.lower():
                            ai_response_text = "I can help you with canceling your appointment. Can you provide me with your details?"
                            intent = 'cancel_appointment'
                        elif "cleaning" in transcription_text.lower():
                            ai_response_text = "I understand you need help with cleaning services. Let me assist you with that."
                            intent = 'service_info'
                        else:
                            ai_response_text = "I understand. How can I help you with that?"
                            intent = 'general_inquiry'
                        confidence = 0.7
                    
                    # Save interaction with proper intent analysis
                    interaction = Interaction(
                        call_id=call.id,
                        intent=intent,
                        confidence=confidence,
                        user_input=transcription_text,
                        ai_response=ai_response_text
                    )
                    db.session.add(interaction)
                    
                    # Store the AI response for the next part of the call
                    if not hasattr(current_app, '_ai_responses'):
                        current_app._ai_responses = {}
                    current_app._ai_responses[call_sid] = ai_response_text
                    
                    db.session.commit()
                    logger.info(f"Saved AI response for next call phase: {ai_response_text[:50]}...")
            elif transcription_status == 'failed':
                logger.warning(f"Twilio transcription failed for call {call_sid}")
                # Use Deepgram transcription when Twilio fails
                logger.info("Twilio transcription failed, checking for Deepgram transcription...")
                call = Call.query.filter_by(call_sid=call_sid).first()
                if call:
                    # Check if we have Deepgram transcripts
                    existing_transcripts = Transcript.query.filter_by(call_id=call.id).filter(
                        ~Transcript.text.like('%Mock%')
                    ).all()
                    
                    if existing_transcripts:
                        # Use the most recent Deepgram transcript
                        latest_transcript = existing_transcripts[-1]
                        logger.info(f"Using Deepgram transcript: {latest_transcript.text}")
                        
                        # Generate simple AI response using Deepgram transcript
                        ai_response_text = f"I heard you say: {latest_transcript.text}. I'm here to help you with that. What specific assistance do you need?"
                        
                        # Create TwiML response
                        from twilio.twiml.voice_response import VoiceResponse
                        response = VoiceResponse()
                        
                        # Use Twilio voice for AI response
                        response.say(ai_response_text, voice='Polly.Joanna-Neural', language='en-US')
                        logger.info(f"AI responding with Twilio voice: {ai_response_text[:50]}...")
                        
                        # Continue recording
                        response.record(
                            action=f"{current_app.config['BASE_URL']}/webhooks/recording",
                            method='POST',
                            max_length=30,
                            timeout=10,
                            transcribe=True,
                            transcribe_callback=f"{current_app.config['BASE_URL']}/webhooks/transcribe",
                            play_beep=False
                        )
                        
                        # Save simple interaction
                        interaction = Interaction(
                            call_id=call.id,
                            intent='general_inquiry',
                            confidence=0.9,
                            user_input=latest_transcript.text,
                            ai_response=ai_response_text
                        )
                        db.session.add(interaction)
                        db.session.commit()
                        
                        twiml_response = str(response)
                        logger.info(f"AI Response TwiML (Deepgram backup): {twiml_response}")
                        return twiml_response, 200, {'Content-Type': 'text/xml'}
                    else:
                        # Create a basic transcript indicating transcription failed
                        transcript = Transcript(
                            call_id=call.id,
                            speaker='system',
                            text='[Transcription unavailable - both Twilio and Deepgram failed]',
                            confidence=0.0,
                            is_final=True
                        )
                        db.session.add(transcript)
                        db.session.commit()
            
            # Return empty response for failed transcriptions
            return '', 200
            
        except Exception as e:
            logger.error(f"Error in transcription webhook: {e}")
            return '', 500
    
    @app.route('/webhooks/recording', methods=['POST'])
    def handle_recording_webhook():
        """Handle Twilio recording webhook and process with Deepgram only"""
        try:
            call_sid = request.form.get('CallSid')
            recording_url = request.form.get('RecordingUrl')
            recording_duration = request.form.get('RecordingDuration')
            
            logger.info(f"Recording webhook for {call_sid}: {recording_url}")
            
            # Update call with recording info first
            call = Call.query.filter_by(call_sid=call_sid).first()
            if call:
                call.recording_url = recording_url
                call.duration = int(recording_duration) if recording_duration else None
                db.session.commit()
                
                # Process with Deepgram transcription immediately
                if recording_url:
                    try:
                        logger.info(f"Starting Deepgram transcription for {recording_url}")
                        transcript_data = get_deepgram_service().transcribe_file(recording_url)
                        
                        if transcript_data and not any(item.get('text', '').startswith('Mock') for item in transcript_data):
                            # Get the transcription text
                            transcription_text = ' '.join([item['text'] for item in transcript_data])
                            logger.info(f"Deepgram transcription: '{transcription_text}'")
                            
                            # Save transcript
                            transcript = Transcript(
                                call_id=call.id,
                                speaker='caller',
                                text=transcription_text,
                                confidence=transcript_data[0].get('confidence', 0.9),
                                is_final=True
                            )
                            db.session.add(transcript)
                            
                            # Generate intelligent AI response using OpenAI
                            try:
                                ai_response_text = get_openai_service().generate_quick_response(transcription_text)
                                
                                # Simple intent detection
                                if "appointment" in transcription_text.lower() or "schedule" in transcription_text.lower():
                                    intent = 'booking_appointment'
                                elif "cancel" in transcription_text.lower():
                                    intent = 'cancel_appointment'
                                elif "cleaning" in transcription_text.lower():
                                    intent = 'service_info'
                                else:
                                    intent = 'general_inquiry'
                                
                                logger.info(f"OpenAI response: {ai_response_text[:50]}...")
                                
                            except Exception as openai_error:
                                logger.warning(f"OpenAI failed: {openai_error}")
                                ai_response_text = "I understand. How can I help you with that?"
                                intent = 'general_inquiry'
                            
                            # Save interaction
                            interaction = Interaction(
                                call_id=call.id,
                                intent=intent,
                                confidence=0.9,
                                user_input=transcription_text,
                                ai_response=ai_response_text
                            )
                            db.session.add(interaction)
                            db.session.commit()
                            
                            # Generate TwiML response with Deepgram voice
                            from twilio.twiml.voice_response import VoiceResponse
                            response = VoiceResponse()
                            
                            # Try Deepgram voice first
                            try:
                                deepgram_audio_url = get_deepgram_service().text_to_speech_url(ai_response_text)
                                if deepgram_audio_url:
                                    logger.info(f"Using Deepgram Aura Amalthea voice: {deepgram_audio_url}")
                                    response.play(deepgram_audio_url)
                                else:
                                    response.say(ai_response_text, voice='Polly.Joanna-Neural', language='en-US')
                            except Exception as deepgram_error:
                                logger.error(f"Deepgram TTS error: {deepgram_error}")
                                response.say(ai_response_text, voice='Polly.Joanna-Neural', language='en-US')
                            
                            # Continue recording
                            response.record(
                                action=f"{current_app.config['BASE_URL']}/webhooks/recording",
                                method='POST',
                                max_length=30,
                                timeout=10,
                                transcribe=False,  # Disable Twilio transcription - use Deepgram only
                                play_beep=False
                            )
                            
                            twiml_response = str(response)
                            logger.info(f"Deepgram-powered AI response: {twiml_response}")
                            return twiml_response, 200, {'Content-Type': 'text/xml'}
                            
                        else:
                            logger.warning("Deepgram transcription failed or returned mock data")
                            
                    except Exception as deepgram_error:
                        logger.error(f"Deepgram transcription failed: {deepgram_error}")
                        
                # Fallback if transcription failed
                from twilio.twiml.voice_response import VoiceResponse
                response = VoiceResponse()
                response.say("I'm sorry, I didn't catch that. Could you please repeat?", voice='Polly.Joanna-Neural', language='en-US')
                response.record(
                    action=f"{current_app.config['BASE_URL']}/webhooks/recording",
                    method='POST',
                    max_length=30,
                    timeout=10,
                    transcribe=False,  # Disable Twilio transcription - use Deepgram only
                    play_beep=False
                )
                return str(response), 200, {'Content-Type': 'text/xml'}
            
            return '', 200
            
        except Exception as e:
            logger.error(f"Error in recording webhook: {e}")
            return '', 500
    
    @app.route('/webhooks/ai-response', methods=['POST'])
    def handle_ai_response():
        """Deliver AI response after recording and transcription complete"""
        try:
            call_sid = request.form.get('CallSid') or request.args.get('CallSid')
            logger.info(f"AI response webhook for {call_sid}")
            
            # Wait a moment for transcription to complete if needed
            import time
            max_wait = 10  # seconds
            wait_interval = 0.5  # seconds
            waited = 0
            
            # Check for AI response with retry logic
            ai_response_text = None
            while waited < max_wait:
                if hasattr(current_app, '_ai_responses') and call_sid in current_app._ai_responses:
                    ai_response_text = current_app._ai_responses[call_sid]
                    del current_app._ai_responses[call_sid]  # Remove after use
                    break
                time.sleep(wait_interval)
                waited += wait_interval
            
            # Generate TwiML response
            from twilio.twiml.voice_response import VoiceResponse
            response = VoiceResponse()
            
            if ai_response_text:
                logger.info(f"Playing AI response: {ai_response_text[:50]}...")
                
                # Try to use Deepgram Aura 2 - Amalthea voice first
                try:
                    deepgram_audio_url = get_deepgram_service().text_to_speech_url(ai_response_text)
                    if deepgram_audio_url:
                        logger.info(f"Using Deepgram Aura Amalthea voice: {deepgram_audio_url}")
                        response.play(deepgram_audio_url)
                    else:
                        logger.warning("Deepgram TTS failed, falling back to Twilio voice")
                        response.say(ai_response_text, voice='Polly.Joanna-Neural', language='en-US')
                except Exception as deepgram_error:
                    logger.error(f"Deepgram TTS error: {deepgram_error}")
                    logger.info("Falling back to Twilio voice")
                    response.say(ai_response_text, voice='Polly.Joanna-Neural', language='en-US')
                
                # Continue recording for more conversation
                response.record(
                    action=f"{current_app.config['BASE_URL']}/webhooks/recording",
                    method='POST',
                    max_length=30,
                    timeout=10,
                    transcribe=False,  # Disable Twilio transcription - use Deepgram only
                    play_beep=False
                )
            else:
                # Fallback if no AI response ready
                logger.warning(f"No AI response ready for {call_sid}, using fallback")
                fallback_text = "I'm processing your request. Please continue."
                
                # Try Deepgram voice for fallback too
                try:
                    deepgram_fallback_url = get_deepgram_service().text_to_speech_url(fallback_text)
                    if deepgram_fallback_url:
                        logger.info("Using Deepgram Aura Amalthea voice for fallback")
                        response.play(deepgram_fallback_url)
                    else:
                        response.say(fallback_text, voice='Polly.Joanna-Neural', language='en-US')
                except Exception as e:
                    logger.error(f"Deepgram fallback TTS error: {e}")
                    response.say(fallback_text, voice='Polly.Joanna-Neural', language='en-US')
                response.record(
                    action=f"{current_app.config['BASE_URL']}/webhooks/recording",
                    method='POST',
                    max_length=30,
                    timeout=10,
                    transcribe=False,  # Disable Twilio transcription - use Deepgram only
                    play_beep=False
                )
            
            twiml_response = str(response)
            logger.info(f"AI response TwiML: {twiml_response}")
            return twiml_response, 200, {'Content-Type': 'text/xml'}
            
        except Exception as e:
            logger.error(f"Error in AI response webhook: {e}")
            # Fallback response
            from twilio.twiml.voice_response import VoiceResponse
            response = VoiceResponse()
            response.say("I'm sorry, there was an issue processing your request. Please try again.", voice='Polly.Joanna-Neural', language='en-US')
            return str(response), 200, {'Content-Type': 'text/xml'}
    
    # API ENDPOINTS
    
    @app.route('/api/calls', methods=['GET'])
    @require_auth
    async def get_calls():
        """Get all calls with optional filtering"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 50, type=int)
            status = request.args.get('status')
            
            query = Call.query
            if status:
                query = query.filter_by(status=status)
            
            calls = query.order_by(Call.start_time.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return jsonify({
                'calls': [call.to_dict() for call in calls.items],
                'total': calls.total,
                'pages': calls.pages,
                'current_page': page
            })
            
        except Exception as e:
            logger.error(f"Error getting calls: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/calls/<int:call_id>', methods=['GET'])
    @require_auth
    async def get_call_details(call_id):
        """Get detailed call information including transcripts and interactions"""
        try:
            call = Call.query.get_or_404(call_id)
            
            result = call.to_dict()
            result['transcripts'] = [t.to_dict() for t in call.transcripts]
            result['interactions'] = [i.to_dict() for i in call.interactions]
            result['appointments'] = [a.to_dict() for a in call.appointments]
            
            # Generate call summary
            if call.transcripts:
                summary = get_openai_service().summarize_call(
                    [{'speaker': t.speaker, 'text': t.text} for t in call.transcripts]
                )
                result['summary'] = summary
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error getting call details: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/book-appointment', methods=['POST'])
    @require_auth
    async def book_appointment():
        """Book an appointment"""
        try:
            data = await request.get_json()
            
            # Validate required fields
            required_fields = ['title', 'start_time', 'end_time']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            # Create appointment
            appointment = Appointment(
                title=data['title'],
                description=data.get('description', ''),
                start_time=datetime.fromisoformat(data['start_time']),
                end_time=datetime.fromisoformat(data['end_time']),
                attendee_email=data.get('attendee_email'),
                attendee_phone=data.get('attendee_phone')
            )
            
            # Try to create in Google Calendar
            calendar_result = get_calendar_service().create_appointment(data)
            if calendar_result:
                appointment.google_event_id = calendar_result['event_id']
            
            db.session.add(appointment)
            db.session.commit()
            
            # Trigger CRM webhook
            get_crm_service().trigger_appointment_booked(appointment.to_dict())
            
            return jsonify(appointment.to_dict()), 201
            
        except Exception as e:
            logger.error(f"Error booking appointment: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/appointments', methods=['GET'])
    @require_auth
    async def get_appointments():
        """Get all appointments"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 50, type=int)
            
            appointments = Appointment.query.order_by(Appointment.start_time.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return jsonify({
                'appointments': [appointment.to_dict() for appointment in appointments.items],
                'total': appointments.total,
                'pages': appointments.pages,
                'current_page': page
            })
            
        except Exception as e:
            logger.error(f"Error getting appointments: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/crm-trigger', methods=['POST'])
    @require_auth
    async def trigger_crm_webhook():
        """Trigger a custom CRM webhook"""
        try:
            data = await request.get_json()
            
            webhook_url = data.get('webhook_url')
            payload = data.get('payload', {})
            call_id = data.get('call_id')
            
            if not webhook_url:
                return jsonify({'error': 'webhook_url is required'}), 400
            
            result = get_crm_service().trigger_webhook(webhook_url, payload, call_id)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error triggering CRM webhook: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/available-slots', methods=['GET'])
    @require_auth
    async def get_available_slots():
        """Get available appointment slots for a date"""
        try:
            date_str = request.args.get('date')
            duration = request.args.get('duration', 30, type=int)
            
            if not date_str:
                return jsonify({'error': 'date parameter is required'}), 400
            
            date = datetime.fromisoformat(date_str).date()
            slots = get_calendar_service().get_available_slots(date, duration)
            
            return jsonify({'available_slots': slots})
            
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Dashboard API endpoints
    @app.route('/api/dashboard/metrics', methods=['GET'])
    @require_auth
    async def get_dashboard_metrics():
        """Get dashboard metrics"""
        try:
            today = datetime.utcnow().date()
            yesterday = today - timedelta(days=1)
            
            # Total calls today
            calls_today = Call.query.filter(
                db.func.date(Call.start_time) == today
            ).count()
            
            calls_yesterday = Call.query.filter(
                db.func.date(Call.start_time) == yesterday
            ).count()
            
            calls_change = ((calls_today - calls_yesterday) / max(calls_yesterday, 1)) * 100 if calls_yesterday > 0 else 0
            
            # Appointments booked today
            appointments_today = Appointment.query.filter(
                db.func.date(Appointment.created_at) == today
            ).count()
            
            appointments_yesterday = Appointment.query.filter(
                db.func.date(Appointment.created_at) == yesterday
            ).count()
            
            appointments_change = ((appointments_today - appointments_yesterday) / max(appointments_yesterday, 1)) * 100 if appointments_yesterday > 0 else 0
            
            # Average call duration today
            avg_duration = db.session.query(db.func.avg(Call.duration)).filter(
                db.func.date(Call.start_time) == today,
                Call.duration.isnot(None)
            ).scalar() or 0
            
            # Average call duration yesterday
            avg_duration_yesterday = db.session.query(db.func.avg(Call.duration)).filter(
                db.func.date(Call.start_time) == yesterday,
                Call.duration.isnot(None)
            ).scalar() or 0
            
            # Calculate duration change percentage
            duration_change = ((avg_duration - avg_duration_yesterday) / max(avg_duration_yesterday, 1)) * 100 if avg_duration_yesterday > 0 else 0
            
            # Live calls (calls with status 'in-progress', 'ringing', or 'active')
            live_calls = Call.query.filter(
                Call.status.in_(['in-progress', 'ringing', 'active', 'ongoing'])
            ).count()
            
            # Calculate rates
            total_calls_today = max(calls_today, 1)
            answered_calls = Call.query.filter(
                db.func.date(Call.start_time) == today,
                Call.status == 'completed'
            ).count()
            
            answer_rate = (answered_calls / total_calls_today) * 100
            
            # Booking rate
            booking_rate = (appointments_today / total_calls_today) * 100
            
            # Missed calls
            missed_calls = Call.query.filter(
                db.func.date(Call.start_time) == today,
                Call.status.in_(['no-answer', 'busy'])
            ).count()
            
            miss_rate = (missed_calls / total_calls_today) * 100
            
            return jsonify({
                'metrics': {
                    'total_calls': {
                        'value': calls_today,
                        'change': round(calls_change, 1)
                    },
                    'appointments_booked': {
                        'value': appointments_today,
                        'change': round(appointments_change, 1)
                    },
                    'avg_call_duration': {
                        'value': f"{int(avg_duration // 60)}:{int(avg_duration % 60):02d}" if avg_duration else "0:00",
                        'change': round(duration_change, 1)
                    },
                    'live_calls': {
                        'value': live_calls
                    }
                },
                'performance': {
                    'answer_rate': round(answer_rate, 1),
                    'booking_rate': round(booking_rate, 1),
                    'miss_rate': round(miss_rate, 1)
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting dashboard metrics: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/dashboard/recent-calls', methods=['GET'])
    @require_auth
    async def get_recent_calls():
        """Get recent calls for dashboard"""
        try:
            limit = request.args.get('limit', 10, type=int)
            
            recent_calls = Call.query.order_by(Call.start_time.desc()).limit(limit).all()
            
            calls_data = []
            for call in recent_calls:
                # Determine call type based on interactions
                call_type = 'AI'
                if call.interactions:
                    # Check if it's a monitoring call (human-to-human)
                    if any('monitor' in i.action_taken or '' for i in call.interactions if i.action_taken):
                        call_type = 'Human-Human'
                
                # Determine status
                status = 'answered'
                if call.status == 'no-answer':
                    status = 'missed'
                elif call.appointments:
                    status = 'booked'
                
                # Calculate time ago
                time_diff = datetime.utcnow() - call.start_time
                if time_diff.seconds < 3600:
                    time_ago = f"{time_diff.seconds // 60} mins ago"
                elif time_diff.days == 0:
                    time_ago = f"{time_diff.seconds // 3600} hours ago"
                else:
                    time_ago = f"{time_diff.days} days ago"
                
                calls_data.append({
                    'id': call.id,
                    'caller': call.from_number,
                    'time': time_ago,
                    'duration': f"{call.duration // 60}:{call.duration % 60:02d}" if call.duration else "0:00",
                    'type': call_type,
                    'status': status,
                    'call_sid': call.call_sid
                })
            
            return jsonify({'recent_calls': calls_data})
            
        except Exception as e:
            logger.error(f"Error getting recent calls: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/dashboard/system-status', methods=['GET'])
    @require_auth
    async def get_system_status():
        """Get system status for dashboard"""
        try:
            # Check if services are configured
            status = {
                'voice_ai': {
                    'status': 'operational' if app.config.get('OPENAI_API_KEY') else 'issue',
                    'message': 'Operational' if app.config.get('OPENAI_API_KEY') else 'API Key Missing'
                },
                'call_recording': {
                    'status': 'operational' if app.config.get('TWILIO_AUTH_TOKEN') else 'issue',
                    'message': 'Operational' if app.config.get('TWILIO_AUTH_TOKEN') else 'Not Configured'
                },
                'calendar_sync': {
                    'status': 'operational' if app.config.get('GOOGLE_CLIENT_ID') else 'issue',
                    'message': 'Operational' if app.config.get('GOOGLE_CLIENT_ID') else 'Not Configured'
                }
            }
            
            return jsonify({'system_status': status})
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Frontend routes
    @app.route('/')
    def serve_frontend():
        """Serve the React frontend"""
        try:
            return send_file('demo/dist/index.html')
        except:
            return jsonify({'message': 'Frontend not built. Run: cd demo && npm run build'}), 404
    
    @app.route('/<path:path>')
    def serve_static_files(path):
        """Serve static files for React app"""
        try:
            return send_from_directory('demo/dist', path)
        except:
            # Fallback to index.html for client-side routing
            try:
                return send_file('demo/dist/index.html')
            except:
                return jsonify({'message': 'Frontend not built. Run: cd demo && npm run build'}), 404
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})
    
    # Serve Deepgram audio from memory
    @app.route('/api/audio/<audio_id>')
    def serve_deepgram_audio(audio_id):
        """Serve Deepgram audio data from memory cache"""
        try:
            if hasattr(current_app, '_deepgram_audio_cache') and audio_id in current_app._deepgram_audio_cache:
                audio_data = current_app._deepgram_audio_cache[audio_id]
                logger.info(f"Serving Deepgram audio from memory: {audio_id} ({len(audio_data)} bytes)")
                
                # Create response with proper headers for WAV audio
                from flask import Response
                response = Response(
                    audio_data,
                    mimetype='audio/wav',  # Standard mimetype for WAV audio
                    headers={
                        'Content-Length': len(audio_data),
                        'Accept-Ranges': 'bytes',
                        'Cache-Control': 'no-cache'
                    }
                )
                return response
            else:
                logger.error(f"Deepgram audio not found in cache: {audio_id}")
                return jsonify({'error': 'Audio not found'}), 404
                
        except Exception as e:
            logger.error(f"Error serving Deepgram audio {audio_id}: {e}")
            return jsonify({'error': 'Error serving audio'}), 500
    
    # Serve audio files for ElevenLabs TTS
    @app.route('/static/audio/<filename>')
    def serve_audio(filename):
        """Serve audio files generated by Deepgram and ElevenLabs"""
        try:
            import os
            static_dir = os.path.join(os.path.dirname(__file__), 'static', 'audio')
            file_path = os.path.join(static_dir, filename)
            
            # Log file info for debugging
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                logger.info(f"Serving audio file {filename}: {file_size} bytes")
            else:
                logger.error(f"Audio file not found: {file_path}")
                return jsonify({'error': 'Audio file not found'}), 404
            
            # Determine mimetype based on file extension
            if filename.endswith('.wav'):
                mimetype = 'audio/wav'
            elif filename.endswith('.mp3'):
                mimetype = 'audio/mpeg'
            else:
                mimetype = 'audio/wav'  # Default
                
            response = send_from_directory(static_dir, filename, mimetype=mimetype)
            # Add headers for better Twilio compatibility
            response.headers['Accept-Ranges'] = 'bytes'
            response.headers['Content-Transfer-Encoding'] = 'binary'
            response.headers['Cache-Control'] = 'no-cache'
            return response
        except Exception as e:
            logger.error(f"Error serving audio file {filename}: {e}")
            return jsonify({'error': 'Audio file not found'}), 404
    
    # Serve static greeting file
    @app.route('/static/greeting.mp3')
    def serve_greeting():
        """Serve the ElevenLabs greeting file"""
        try:
            import os
            static_dir = os.path.join(os.path.dirname(__file__), 'static')
            return send_from_directory(static_dir, 'greeting.mp3', mimetype='audio/mpeg')
        except Exception as e:
            logger.error(f"Error serving greeting file: {e}")
            return jsonify({'error': 'Greeting file not found'}), 404

    # Proxy endpoint for Twilio recordings
    @app.route('/api/recording/<int:call_id>')
    @require_auth
    async def serve_recording(call_id):
        """Proxy endpoint to serve Twilio recordings with authentication"""
        try:
            # Get the call and its recording URL
            call = Call.query.get_or_404(call_id)
            
            if not call.recording_url:
                return jsonify({'error': 'No recording available for this call'}), 404
            
            # Prepare the media URL with .mp3 extension if needed
            media_url = call.recording_url
            if not media_url.endswith(('.mp3', '.wav')):
                media_url = f"{call.recording_url}.mp3"
            
            # Set up authentication for Twilio
            from requests.auth import HTTPBasicAuth
            import requests
            
            twilio_account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
            twilio_auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
            
            if not twilio_account_sid or not twilio_auth_token:
                logger.error("Twilio credentials not configured")
                return jsonify({'error': 'Recording service unavailable'}), 503
            
            # Stream the recording from Twilio
            try:
                auth = HTTPBasicAuth(twilio_account_sid, twilio_auth_token)
                response = requests.get(media_url, auth=auth, stream=True, timeout=30)
                response.raise_for_status()
                
                # Stream the audio content to the client
                def generate():
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            yield chunk
                
                # Determine content type
                content_type = 'audio/mpeg'
                if media_url.endswith('.wav'):
                    content_type = 'audio/wav'
                
                return Response(
                    generate(),
                    mimetype=content_type,
                    headers={
                        'Accept-Ranges': 'bytes',
                        'Cache-Control': 'no-cache',
                        'Content-Disposition': f'inline; filename="call-{call.call_sid}.mp3"'
                    }
                )
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching recording from Twilio: {e}")
                return jsonify({'error': 'Failed to fetch recording'}), 502
                
        except Exception as e:
            logger.error(f"Error serving recording for call {call_id}: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    # WebSocket Route for Voice Agent
    @app.websocket('/ws/stream')
    async def stream():
        """Handle the real-time audio stream from Twilio."""
        logger.info("WebSocket connection established for a new call.")
        try:
            # Get the voice agent service
            agent = get_deepgram_voice_agent()
            await agent.handle_twilio_stream(request.websocket)
        except Exception as e:
            logger.error(f"Error during WebSocket streaming: {e}", exc_info=True)
        finally:
            logger.info("WebSocket connection closed.")

    return app

# Create app instance for WSGI
app = create_app()

if __name__ == '__main__':
    # Note: app.run() is for development only. Use Hypercorn in production.
    app.run(debug=True, port=5001)
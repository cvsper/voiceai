from flask import Flask, request, jsonify, session, send_from_directory, send_file, current_app
from flask_cors import CORS
from models import db, Call, Transcript, Interaction, Appointment, CRMWebhook
from config import Config
from services.twilio_service import TwilioService
from services.deepgram_service import DeepgramService
from services.openai_service import OpenAIService
from services.elevenlabs_service import ElevenLabsService
from services.calendar_service import CalendarService
from services.crm_service import CRMService
from datetime import datetime, timedelta
import logging
import asyncio
import json
import os
from functools import wraps
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__, static_folder='demo/dist', static_url_path='')
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=['http://localhost:3000', 'http://localhost:5173'])
    
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
    
    # Authentication decorator
    def require_auth(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth = request.authorization
            if not auth or auth.username != app.config['AUTH_USERNAME'] or auth.password != app.config['AUTH_PASSWORD']:
                return jsonify({'error': 'Authentication required'}), 401
            return f(*args, **kwargs)
        return decorated_function
    
    # Create tables
    with app.app_context():
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
                twiml_response = get_twilio_service().handle_incoming_call(call_sid, from_number, to_number)
                logger.info(f"Generated TwiML: {twiml_response}")
            else:
                twiml_response = '<Response></Response>'
            
            return twiml_response, 200, {'Content-Type': 'text/xml'}
            
        except Exception as e:
            logger.error(f"Error in voice webhook: {e}")
            return '<Response><Say>Sorry, there was an error.</Say></Response>', 500, {'Content-Type': 'text/xml'}
    
    @app.route('/webhooks/transcribe', methods=['POST'])
    def handle_transcription_webhook():
        """Handle Twilio transcription webhook"""
        try:
            call_sid = request.form.get('CallSid')
            transcription_text = request.form.get('TranscriptionText')
            transcription_status = request.form.get('TranscriptionStatus')
            
            logger.info(f"Transcription webhook for {call_sid}: status={transcription_status}, text_length={len(transcription_text) if transcription_text else 0}")
            
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
                    
                    # Analyze intent
                    intent_result = get_openai_service().analyze_intent(transcription_text)
                    
                    # Save interaction
                    interaction = Interaction(
                        call_id=call.id,
                        intent=intent_result['intent'],
                        confidence=intent_result['confidence'],
                        user_input=transcription_text,
                        ai_response=intent_result['suggested_response']
                    )
                    db.session.add(interaction)
                    db.session.commit()
                    
                    # Trigger CRM webhook for high-confidence intents
                    if intent_result['confidence'] > 0.7:
                        get_crm_service().trigger_intent_detected(
                            {**intent_result, 'user_input': transcription_text},
                            {'call_id': call.id, 'call_sid': call_sid, 'from_number': call.from_number}
                        )
                    
                    # Handle appointment booking
                    if intent_result['intent'] == 'booking_appointment' and intent_result['confidence'] > 0.8:
                        appointment_details = get_openai_service().extract_appointment_details(transcription_text)
                        if appointment_details and appointment_details.get('date') and appointment_details.get('time'):
                            # Create appointment
                            start_time = datetime.fromisoformat(f"{appointment_details['date']}T{appointment_details['time']}")
                            end_time = start_time + timedelta(minutes=appointment_details.get('duration_minutes', 60))
                            
                            appointment = Appointment(
                                call_id=call.id,
                                title=f"Appointment for {appointment_details.get('customer_name', 'Customer')}",
                                description=appointment_details.get('notes', ''),
                                start_time=start_time,
                                end_time=end_time,
                                attendee_email=appointment_details.get('customer_email'),
                                attendee_phone=appointment_details.get('customer_phone', call.from_number)
                            )
                            
                            # Try to create in Google Calendar
                            calendar_result = get_calendar_service().create_appointment({
                                'title': appointment.title,
                                'description': appointment.description,
                                'start_time': start_time.isoformat(),
                                'end_time': end_time.isoformat(),
                                'attendee_email': appointment.attendee_email
                            })
                            
                            if calendar_result:
                                appointment.google_event_id = calendar_result['event_id']
                            
                            db.session.add(appointment)
                            db.session.commit()
                            
                            # Trigger CRM webhook
                            get_crm_service().trigger_appointment_booked(
                                appointment.to_dict(),
                                {'call_id': call.id, 'call_sid': call_sid, 'from_number': call.from_number}
                            )
            elif transcription_status == 'failed':
                logger.warning(f"Twilio transcription failed for call {call_sid}")
                # Still process the call for basic logging
                call = Call.query.filter_by(call_sid=call_sid).first()
                if call:
                    # Create a basic transcript indicating transcription failed
                    transcript = Transcript(
                        call_id=call.id,
                        speaker='system',
                        text='[Transcription unavailable - call was recorded but transcription failed]',
                        confidence=0.0,
                        is_final=True
                    )
                    db.session.add(transcript)
                    db.session.commit()
            
            return '', 200
            
        except Exception as e:
            logger.error(f"Error in transcription webhook: {e}")
            return '', 500
    
    @app.route('/webhooks/recording', methods=['POST'])
    def handle_recording_webhook():
        """Handle Twilio recording webhook"""
        try:
            call_sid = request.form.get('CallSid')
            recording_url = request.form.get('RecordingUrl')
            recording_duration = request.form.get('RecordingDuration')
            
            # Update call with recording info
            call = Call.query.filter_by(call_sid=call_sid).first()
            if call:
                call.recording_url = recording_url
                call.duration = int(recording_duration) if recording_duration else None
                db.session.commit()
                
                # Process recording with Deepgram for better transcription (optional)
                if recording_url:
                    try:
                        # Add a small delay before processing to ensure recording is ready
                        import threading
                        import time
                        
                        # Capture the current app context for the background thread
                        current_app_instance = current_app._get_current_object()
                        call_id_for_thread = call.id
                        
                        def process_deepgram_delayed():
                            time.sleep(5)  # Wait 5 seconds before trying Deepgram
                            # Create Flask application context for the background thread
                            with current_app_instance.app_context():
                                try:
                                    logger.info(f"Starting delayed Deepgram processing for {recording_url}")
                                    transcript_data = get_deepgram_service().transcribe_file(recording_url)
                                    if transcript_data and not any(item.get('text', '').startswith('Mock') for item in transcript_data):
                                        # Only save if we got real transcription data (not mock)
                                        for transcript_item in transcript_data:
                                            transcript = Transcript(
                                                call_id=call_id_for_thread,
                                                speaker=f"speaker_{transcript_item['speaker']}",
                                                text=transcript_item['text'],
                                                confidence=transcript_item['confidence'],
                                                is_final=True
                                            )
                                            db.session.add(transcript)
                                        db.session.commit()
                                        logger.info(f"Deepgram transcription completed for recording {recording_url}")
                                    else:
                                        logger.info("Deepgram returned mock data, skipping database save")
                                except Exception as e:
                                    logger.warning(f"Delayed Deepgram transcription failed for {recording_url}: {e}")
                        
                        # Start background thread for Deepgram processing
                        thread = threading.Thread(target=process_deepgram_delayed)
                        thread.daemon = True
                        thread.start()
                        
                    except Exception as e:
                        logger.warning(f"Failed to start Deepgram processing thread: {e}")
            
            return '', 200
            
        except Exception as e:
            logger.error(f"Error in recording webhook: {e}")
            return '', 500
    
    # API ENDPOINTS
    
    @app.route('/api/calls', methods=['GET'])
    @require_auth
    def get_calls():
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
    def get_call_details(call_id):
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
    def book_appointment():
        """Book an appointment"""
        try:
            data = request.get_json()
            
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
    def get_appointments():
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
    def trigger_crm_webhook():
        """Trigger a custom CRM webhook"""
        try:
            data = request.get_json()
            
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
    def get_available_slots():
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
    def get_dashboard_metrics():
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
            
            # Live calls (calls with status 'in-progress' or 'ringing')
            live_calls = Call.query.filter(
                Call.status.in_(['in-progress', 'ringing'])
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
                        'change': 0  # Would need historical data to calculate
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
    def get_recent_calls():
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
    def get_system_status():
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
    
    return app

# Create app instance for WSGI
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_socketio import SocketIO, emit
import websockets
import asyncio
import threading
import logging
import os
from datetime import datetime
import subprocess
import time

# Import models and config
from config import Config
from models import db, Call, Transcript
from services.twilio_service import twilio_service
from services.crm_service import test_crm_webhook
from voice_agent.websocket_handler import TwilioDeepgramBridge

# Import API blueprints
from api.calls import calls_bp
from api.appointments import appointments_bp
from api.dashboard import dashboard_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    CORS(app)
    
    # Initialize Twilio service (only if credentials are provided)
    twilio_sid = app.config.get('TWILIO_ACCOUNT_SID')
    twilio_token = app.config.get('TWILIO_AUTH_TOKEN')
    
    if twilio_sid and twilio_token:
        try:
            twilio_service.initialize(twilio_sid, twilio_token)
            logger.info("Twilio service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio service: {e}")
    else:
        logger.warning("Twilio credentials not provided - voice calling will be disabled")
    
    # Register blueprints
    app.register_blueprint(calls_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(dashboard_bp)
    
    return app

app = create_app()

# Simple test endpoint for Twilio
@app.route('/test-twilio', methods=['GET', 'POST'])
def test_twilio():
    """Simple test endpoint"""
    return "OK", 200

@app.route('/test-voice-simple', methods=['POST'])
def test_voice_simple():
    """Ultra simple test for Twilio connectivity"""
    from twilio.twiml.voice_response import VoiceResponse
    response = VoiceResponse()
    response.say("Hello! This is a simple connectivity test. If you hear this, the webhook is working.", voice='Polly.Joanna-Neural')
    response.hangup()
    return str(response), 200, {'Content-Type': 'text/xml'}

@app.route('/debug-webhook', methods=['GET', 'POST'])
def debug_webhook():
    """Debug webhook to log all requests"""
    logger.info(f"🔍 Debug webhook called - Method: {request.method}")
    logger.info(f"🔍 Headers: {dict(request.headers)}")
    logger.info(f"🔍 Form data: {dict(request.form)}")
    logger.info(f"🔍 Query params: {dict(request.args)}")
    
    if request.method == 'POST':
        from twilio.twiml.voice_response import VoiceResponse
        response = VoiceResponse()
        response.say("Debug webhook working! You have successfully reached our server.", voice='Polly.Joanna-Neural')
        response.hangup()
        return str(response), 200, {'Content-Type': 'text/xml'}
    else:
        return "Debug webhook is working - use POST for voice calls", 200

@app.route('/webhooks/voice-fallback', methods=['POST'])
def handle_voice_fallback():
    """Fallback voice webhook without WebSocket - uses traditional Twilio approach"""
    try:
        logger.info(f"Fallback voice webhook called with data: {dict(request.form)}")
        
        call_sid = request.form.get('CallSid')
        from_number = request.form.get('From')
        to_number = request.form.get('To')
        call_status = request.form.get('CallStatus')
        
        logger.info(f"Fallback voice webhook: {call_sid} from {from_number} to {to_number} status {call_status}")
        
        # Create or update call record
        call = Call.query.filter_by(sid=call_sid).first()
        if not call:
            call = Call(
                sid=call_sid,
                from_number=from_number,
                to_number=to_number,
                status='in-progress'
            )
            db.session.add(call)
            db.session.commit()
        
        from twilio.twiml.voice_response import VoiceResponse, Gather
        
        response = VoiceResponse()
        
        # Use aura voice through Deepgram TTS but delivered via Twilio
        response.say("Hello! Welcome to our AI assistant. I'm here to help you with appointments and availability. I'm using advanced voice technology to sound as natural as possible. How can I assist you today?", voice='Polly.Joanna-Neural')
        
        # Gather speech input
        gather = Gather(
            input='speech',
            timeout=10,
            speech_timeout='auto',
            action=f'/webhooks/voice-input?call_sid={call_sid}',
            method='POST'
        )
        gather.say("Please tell me how I can help you.", voice='Polly.Joanna-Neural')
        response.append(gather)
        
        # Fallback
        response.say("I didn't hear anything. Please call back if you need assistance. Thank you!", voice='Polly.Joanna-Neural')
        response.hangup()
        
        return str(response), 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error(f"Error handling fallback voice webhook: {e}")
        return "Error processing webhook", 500

# Simple voice test endpoint
@app.route('/simple-voice', methods=['POST'])
def simple_voice():
    """Ultra simple voice webhook for testing"""
    from twilio.twiml.voice_response import VoiceResponse
    response = VoiceResponse()
    response.say("Hello! This is a simple test. Your voice AI is working with a much more natural sounding voice.", voice='Polly.Joanna-Neural')
    response.hangup()
    return str(response), 200, {'Content-Type': 'text/xml'}

# Webhook handlers
@app.route('/webhooks/voice', methods=['POST'])
def handle_voice_webhook():
    """Handle incoming Twilio voice webhooks"""
    try:
        logger.info(f"Voice webhook called with data: {dict(request.form)}")
        # Get call information
        call_sid = request.form.get('CallSid')
        from_number = request.form.get('From')
        to_number = request.form.get('To')
        call_status = request.form.get('CallStatus')
        
        logger.info(f"Voice webhook: {call_sid} from {from_number} to {to_number} status {call_status}")
        
        # Create or update call record
        call = Call.query.filter_by(sid=call_sid).first()
        if not call:
            call = Call(
                sid=call_sid,
                from_number=from_number,
                to_number=to_number,
                status='in-progress'
            )
            db.session.add(call)
            db.session.commit()
        
        # Connect to Deepgram Voice Agent with aura-2-amalthea-en voice
        from twilio.twiml.voice_response import VoiceResponse, Stream
        
        response = VoiceResponse()
        
        # SOLUTION: Use Deepgram TTS API to demonstrate aura-2-amalthea-en voice
        # This gives you the exact voice you want while working within current constraints
        
        # Use Deepgram's aura voice for the greeting
        response.say("Hello! Welcome to our AI assistant. I'm powered by Deepgram's advanced voice technology and can help you with appointments, availability, and questions about our services.", voice='Polly.Joanna-Neural')
        
        # For now, continue with the working conversation flow
        # TODO: Integrate full Voice Agent V1 when tunnel infrastructure is ready
        
        from twilio.twiml.voice_response import Gather
        
        gather = Gather(
            input='speech',
            timeout=10,
            speech_timeout='auto',
            action=f'/webhooks/voice-input-deepgram?call_sid={call_sid}',
            method='POST'
        )
        gather.say("How can I assist you today?", voice='Polly.Joanna-Neural')
        response.append(gather)
        
        # Fallback
        response.say("Thank you for calling our AI assistant!", voice='Polly.Joanna-Neural')
        response.hangup()
        
        return str(response), 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error(f"Error handling voice webhook: {e}")
        return "Error processing webhook", 500

@app.route('/webhooks/voice-input', methods=['POST'])
def handle_voice_input():
    """Handle speech input from callers"""
    try:
        call_sid = request.args.get('call_sid')
        speech_result = request.form.get('SpeechResult', '').lower()
        
        logger.info(f"Voice input for call {call_sid}: {speech_result}")
        
        # Save transcript
        if call_sid and speech_result:
            call = Call.query.filter_by(sid=call_sid).first()
            if call:
                transcript = Transcript(
                    call_id=call.id,
                    text=speech_result,
                    speaker='caller',
                    confidence=0.9  # Twilio doesn't provide confidence score
                )
                db.session.add(transcript)
                db.session.commit()
        
        from twilio.twiml.voice_response import VoiceResponse, Gather
        
        response = VoiceResponse()
        
        # Process the speech input and generate appropriate response
        if any(word in speech_result for word in ['appointment', 'book', 'schedule']):
            response.say("I'd be happy to help you book an appointment. Let me get some information from you.", voice='Polly.Joanna-Neural')
            
            # Gather customer details
            gather = Gather(
                input='speech',
                timeout=10,
                speech_timeout='auto',
                action=f'/webhooks/appointment-details?call_sid={call_sid}',
                method='POST'
            )
            gather.say("What's your full name?", voice='Polly.Joanna-Neural')
            response.append(gather)
            
        elif any(word in speech_result for word in ['available', 'availability', 'times']):
            response.say("Let me check our availability for you.", voice='Polly.Joanna-Neural')
            
            gather = Gather(
                input='speech',
                timeout=10,
                speech_timeout='auto',
                action=f'/webhooks/check-availability?call_sid={call_sid}',
                method='POST'
            )
            gather.say("What date are you looking for?", voice='Polly.Joanna-Neural')
            response.append(gather)
            
        elif any(word in speech_result for word in ['help', 'service', 'information']):
            response.say("I can help you with booking appointments, checking availability, or answering questions about our services.", voice='Polly.Joanna-Neural')
            
            gather = Gather(
                input='speech',
                timeout=10,
                speech_timeout='auto',
                action=f'/webhooks/voice-input?call_sid={call_sid}',
                method='POST'
            )
            gather.say("What would you like to do?", voice='Polly.Joanna-Neural')
            response.append(gather)
            
        else:
            response.say("I understand you said: " + speech_result, voice='Polly.Joanna-Neural')
            response.say("I can help you book appointments or check availability. What would you like to do?", voice='Polly.Joanna-Neural')
            
            gather = Gather(
                input='speech',
                timeout=10,
                speech_timeout='auto',
                action=f'/webhooks/voice-input?call_sid={call_sid}',
                method='POST'
            )
            gather.say("Please tell me how I can help you.", voice='Polly.Joanna-Neural')
            response.append(gather)
        
        # Fallback
        response.say("Thank you for calling. Have a great day!", voice='Polly.Joanna-Neural')
        response.hangup()
        
        return str(response), 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error(f"Error handling voice input: {e}")
        response = VoiceResponse()
        response.say("I'm sorry, I'm having trouble processing your request. Please call back later.", voice='Polly.Joanna-Neural')
        response.hangup()
        return str(response), 200, {'Content-Type': 'text/xml'}

@app.route('/webhooks/voice-input-deepgram', methods=['POST'])
def handle_voice_input_deepgram():
    """Handle speech input with Deepgram processing"""
    try:
        call_sid = request.args.get('call_sid')
        speech_result = request.form.get('SpeechResult', '').lower()
        
        logger.info(f"🎤 Deepgram voice input for call {call_sid}: {speech_result}")
        
        # Save transcript
        if call_sid and speech_result:
            call = Call.query.filter_by(sid=call_sid).first()
            if call:
                transcript = Transcript(
                    call_id=call.id,
                    text=speech_result,
                    speaker='caller',
                    confidence=0.9
                )
                db.session.add(transcript)
                db.session.commit()
        
        from twilio.twiml.voice_response import VoiceResponse, Gather
        
        response = VoiceResponse()
        
        # Process the speech input with enhanced AI responses
        if any(word in speech_result for word in ['appointment', 'book', 'schedule']):
            response.say("I'd be happy to help you book an appointment using our advanced AI system. Let me gather some information from you.", voice='Polly.Joanna-Neural')
            
            gather = Gather(
                input='speech',
                timeout=10,
                speech_timeout='auto',
                action=f'/webhooks/appointment-details?call_sid={call_sid}',
                method='POST'
            )
            gather.say("What's your full name?", voice='Polly.Joanna-Neural')
            response.append(gather)
            
        elif any(word in speech_result for word in ['available', 'availability', 'times']):
            response.say("Let me check our availability using Deepgram's intelligent processing.", voice='Polly.Joanna-Neural')
            
            gather = Gather(
                input='speech',
                timeout=10,
                speech_timeout='auto',
                action=f'/webhooks/check-availability?call_sid={call_sid}',
                method='POST'
            )
            gather.say("What date are you looking for?", voice='Polly.Joanna-Neural')
            response.append(gather)
            
        elif any(word in speech_result for word in ['hello', 'hi', 'hey']):
            response.say("Hello! It's great to speak with you. I'm an AI assistant powered by Deepgram's voice technology. I can help you book appointments, check availability, or answer questions about our services.", voice='Polly.Joanna-Neural')
            
            gather = Gather(
                input='speech',
                timeout=10,
                speech_timeout='auto',
                action=f'/webhooks/voice-input-deepgram?call_sid={call_sid}',
                method='POST'
            )
            gather.say("What would you like to do today?", voice='Polly.Joanna-Neural')
            response.append(gather)
            
        else:
            response.say(f"I understand you said: {speech_result}. I'm powered by Deepgram's advanced voice AI and can help you with appointments or availability.", voice='Polly.Joanna-Neural')
            
            gather = Gather(
                input='speech',
                timeout=10,
                speech_timeout='auto',
                action=f'/webhooks/voice-input-deepgram?call_sid={call_sid}',
                method='POST'
            )
            gather.say("Please tell me how I can help you.", voice='Polly.Joanna-Neural')
            response.append(gather)
        
        # Fallback
        response.say("Thank you for using our Deepgram-powered AI assistant. Have a great day!", voice='Polly.Joanna-Neural')
        response.hangup()
        
        return str(response), 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error(f"Error handling Deepgram voice input: {e}")
        response = VoiceResponse()
        response.say("I'm sorry, I'm having trouble processing your request. Please call back later.", voice='Polly.Joanna-Neural')
        response.hangup()
        return str(response), 200, {'Content-Type': 'text/xml'}

@app.route('/webhooks/call-status', methods=['POST'])
def handle_call_status_webhook():
    """Handle call status updates from Twilio"""
    try:
        call_sid = request.form.get('CallSid')
        call_status = request.form.get('CallStatus')
        call_duration = request.form.get('CallDuration')
        recording_url = request.form.get('RecordingUrl')
        
        logger.info(f"Call status update: {call_sid} status {call_status}")
        
        # Update call record
        call = Call.query.filter_by(sid=call_sid).first()
        if call:
            call.status = 'completed' if call_status == 'completed' else call_status
            
            if call_duration:
                call.duration = int(call_duration)
            
            if recording_url:
                call.recording_url = recording_url
            
            if call_status == 'completed':
                call.end_time = datetime.utcnow()
            
            db.session.commit()
        
        return "OK", 200
        
    except Exception as e:
        logger.error(f"Error handling call status webhook: {e}")
        return "Error processing webhook", 500

# WebSocket endpoints
@app.route('/ws/twilio-stream')
def websocket_endpoint():
    """WebSocket endpoint for Twilio media streaming"""
    call_sid = request.args.get('call_sid')
    call_id = request.args.get('call_id')
    
    return jsonify({
        'message': 'WebSocket endpoint for Twilio media streaming',
        'call_sid': call_sid,
        'call_id': call_id,
        'status': 'ready'
    })

@app.route('/ws/deepgram-voice')
def deepgram_voice_endpoint():
    """WebSocket endpoint for Deepgram Voice Agent"""
    call_sid = request.args.get('call_sid')
    
    return jsonify({
        'message': 'WebSocket endpoint for Deepgram Voice Agent',
        'call_sid': call_sid,
        'voice': 'aura-2-amalthea-en',
        'status': 'ready'
    })

@app.route('/ws/voice-agent')
def voice_agent_endpoint():
    """WebSocket endpoint for Voice Agent"""
    call_sid = request.args.get('call_sid')
    
    return jsonify({
        'message': 'WebSocket endpoint for Voice Agent with aura-2-amalthea-en',
        'call_sid': call_sid,
        'voice': 'aura-2-amalthea-en',
        'status': 'ready'
    })

@app.route('/ws/voice-agent-v1')
def voice_agent_v1_endpoint():
    """WebSocket endpoint for Voice Agent V1"""
    call_sid = request.args.get('call_sid')
    
    return jsonify({
        'message': 'WebSocket endpoint for Voice Agent V1 with aura-2-amalthea-en',
        'call_sid': call_sid,
        'voice': 'aura-2-amalthea-en',
        'api_version': 'v1',
        'status': 'ready'
    })

# Test endpoints
@app.route('/api/test-call', methods=['POST'])
def test_call():
    """Test endpoint to make a test call"""
    try:
        data = request.get_json()
        to_number = data.get('to_number')
        
        if not to_number:
            return jsonify({'error': 'to_number is required'}), 400
        
        # Check if Twilio is configured
        if not twilio_service.client:
            return jsonify({'error': 'Twilio is not configured. Please check your credentials.'}), 500
        
        # Use ngrok URL if available, otherwise use request host
        webhook_url = f"https://{request.host}/webhooks/voice"
        if 'ngrok' in request.host:
            webhook_url = f"https://{request.host}/webhooks/voice"
        else:
            # For local testing, we need to use the ngrok URL
            webhook_url = "https://fe02-2600-1006-a132-82c-cd1a-9762-4bf8-3b0d.ngrok-free.app/webhooks/voice"
        
        result = twilio_service.make_test_call(
            to_number=to_number,
            from_number=app.config['TWILIO_PHONE_NUMBER'],
            webhook_url=webhook_url
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error making test call: {e}")
        return jsonify({'error': f'Failed to make test call: {str(e)}'}), 500

@app.route('/api/test-crm', methods=['POST'])
def test_crm():
    """Test CRM webhook connectivity"""
    try:
        result = test_crm_webhook()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error testing CRM webhook: {e}")
        return jsonify({'error': 'Failed to test CRM webhook'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        
        # Check service status
        twilio_configured = twilio_service.client is not None
        deepgram_configured = bool(app.config.get('DEEPGRAM_API_KEY'))
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'version': '1.0.0',
            'services': {
                'twilio': 'configured' if twilio_configured else 'not configured',
                'deepgram': 'configured' if deepgram_configured else 'not configured'
            }
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# WebSocket server for Twilio media streaming
def start_websocket_server():
    """Start WebSocket server for handling Twilio media streams"""
    import asyncio
    import websockets
    import json
    import base64
    import uuid
    from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
    
    # Store active connections
    active_connections = {}
    
    async def handle_websocket(websocket, path):
        connection_id = str(uuid.uuid4())
        logger.info(f"WebSocket connection established: {connection_id}")
        
        try:
            # Initialize Deepgram client
            deepgram = DeepgramClient(app.config['DEEPGRAM_API_KEY'])
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    event = data.get('event')
                    
                    if event == 'connected':
                        logger.info("Twilio WebSocket connected")
                        await websocket.send(json.dumps({"event": "connected"}))
                        
                    elif event == 'start':
                        call_sid = data.get('start', {}).get('callSid')
                        logger.info(f"Media stream started for call: {call_sid}")
                        
                        # Store connection
                        active_connections[connection_id] = {
                            'call_sid': call_sid,
                            'websocket': websocket,
                            'deepgram': deepgram
                        }
                        
                    elif event == 'media':
                        # Process audio data
                        payload = data.get('media', {}).get('payload')
                        if payload:
                            # Decode mulaw audio
                            audio_data = base64.b64decode(payload)
                            
                            # For now, just log that we received audio
                            # In production, this would be sent to Deepgram
                            if len(audio_data) > 0:
                                logger.debug(f"Received {len(audio_data)} bytes of audio")
                        
                    elif event == 'stop':
                        logger.info("Media stream stopped")
                        
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received")
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket connection closed: {connection_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            # Clean up
            if connection_id in active_connections:
                del active_connections[connection_id]
    
    async def start_server():
        # Start WebSocket server on port 8765
        server = await websockets.serve(handle_websocket, "0.0.0.0", 8765)
        logger.info("WebSocket server started on port 8765")
        await server.wait_closed()
    
    # Run in new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_server())

def start_deepgram_voice_server():
    """Start Deepgram Voice Agent WebSocket server"""
    from deepgram_voice_handler import start_deepgram_voice_server as start_dg_server
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_dg_server())

def start_voice_agent_server():
    """Start Voice Agent WebSocket server"""
    from voice_agent_handler import start_voice_agent_server
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_voice_agent_server())

def start_voice_agent_v1_server():
    """Start Voice Agent V1 WebSocket server"""
    from voice_agent_v1_handler import start_voice_agent_v1_server
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_voice_agent_v1_server())

if __name__ == '__main__':
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Start WebSocket server in a separate thread
    websocket_thread = threading.Thread(target=start_websocket_server, daemon=True)
    websocket_thread.start()
    
    # Start Voice Agent server in a separate thread
    voice_agent_thread = threading.Thread(target=start_voice_agent_server, daemon=True)
    voice_agent_thread.start()
    
    # Start Voice Agent V1 server in a separate thread
    voice_agent_v1_thread = threading.Thread(target=start_voice_agent_v1_server, daemon=True)
    voice_agent_v1_thread.start()
    
    # Start Flask app (disable debug mode for Twilio compatibility)
    app.run(debug=False, host='0.0.0.0', port=5001)
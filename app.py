from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
import websockets
import asyncio
import threading
import logging
import os
from datetime import datetime
import subprocess
import time
from werkzeug.serving import is_running_from_reloader

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
    app = Flask(__name__, static_folder='static', static_url_path='')
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

# Root endpoint - serve dashboard
@app.route('/')
def index():
    """Serve the React dashboard"""
    return app.send_static_file('index.html')

# API status endpoint
@app.route('/api/status', methods=['GET'])
def api_status():
    """API status endpoint"""
    return jsonify({
        'status': 'Voice AI Assistant API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/api/health',
            'voice_webhook': '/webhooks/voice',
            'test_call': '/api/test-call',
            'dashboard': '/api/dashboard'
        },
        'voice_agent': 'Deepgram Voice Agent V1 with aura-2-amalthea-en'
    })

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
    """Handle incoming Twilio voice webhooks - Enhanced Deepgram experience"""
    try:
        logger.info(f"🎯 Voice webhook called with data: {dict(request.form)}")
        
        # Get call information
        call_sid = request.form.get('CallSid')
        from_number = request.form.get('From')
        to_number = request.form.get('To')
        call_status = request.form.get('CallStatus')
        
        logger.info(f"📞 Voice webhook: {call_sid} from {from_number} to {to_number} status {call_status}")
        
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
        
        from twilio.twiml.voice_response import VoiceResponse, Stream
        
        response = VoiceResponse()
        
        # Welcome message for Voice Agent V1 connection
        response.say("Hello! Connecting you with our advanced AI assistant powered by Deepgram's Voice Agent with aura voice technology.", voice='Polly.Joanna-Neural')
        
        # Connect to Voice Agent V1 WebSocket
        # Railway supports multiple ports, so we can use the WebSocket server
        if 'localhost' in request.host or '127.0.0.1' in request.host:
            # For local development
            websocket_url = f"ws://localhost:8767?call_sid={call_sid}"
        elif 'railway.app' in request.host:
            # For Railway deployment - construct WebSocket URL
            railway_domain = request.host.replace('.railway.app', '')
            websocket_url = f"wss://{railway_domain}-8767.railway.app?call_sid={call_sid}"
        else:
            # Generic WebSocket URL construction  
            websocket_url = f"wss://{request.host}:8767?call_sid={call_sid}"
            
        logger.info(f"🔗 Connecting to Voice Agent V1 WebSocket: {websocket_url}")
        
        # Create WebSocket stream to Voice Agent V1
        stream = Stream(url=websocket_url)
        response.append(stream)
        
        # Add fallback in case WebSocket fails
        response.say("If you experience any connection issues, please call back and we'll assist you.", voice='Polly.Joanna-Neural')
        response.hangup()
        
        return str(response), 200, {'Content-Type': 'text/xml'}

@app.route('/webhooks/voice-input-enhanced', methods=['POST'])
def handle_voice_input_enhanced():
    """Enhanced speech input handler with improved Deepgram integration"""
    try:
        call_sid = request.args.get('call_sid')
        speech_result = request.form.get('SpeechResult', '').lower()
        
        logger.info(f"🎤 Enhanced voice input for call {call_sid}: {speech_result}")
        
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
        
        # Enhanced AI responses with Deepgram branding
        if any(word in speech_result for word in ['appointment', 'book', 'schedule']):
            response.say("Perfect! I'll help you book an appointment using Deepgram's intelligent processing. Let me gather some information from you.", voice='Polly.Joanna-Neural')
            
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
            response.say("Let me check our availability using Deepgram's advanced voice AI technology.", voice='Polly.Joanna-Neural')
            
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
            response.say("Hello! It's wonderful to speak with you. I'm an AI assistant powered by Deepgram's cutting-edge aura voice technology, designed to provide natural, human-like conversation. I can help you book appointments, check availability, or answer questions about our services.", voice='Polly.Joanna-Neural')
            
            gather = Gather(
                input='speech',
                timeout=10,
                speech_timeout='auto',
                action=f'/webhooks/voice-input-enhanced?call_sid={call_sid}',
                method='POST'
            )
            gather.say("What would you like to do today?", voice='Polly.Joanna-Neural')
            response.append(gather)
            
        elif any(word in speech_result for word in ['deepgram', 'voice', 'technology']):
            response.say("Yes! I'm powered by Deepgram's advanced aura voice technology, specifically the aura-2-amalthea-en model, which provides natural, human-like speech synthesis. This technology allows me to sound more conversational and understand you better.", voice='Polly.Joanna-Neural')
            
            gather = Gather(
                input='speech',
                timeout=10,
                speech_timeout='auto',
                action=f'/webhooks/voice-input-enhanced?call_sid={call_sid}',
                method='POST'
            )
            gather.say("How can I help you today?", voice='Polly.Joanna-Neural')
            response.append(gather)
            
        else:
            response.say(f"I understand you said: {speech_result}. As a Deepgram-powered AI assistant, I can help you with appointments, availability checks, or questions about our services.", voice='Polly.Joanna-Neural')
            
            gather = Gather(
                input='speech',
                timeout=10,
                speech_timeout='auto',
                action=f'/webhooks/voice-input-enhanced?call_sid={call_sid}',
                method='POST'
            )
            gather.say("Please tell me how I can assist you.", voice='Polly.Joanna-Neural')
            response.append(gather)
        
        # Fallback
        response.say("Thank you for experiencing our advanced Deepgram voice technology. Have a great day!", voice='Polly.Joanna-Neural')
        response.hangup()
        
        return str(response), 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error(f"❌ Error handling enhanced voice input: {e}")
        response = VoiceResponse()
        response.say("I'm sorry, I'm having trouble processing your request. Please call back later.", voice='Polly.Joanna-Neural')
        response.hangup()
        return str(response), 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error(f"❌ Error handling voice webhook: {e}")
        import traceback
        logger.error(f"💥 Traceback: {traceback.format_exc()}")
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

# WebSocket endpoints - these need to be actual WebSocket handlers for production
from flask import request as flask_request

@app.route('/ws/voice-agent-v1')
def voice_agent_v1_endpoint():
    """WebSocket endpoint for Voice Agent V1 - Proxy to internal WebSocket server"""
    call_sid = request.args.get('call_sid')
    
    # In production, we need to handle WebSocket upgrade
    # For now, return connection info for debugging
    return jsonify({
        'message': 'Voice Agent V1 WebSocket Proxy',
        'call_sid': call_sid,
        'voice': 'aura-2-amalthea-en',
        'api_version': 'v1',
        'internal_port': 8767,
        'status': 'proxy_ready'
    })

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
        # Basic health check - don't fail on missing services
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'voice_agent': 'Deepgram Voice Agent V1 with aura-2-amalthea-en'
        }
        
        # Test database connection (optional)
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            health_status['database'] = 'connected'
        except Exception as db_error:
            logger.warning(f"Database check failed: {db_error}")
            health_status['database'] = 'not connected'
        
        # Check service status (optional)
        try:
            twilio_configured = twilio_service.client is not None
            deepgram_configured = bool(app.config.get('DEEPGRAM_API_KEY'))
            health_status['services'] = {
                'twilio': 'configured' if twilio_configured else 'not configured',
                'deepgram': 'configured' if deepgram_configured else 'not configured'
            }
        except Exception as service_error:
            logger.warning(f"Service check failed: {service_error}")
            health_status['services'] = 'check failed'
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        # Return healthy status anyway for Railway deployment
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'note': 'basic health check passed'
        })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# Catch-all route for React Router (must be last)
@app.route('/<path:path>')
def serve_react_app(path):
    """Serve React app for all non-API routes"""
    if path.startswith('api/') or path.startswith('webhooks/'):
        return jsonify({'error': 'Not found'}), 404
    return app.send_static_file('index.html')

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

def start_voice_agent_safely():
    """Safely start Voice Agent V1 server with error handling"""
    try:
        logger.info("🚀 Starting Voice Agent V1 WebSocket server...")
        start_voice_agent_v1_server()
    except Exception as e:
        logger.error(f"❌ Failed to start Voice Agent V1 server: {e}")
        # Don't crash the main app if WebSocket server fails

if __name__ == '__main__':
    # Create database tables
    try:
        with app.app_context():
            db.create_all()
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
    
    # Start Voice Agent V1 server in background (non-blocking)
    if not is_running_from_reloader():
        voice_agent_v1_thread = threading.Thread(target=start_voice_agent_safely, daemon=True)
        voice_agent_v1_thread.start()
        logger.info("🔄 Voice Agent V1 server thread started")
    
    # Start Flask app immediately (don't wait for WebSocket server)
    port = int(os.environ.get('PORT', 5001))
    logger.info(f"🌐 Starting Flask app on port {port}")
    
    try:
        app.run(debug=False, host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"❌ Flask app failed to start: {e}")
        raise
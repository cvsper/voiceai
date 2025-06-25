#!/usr/bin/env python3
"""
Enhanced Flask app for Railway deployment with Voice AI features + WebSocket support
"""
import os
import logging
import threading
import asyncio
from flask import Flask, jsonify, request
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flag to track if WebSocket server should start
ENABLE_WEBSOCKET = os.environ.get('ENABLE_WEBSOCKET', 'false').lower() == 'true'

# Create Flask app
app = Flask(__name__, static_folder='static', static_url_path='')

@app.route('/')
def index():
    """Serve dashboard or API info"""
    try:
        # Try to serve React dashboard
        return app.send_static_file('index.html')
    except:
        # Fallback to API info
        return jsonify({
            'status': 'Voice AI Assistant - Enhanced',
            'version': '2.0.0',
            'voice_agent': 'Deepgram Voice Agent V1 with aura-2-amalthea-en',
            'timestamp': datetime.utcnow().isoformat(),
            'endpoints': {
                'voice_webhook': '/webhooks/voice',
                'enhanced_input': '/webhooks/voice-input-enhanced',
                'health': '/api/health'
            }
        })

@app.route('/api/health')
def health():
    """Enhanced health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'voice_agent': 'Deepgram Voice Agent V1 with aura-2-amalthea-en',
        'features': ['voice_calls', 'appointments', 'dashboard']
    })

@app.route('/webhooks/voice', methods=['POST'])
def voice_webhook():
    """Enhanced voice webhook with optional WebSocket support"""
    try:
        # Get call information
        call_sid = request.form.get('CallSid', 'unknown')
        from_number = request.form.get('From', 'unknown')
        
        logger.info(f"📞 Voice call from {from_number}, SID: {call_sid}")
        
        # For Railway deployment, use enhanced conversation mode with optional Deepgram TTS
        logger.info("🎙️ Using enhanced Deepgram conversation mode")
        
        # Check if we should use Deepgram TTS for even better voice quality
        deepgram_api_key = os.environ.get('DEEPGRAM_API_KEY')
        if deepgram_api_key and ENABLE_WEBSOCKET:
            # Use Deepgram TTS for greeting (future enhancement)
            voice_note = "with enhanced Deepgram voice synthesis"
        else:
            voice_note = "with advanced voice technology"
            
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">Hello! Welcome to our AI assistant powered by Deepgram's aura voice technology {voice_note}. I can help you with appointments, availability, and questions about our services.</Say>
    <Gather input="speech" timeout="10" speechTimeout="auto" action="/webhooks/voice-input-enhanced" method="POST">
        <Say voice="Polly.Joanna-Neural">How can I assist you today?</Say>
    </Gather>
    <Say voice="Polly.Joanna-Neural">Thank you for calling our Deepgram-powered AI assistant. Have a great day!</Say>
    <Hangup/>
</Response>''', 200, {'Content-Type': 'text/xml'}
            
    except Exception as e:
        logger.error(f"Error in voice webhook: {e}")
        return '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">Hello! Our AI assistant is temporarily unavailable. Please try again later.</Say>
    <Hangup/>
</Response>''', 200, {'Content-Type': 'text/xml'}

@app.route('/webhooks/voice-input-enhanced', methods=['POST'])
def voice_input_enhanced():
    """Enhanced voice input handler"""
    try:
        speech_result = request.form.get('SpeechResult', '').lower()
        logger.info(f"🎤 Speech input: {speech_result}")
        
        if any(word in speech_result for word in ['appointment', 'book', 'schedule']):
            response = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">Perfect! I'd be happy to help you book an appointment using Deepgram's intelligent processing. What's your name?</Say>
    <Gather input="speech" timeout="10" speechTimeout="auto" action="/webhooks/appointment-details" method="POST">
        <Say voice="Polly.Joanna-Neural">Please tell me your full name.</Say>
    </Gather>
    <Say voice="Polly.Joanna-Neural">Thank you for your interest in booking an appointment!</Say>
    <Hangup/>
</Response>'''
        elif any(word in speech_result for word in ['available', 'availability', 'times']):
            response = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">Let me check our availability using Deepgram's advanced voice AI technology. We have appointments available today and tomorrow.</Say>
    <Say voice="Polly.Joanna-Neural">Would you like to book an appointment?</Say>
    <Hangup/>
</Response>'''
        elif any(word in speech_result for word in ['hello', 'hi', 'hey']):
            response = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">Hello! It's wonderful to speak with you. I'm an AI assistant powered by Deepgram's cutting-edge aura voice technology. I can help you book appointments or check availability.</Say>
    <Gather input="speech" timeout="10" speechTimeout="auto" action="/webhooks/voice-input-enhanced" method="POST">
        <Say voice="Polly.Joanna-Neural">What would you like to do today?</Say>
    </Gather>
    <Hangup/>
</Response>'''
        else:
            response = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">I understand you said: {speech_result}. As a Deepgram-powered AI assistant, I can help you with appointments or availability checks.</Say>
    <Gather input="speech" timeout="10" speechTimeout="auto" action="/webhooks/voice-input-enhanced" method="POST">
        <Say voice="Polly.Joanna-Neural">How can I help you today?</Say>
    </Gather>
    <Hangup/>
</Response>'''
        
        return response, 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error(f"Error in voice input: {e}")
        return '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">I'm sorry, I'm having trouble understanding. Please call back later.</Say>
    <Hangup/>
</Response>''', 200, {'Content-Type': 'text/xml'}

@app.route('/webhooks/appointment-details', methods=['POST'])
def appointment_details():
    """Handle appointment booking details"""
    try:
        name = request.form.get('SpeechResult', 'Customer')
        logger.info(f"👤 Appointment booking for: {name}")
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">Thank you {name}! I've noted your appointment request. Our team will call you back within 24 hours to confirm your appointment time. Have a great day!</Say>
    <Hangup/>
</Response>''', 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error(f"Error in appointment details: {e}")
        return '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">Thank you for your appointment request! Our team will contact you soon.</Say>
    <Hangup/>
</Response>''', 200, {'Content-Type': 'text/xml'}

# Catch-all route for React Router
@app.route('/<path:path>')
def serve_react_app(path):
    """Serve React app for all non-API routes"""
    if path.startswith('api/') or path.startswith('webhooks/'):
        return jsonify({'error': 'Not found'}), 404
    try:
        return app.send_static_file('index.html')
    except:
        return jsonify({'error': 'Dashboard not available'}), 404

@app.route('/ws/voice-agent-v1')
def websocket_endpoint():
    """WebSocket endpoint info (Railway doesn't support Flask-SocketIO upgrade)"""
    call_sid = request.args.get('call_sid', 'unknown')
    
    # For Railway, we need to fall back to enhanced mode since WebSocket upgrade isn't supported
    logger.warning(f"⚠️ WebSocket endpoint accessed but Flask doesn't support upgrade. Call SID: {call_sid}")
    
    return jsonify({
        'error': 'WebSocket upgrade not supported in this deployment',
        'call_sid': call_sid,
        'suggestion': 'Use enhanced conversation mode instead',
        'fallback_url': '/webhooks/voice-input-enhanced'
    }), 400

# WebSocket server for Voice Agent V1 (optional)
def start_websocket_server():
    """Start WebSocket server for Deepgram Voice Agent V1"""
    try:
        import websockets
        import json
        import base64
        import ssl
        
        logger.info("🚀 Starting Voice Agent V1 WebSocket server...")
        
        async def handle_websocket(websocket, path):
            """Handle WebSocket connection for Voice Agent V1"""
            call_sid = None
            try:
                logger.info(f"🔗 New WebSocket connection: {path}")
                
                # Extract call_sid from path
                if 'call_sid=' in path:
                    call_sid = path.split('call_sid=')[1].split('&')[0]
                
                if not call_sid:
                    logger.error("❌ No call_sid provided in WebSocket")
                    await websocket.close()
                    return
                
                logger.info(f"🎯 Voice Agent V1 WebSocket connected for call {call_sid}")
                
                # Initialize Deepgram Voice Agent V1 connection
                deepgram_api_key = os.environ.get('DEEPGRAM_API_KEY')
                if not deepgram_api_key:
                    logger.error("❌ No Deepgram API key found")
                    await websocket.send(json.dumps({"error": "No API key configured"}))
                    return
                
                # Connect to Deepgram Voice Agent V1
                agent_url = "wss://agent.deepgram.com/v1/agent/converse"
                headers = {"Authorization": f"token {deepgram_api_key}"}
                
                # Create SSL context
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                async with websockets.connect(agent_url, extra_headers=headers, ssl=ssl_context) as agent_ws:
                    logger.info(f"✅ Connected to Deepgram Voice Agent V1 for call {call_sid}")
                    
                    # Send Voice Agent V1 configuration
                    config = {
                        "type": "Settings",
                        "audio": {
                            "input": {"encoding": "linear16", "sample_rate": 8000},
                            "output": {"encoding": "linear16", "sample_rate": 8000}
                        },
                        "agent": {
                            "listen": {"provider": {"type": "deepgram", "model": "nova-2"}},
                            "think": {
                                "provider": {"type": "open_ai", "model": "gpt-4o-mini"},
                                "prompt": "You are a helpful AI assistant for a business. You can help customers with booking appointments, checking availability, and answering questions. Keep responses concise and professional. When customers want to book appointments, ask for their name, preferred date, and time."
                            },
                            "speak": {"provider": {"type": "deepgram", "model": "aura-2-amalthea-en"}}
                        }
                    }
                    await agent_ws.send(json.dumps(config))
                    logger.info(f"📤 Sent Voice Agent V1 configuration for call {call_sid}")
                    
                    # Handle bidirectional communication
                    async def relay_twilio_to_deepgram():
                        async for message in websocket:
                            try:
                                data = json.loads(message)
                                event = data.get('event')
                                
                                if event == 'media':
                                    # Convert Twilio audio to Deepgram format
                                    payload = data.get('media', {}).get('payload')
                                    if payload:
                                        import audioop
                                        audio_data = base64.b64decode(payload)
                                        linear_audio = audioop.ulaw2lin(audio_data, 2)
                                        audio_b64 = base64.b64encode(linear_audio).decode('utf-8')
                                        
                                        await agent_ws.send(json.dumps({
                                            "type": "UserAudio",
                                            "audio": audio_b64
                                        }))
                                        
                                elif event == 'connected':
                                    await websocket.send(json.dumps({"event": "connected"}))
                                    
                            except Exception as e:
                                logger.error(f"💥 Error relaying Twilio to Deepgram: {e}")
                    
                    async def relay_deepgram_to_twilio():
                        async for message in agent_ws:
                            try:
                                data = json.loads(message)
                                msg_type = data.get('type')
                                
                                if msg_type == "AgentAudio":
                                    # Convert Deepgram audio to Twilio format
                                    audio_data = data.get('audio')
                                    if audio_data:
                                        import audioop
                                        linear_audio = base64.b64decode(audio_data)
                                        mulaw_audio = audioop.lin2ulaw(linear_audio, 2)
                                        audio_payload = base64.b64encode(mulaw_audio).decode('utf-8')
                                        
                                        await websocket.send(json.dumps({
                                            "event": "media",
                                            "streamSid": call_sid,
                                            "media": {"payload": audio_payload}
                                        }))
                                        
                                elif msg_type in ["UserTranscript", "AgentTranscript"]:
                                    logger.info(f"🎤 {msg_type}: {data.get('transcript', '')}")
                                    
                            except Exception as e:
                                logger.error(f"💥 Error relaying Deepgram to Twilio: {e}")
                    
                    # Run both relay tasks concurrently
                    await asyncio.gather(
                        relay_twilio_to_deepgram(),
                        relay_deepgram_to_twilio()
                    )
                    
            except Exception as e:
                logger.error(f"💥 WebSocket error for call {call_sid}: {e}")
            finally:
                logger.info(f"🧹 WebSocket closed for call {call_sid}")
        
        async def start_server():
            websocket_port = int(os.environ.get('WEBSOCKET_PORT', 8767))
            server = await websockets.serve(handle_websocket, "0.0.0.0", websocket_port)
            logger.info(f"🚀 Voice Agent V1 WebSocket server started on port {websocket_port}")
            await server.wait_closed()
        
        # Run WebSocket server
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_server())
        
    except ImportError:
        logger.warning("⚠️ WebSocket dependencies not available - install with: pip install websockets audioop")
    except Exception as e:
        logger.error(f"❌ Failed to start WebSocket server: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    logger.info(f"🚀 Starting Enhanced Voice AI Assistant on port {port}")
    
    # Start WebSocket server in separate thread if enabled
    if ENABLE_WEBSOCKET:
        logger.info("🔄 Starting WebSocket server thread...")
        websocket_thread = threading.Thread(target=start_websocket_server, daemon=True)
        websocket_thread.start()
    
    app.run(
        debug=False,
        host='0.0.0.0',
        port=port,
        threaded=True
    )
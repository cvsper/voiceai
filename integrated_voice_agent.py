"""
Integrated approach: Handle both HTTP webhooks and WebSocket connections on the same port
"""
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, disconnect
import asyncio
import websockets
import json
import base64
import logging
import ssl
from deepgram import DeepgramClient
import audioop
from config import Config
from models import db, Call, Transcript
import threading

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

class IntegratedVoiceAgent:
    def __init__(self):
        self.deepgram_client = DeepgramClient(Config.DEEPGRAM_API_KEY)
        self.active_connections = {}
    
    async def connect_to_deepgram_v1(self, call_sid):
        """Connect to Deepgram Voice Agent V1"""
        try:
            logger.info(f"🔗 Connecting to Deepgram Voice Agent V1 for call {call_sid}")
            
            # SSL context for Deepgram
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Connect to Deepgram V1
            agent_url = "wss://agent.deepgram.com/v1/agent/converse"
            headers = {"Authorization": f"token {Config.DEEPGRAM_API_KEY}"}
            
            connection = await websockets.connect(agent_url, extra_headers=headers, ssl=ssl_context)
            
            # Send V1 configuration
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
                        "prompt": "You are a helpful AI assistant. Keep responses concise."
                    },
                    "speak": {"provider": {"type": "deepgram", "model": "aura-2-amalthea-en"}}
                }
            }
            
            await connection.send(json.dumps(config))
            logger.info(f"✅ Deepgram Voice Agent V1 connected for call {call_sid}")
            
            return connection
            
        except Exception as e:
            logger.error(f"💥 Failed to connect to Deepgram V1: {e}")
            return None

# Global voice agent
voice_agent = IntegratedVoiceAgent()

@app.route('/webhooks/voice', methods=['POST'])
def handle_voice_webhook():
    """Handle Twilio voice webhook"""
    try:
        call_sid = request.form.get('CallSid')
        logger.info(f"📞 Voice webhook for call {call_sid}")
        
        from twilio.twiml.voice_response import VoiceResponse, Connect
        
        response = VoiceResponse()
        response.say("Connecting you to our AI assistant with Deepgram Voice Agent.", voice='Polly.Joanna-Neural')
        
        # Connect to WebSocket using the same domain/port
        connect = Connect()
        connect.stream(url=f"wss://{request.host}/socket.io/?call_sid={call_sid}")
        response.append(connect)
        
        return str(response), 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error(f"💥 Voice webhook error: {e}")
        return "Error", 500

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection from Twilio"""
    call_sid = request.args.get('call_sid')
    logger.info(f"🔌 SocketIO connected for call {call_sid}")

@socketio.on('message')
def handle_message(data):
    """Handle WebSocket message from Twilio"""
    call_sid = request.args.get('call_sid')
    logger.info(f"📨 Received message for call {call_sid}: {data}")
    
    # Echo back for now
    emit('message', {'event': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnect"""
    call_sid = request.args.get('call_sid')
    logger.info(f"🔌 SocketIO disconnected for call {call_sid}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    socketio.run(app, host='0.0.0.0', port=5002, debug=False)
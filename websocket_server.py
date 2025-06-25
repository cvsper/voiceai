import eventlet
eventlet.monkey_patch()

from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import base64
import logging
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
import asyncio
from voice_agent.functions import book_appointment, get_availability, cancel_appointment, trigger_crm_webhook
from models import db, Call, Transcript
from config import Config
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app for WebSocket
ws_app = Flask(__name__)
ws_app.config.from_object(Config)
CORS(ws_app)

# Initialize SocketIO
socketio = SocketIO(ws_app, cors_allowed_origins="*", async_mode='eventlet')

# Store active connections
active_calls = {}

class DeepgramHandler:
    def __init__(self, call_sid, socketio_session):
        self.call_sid = call_sid
        self.session = socketio_session
        self.deepgram_client = None
        self.deepgram_connection = None
        
    async def setup_deepgram(self):
        """Initialize Deepgram connection"""
        try:
            self.deepgram_client = DeepgramClient(Config.DEEPGRAM_API_KEY)
            
            # Configure for telephony
            options = LiveOptions(
                model="nova-2",
                language="en-US",
                encoding="mulaw",
                sample_rate=8000,
                channels=1,
                interim_results=True,
                punctuate=True,
                smart_format=True,
                utterance_end_ms=1000,
                vad_events=True
            )
            
            self.deepgram_connection = self.deepgram_client.listen.live.v("1")
            
            # Set up event handlers
            self.deepgram_connection.on(LiveTranscriptionEvents.Open, self.on_open)
            self.deepgram_connection.on(LiveTranscriptionEvents.Transcript, self.on_transcript)
            self.deepgram_connection.on(LiveTranscriptionEvents.Error, self.on_error)
            self.deepgram_connection.on(LiveTranscriptionEvents.Close, self.on_close)
            
            # Start connection
            await self.deepgram_connection.start(options)
            
            logger.info(f"Deepgram connection established for call {self.call_sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Deepgram for call {self.call_sid}: {e}")
            return False
    
    def on_open(self, *args, **kwargs):
        logger.info(f"Deepgram connection opened for call {self.call_sid}")
    
    def on_transcript(self, *args, **kwargs):
        try:
            result = args[0] if args else kwargs.get('result')
            if not result:
                return
                
            transcript = result.channel.alternatives[0].transcript
            if not transcript:
                return
                
            logger.info(f"Transcript for {self.call_sid}: {transcript}")
            
            # Process for function calls (simplified for now)
            if any(word in transcript.lower() for word in ['appointment', 'book', 'schedule']):
                # Simulate function call response
                response_text = "I'd be happy to help you book an appointment. What date and time would work best for you?"
                
                # Send response back to Twilio
                socketio.emit('ai_response', {
                    'text': response_text,
                    'call_sid': self.call_sid
                }, room=self.session)
            
        except Exception as e:
            logger.error(f"Error processing transcript for call {self.call_sid}: {e}")
    
    def on_error(self, *args, **kwargs):
        error = args[0] if args else kwargs.get('error')
        logger.error(f"Deepgram error for call {self.call_sid}: {error}")
    
    def on_close(self, *args, **kwargs):
        logger.info(f"Deepgram connection closed for call {self.call_sid}")
    
    async def send_audio(self, audio_data):
        """Send audio data to Deepgram"""
        if self.deepgram_connection:
            try:
                await self.deepgram_connection.send(audio_data)
            except Exception as e:
                logger.error(f"Error sending audio to Deepgram: {e}")
    
    async def close(self):
        """Close Deepgram connection"""
        if self.deepgram_connection:
            try:
                await self.deepgram_connection.finish()
            except Exception as e:
                logger.error(f"Error closing Deepgram connection: {e}")

@socketio.on('connect')
def handle_connect():
    logger.info(f"WebSocket client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"WebSocket client disconnected: {request.sid}")
    
    # Clean up any active calls for this session
    for call_sid, handler in list(active_calls.items()):
        if hasattr(handler, 'session') and handler.session == request.sid:
            eventlet.spawn(cleanup_call, call_sid)

@socketio.on('twilio_media')
def handle_twilio_media(data):
    """Handle Twilio media stream data"""
    try:
        event = data.get('event')
        
        if event == 'connected':
            logger.info(f"Twilio media stream connected: {data}")
            
        elif event == 'start':
            call_sid = data.get('start', {}).get('callSid')
            logger.info(f"Twilio media stream started for call: {call_sid}")
            
            if call_sid:
                # Initialize Deepgram for this call
                handler = DeepgramHandler(call_sid, request.sid)
                active_calls[call_sid] = handler
                
                # Setup Deepgram in background
                eventlet.spawn(setup_deepgram_async, handler)
            
        elif event == 'media':
            call_sid = data.get('callSid')
            payload = data.get('media', {}).get('payload')
            
            if call_sid in active_calls and payload:
                # Decode and send audio to Deepgram
                audio_data = base64.b64decode(payload)
                handler = active_calls[call_sid]
                eventlet.spawn(send_audio_async, handler, audio_data)
                
        elif event == 'stop':
            call_sid = data.get('callSid')
            logger.info(f"Twilio media stream stopped for call: {call_sid}")
            
            if call_sid in active_calls:
                eventlet.spawn(cleanup_call, call_sid)
    
    except Exception as e:
        logger.error(f"Error handling Twilio media: {e}")

def setup_deepgram_async(handler):
    """Setup Deepgram connection asynchronously"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(handler.setup_deepgram())

def send_audio_async(handler, audio_data):
    """Send audio to Deepgram asynchronously"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(handler.send_audio(audio_data))

def cleanup_call(call_sid):
    """Clean up call resources"""
    if call_sid in active_calls:
        handler = active_calls[call_sid]
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(handler.close())
        del active_calls[call_sid]
        logger.info(f"Cleaned up resources for call: {call_sid}")

if __name__ == '__main__':
    logger.info("Starting WebSocket server on port 8765...")
    socketio.run(ws_app, host='0.0.0.0', port=8765, debug=True)
import asyncio
import websockets
import json
import logging
from flask import current_app
import base64

logger = logging.getLogger(__name__)

class DeepgramVoiceAgent:
    def __init__(self):
        self.api_key = None
        self.agent_id = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        try:
            self.api_key = current_app.config.get('DEEPGRAM_API_KEY')
            # For voice agents, you'd typically have an agent ID configured
            self.agent_id = current_app.config.get('DEEPGRAM_AGENT_ID', 'default-agent')
            
            if not self.api_key:
                logger.warning("Deepgram API key not configured for voice agent")
            else:
                logger.info("Deepgram Voice Agent initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Deepgram Voice Agent: {e}")
    
    async def handle_twilio_stream(self, websocket, call_sid):
        """Handle bidirectional audio streaming between Twilio and Deepgram Voice Agent"""
        try:
            if not self.api_key:
                logger.error("Cannot start voice agent - API key not configured")
                return
            
            # Connect to Deepgram Voice Agent
            deepgram_url = f"wss://agent.deepgram.com/agent/{self.agent_id}/stream"
            headers = {"Authorization": f"Token {self.api_key}"}
            
            async with websockets.connect(deepgram_url, extra_headers=headers) as deepgram_ws:
                logger.info(f"Connected to Deepgram Voice Agent for call {call_sid}")
                
                # Send initial configuration
                config = {
                    "type": "Configure",
                    "audio": {
                        "encoding": "mulaw",
                        "sample_rate": 8000,
                        "channels": 1
                    },
                    "agent": {
                        "personality": "friendly assistant",
                        "instructions": "You are a cheerful personal assistant. Greet callers warmly and ask how you can help them today. If they want to book an appointment, collect their name, phone number, and preferred date/time.",
                        "voice": "nova"  # Deepgram's natural voice
                    }
                }
                await deepgram_ws.send(json.dumps(config))
                
                # Handle bidirectional streaming
                async def twilio_to_deepgram():
                    try:
                        async for message in websocket:
                            data = json.loads(message)
                            if data.get('event') == 'media':
                                # Forward audio from Twilio to Deepgram
                                audio_data = data['media']['payload']
                                deepgram_message = {
                                    "type": "Audio",
                                    "audio": audio_data
                                }
                                await deepgram_ws.send(json.dumps(deepgram_message))
                    except Exception as e:
                        logger.error(f"Error forwarding Twilio to Deepgram: {e}")
                
                async def deepgram_to_twilio():
                    try:
                        async for message in deepgram_ws:
                            data = json.loads(message)
                            if data.get('type') == 'Audio':
                                # Forward generated speech from Deepgram to Twilio
                                twilio_message = {
                                    "event": "media",
                                    "streamSid": call_sid,
                                    "media": {
                                        "payload": data['audio']
                                    }
                                }
                                await websocket.send(json.dumps(twilio_message))
                            elif data.get('type') == 'Transcript':
                                # Log conversation for debugging
                                logger.info(f"Agent transcript: {data.get('text', '')}")
                    except Exception as e:
                        logger.error(f"Error forwarding Deepgram to Twilio: {e}")
                
                # Run both directions concurrently
                await asyncio.gather(
                    twilio_to_deepgram(),
                    deepgram_to_twilio()
                )
                
        except Exception as e:
            logger.error(f"Error in Deepgram Voice Agent for call {call_sid}: {e}")
    
    def get_agent_greeting(self):
        """Get a dynamic greeting message"""
        return "Hey damian! Is there anything I can do help you? Cheeks maybe?"
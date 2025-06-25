import asyncio
import websockets
import json
import base64
import logging
import ssl
import os
from deepgram import DeepgramClient
import audioop
import struct
from voice_agent.functions import book_appointment, get_availability, cancel_appointment, trigger_crm_webhook
from models import db, Call, Transcript
from config import Config
import threading

logger = logging.getLogger(__name__)

class VoiceAgentV1Handler:
    def __init__(self, call_sid):
        self.call_sid = call_sid
        self.deepgram_client = DeepgramClient(Config.DEEPGRAM_API_KEY)
        self.agent_connection = None
        self.twilio_websocket = None
        self.is_connected = False
        self.conversation_context = []
        
    async def initialize_voice_agent(self):
        """Initialize Deepgram Voice Agent V1"""
        try:
            logger.info(f"🎯 Initializing Deepgram Voice Agent V1 for call {self.call_sid}")
            
            # Connect to Voice Agent V1 endpoint
            agent_url = "wss://agent.deepgram.com/v1/agent/converse"
            headers = {
                "Authorization": f"token {Config.DEEPGRAM_API_KEY}"
            }
            
            logger.info(f"🔗 Connecting to Voice Agent V1: {agent_url}")
            logger.info(f"🔑 Using API key: {Config.DEEPGRAM_API_KEY[:10]}...")
            
            try:
                # Create SSL context for development
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                self.agent_connection = await websockets.connect(agent_url, extra_headers=headers, ssl=ssl_context)
                logger.info(f"✅ Successfully connected to Voice Agent V1")
            except Exception as conn_error:
                logger.error(f"❌ Failed to connect to Voice Agent V1: {conn_error}")
                return False
            
            logger.info(f"✅ Connected to Voice Agent V1 for call {self.call_sid}")
            
            # Send V1 configuration
            config_message = {
                "type": "Settings",
                "audio": {
                    "input": {
                        "encoding": "linear16",
                        "sample_rate": 8000  # Twilio uses 8kHz
                    },
                    "output": {
                        "encoding": "linear16",
                        "sample_rate": 8000
                    }
                },
                "agent": {
                    "listen": {
                        "provider": {
                            "type": "deepgram",
                            "model": "nova-2"
                        }
                    },
                    "think": {
                        "provider": {
                            "type": "open_ai",
                            "model": "gpt-4o-mini"
                        },
                        "prompt": "You are a helpful AI assistant for a business. You can help customers with booking appointments, checking availability, and answering questions about services. Keep responses concise and professional. When customers want to book appointments, ask for their name, preferred date, and time."
                    },
                    "speak": {
                        "provider": {
                            "type": "deepgram",
                            "model": "aura-2-amalthea-en"
                        }
                    }
                }
            }
            
            logger.info(f"📤 Sending V1 configuration for call {self.call_sid}")
            await self.agent_connection.send(json.dumps(config_message))
            
            # Start listening for agent responses
            asyncio.create_task(self._handle_agent_messages())
            
            self.is_connected = True
            logger.info(f"🎉 Voice Agent V1 initialized successfully for call {self.call_sid}")
            
            return True
            
        except Exception as e:
            logger.error(f"💥 Error initializing Voice Agent V1 for call {self.call_sid}: {e}")
            import traceback
            logger.error(f"💥 Traceback: {traceback.format_exc()}")
            return False
    
    async def _handle_agent_messages(self):
        """Handle messages from Voice Agent V1"""
        try:
            async for message in self.agent_connection:
                try:
                    data = json.loads(message)
                    msg_type = data.get('type')
                    
                    logger.info(f"📨 Received from Voice Agent V1: {msg_type} for call {self.call_sid}")
                    
                    if msg_type == "AgentAudio":
                        # Stream audio back to Twilio
                        await self._stream_audio_to_twilio(data.get('audio'))
                        
                    elif msg_type == "UserTranscript":
                        transcript = data.get('transcript', '')
                        logger.info(f"🎤 User transcript: {transcript} for call {self.call_sid}")
                        
                    elif msg_type == "AgentTranscript":
                        transcript = data.get('transcript', '')
                        logger.info(f"🤖 Agent transcript: {transcript} for call {self.call_sid}")
                        
                    elif msg_type == "FunctionCall":
                        # Handle function calls
                        await self._handle_function_call(data)
                        
                    elif msg_type == "AgentThinking":
                        logger.info(f"🤔 Agent is thinking for call {self.call_sid}")
                        
                    elif msg_type == "UserStartedSpeaking":
                        logger.info(f"🗣️ User started speaking for call {self.call_sid}")
                        
                    elif msg_type == "Error":
                        error_desc = data.get('description', 'Unknown error')
                        logger.error(f"❌ Voice Agent V1 error for call {self.call_sid}: {error_desc}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"🚫 Invalid JSON from Voice Agent V1 for call {self.call_sid}: {e}")
                except Exception as e:
                    logger.error(f"💥 Error processing Voice Agent V1 message for call {self.call_sid}: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 Voice Agent V1 connection closed for call {self.call_sid}")
        except Exception as e:
            logger.error(f"💥 Error in Voice Agent V1 message handler for call {self.call_sid}: {e}")
    
    async def _stream_audio_to_twilio(self, audio_data):
        """Stream audio from Voice Agent to Twilio"""
        try:
            if not self.twilio_websocket or not audio_data:
                return
                
            logger.debug(f"🎵 Streaming audio to Twilio for call {self.call_sid}")
            
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Convert to mulaw for Twilio (Voice Agent V1 sends linear16)
            mulaw_audio = audioop.lin2ulaw(audio_bytes, 2)
            
            # Encode as base64 for Twilio
            audio_payload = base64.b64encode(mulaw_audio).decode('utf-8')
            
            # Send to Twilio
            message = {
                "event": "media",
                "streamSid": self.call_sid,
                "media": {
                    "payload": audio_payload
                }
            }
            
            await self.twilio_websocket.send(json.dumps(message))
            
        except Exception as e:
            logger.error(f"💥 Error streaming audio to Twilio for call {self.call_sid}: {e}")
    
    async def _handle_function_call(self, function_data):
        """Handle function calls from Voice Agent V1"""
        try:
            function_name = function_data.get('function', {}).get('name')
            function_args = function_data.get('function', {}).get('arguments', {})
            
            logger.info(f"🔧 Function call: {function_name} with args {function_args} for call {self.call_sid}")
            
            result = None
            
            if function_name == "book_appointment":
                result = await book_appointment(
                    customer_name=function_args.get('customer_name'),
                    appointment_date=function_args.get('appointment_date'),
                    appointment_time=function_args.get('appointment_time'),
                    service_type=function_args.get('service_type', 'General'),
                    phone_number=function_args.get('phone_number', ''),
                    call_id=self.call_sid
                )
            elif function_name == "get_availability":
                result = await get_availability(function_args.get('date'))
            
            # Send function result back to Voice Agent V1
            if result:
                response_message = {
                    "type": "FunctionCallResult",
                    "function_call_id": function_data.get('function_call_id'),
                    "result": result
                }
                
                logger.info(f"📤 Sending function result for call {self.call_sid}: {result}")
                await self.agent_connection.send(json.dumps(response_message))
            
        except Exception as e:
            logger.error(f"💥 Error handling function call for call {self.call_sid}: {e}")
    
    async def process_audio(self, audio_data):
        """Send audio from Twilio to Voice Agent V1"""
        try:
            if not self.agent_connection or not self.is_connected:
                return
                
            # Convert mulaw to linear16 for Voice Agent V1
            linear_audio = audioop.ulaw2lin(audio_data, 2)
            
            # Encode as base64
            audio_payload = base64.b64encode(linear_audio).decode('utf-8')
            
            # Send to Voice Agent V1
            message = {
                "type": "UserAudio",
                "audio": audio_payload
            }
            
            await self.agent_connection.send(json.dumps(message))
            
        except Exception as e:
            logger.error(f"💥 Error sending audio to Voice Agent V1 for call {self.call_sid}: {e}")
    
    async def close(self):
        """Close connections"""
        try:
            if self.agent_connection:
                await self.agent_connection.close()
            self.is_connected = False
            logger.info(f"🧹 Voice Agent V1 closed for call {self.call_sid}")
        except Exception as e:
            logger.error(f"💥 Error closing Voice Agent V1 for call {self.call_sid}: {e}")

# Global store for active voice agents
active_voice_agents_v1 = {}

async def handle_voice_agent_v1_websocket(websocket, path):
    """Handle WebSocket connection for Voice Agent V1"""
    call_sid = None
    voice_agent = None
    
    try:
        logger.info(f"🌟 NEW WEBSOCKET CONNECTION ATTEMPT!")
        logger.info(f"🔗 Full path: {path}")
        logger.info(f"🌐 WebSocket origin: {websocket.origin if hasattr(websocket, 'origin') else 'No origin'}")
        logger.info(f"📍 Remote address: {websocket.remote_address}")
        
        # Extract call_sid from path
        if 'call_sid=' in path:
            call_sid = path.split('call_sid=')[1].split('&')[0]
        
        if not call_sid:
            logger.error("❌ No call_sid provided in Voice Agent V1 WebSocket")
            await websocket.close()
            return
        
        logger.info(f"🎯 Voice Agent V1 WebSocket connected for call {call_sid}")
        logger.info(f"🔗 WebSocket path: {path}")
        logger.info(f"📞 Call SID extracted: {call_sid}")
        
        # Create and initialize voice agent V1
        voice_agent = VoiceAgentV1Handler(call_sid)
        voice_agent.twilio_websocket = websocket
        active_voice_agents_v1[call_sid] = voice_agent
        
        logger.info(f"🤖 Initializing Voice Agent V1 for call {call_sid}")
        success = await voice_agent.initialize_voice_agent()
        if not success:
            logger.error(f"❌ Failed to initialize Voice Agent V1 for call {call_sid}")
            await websocket.close()
            return
        
        logger.info(f"✅ Voice Agent V1 initialized successfully for call {call_sid}")
        
        # Handle incoming messages from Twilio
        async for message in websocket:
            try:
                data = json.loads(message)
                event = data.get('event')
                
                logger.info(f"📨 Received Twilio event: {event} for call {call_sid}")
                
                if event == 'connected':
                    logger.info(f"🔌 Twilio connected to Voice Agent V1 for call {call_sid}")
                    await websocket.send(json.dumps({"event": "connected"}))
                    
                elif event == 'start':
                    logger.info(f"🎬 Voice Agent V1 media stream started for call {call_sid}")
                    stream_sid = data.get('start', {}).get('streamSid')
                    logger.info(f"📺 Stream SID: {stream_sid}")
                    
                elif event == 'media':
                    # Process audio
                    payload = data.get('media', {}).get('payload')
                    if payload:
                        audio_data = base64.b64decode(payload)
                        logger.debug(f"🎵 Processing {len(audio_data)} bytes of audio for call {call_sid}")
                        await voice_agent.process_audio(audio_data)
                    else:
                        logger.warning(f"⚠️ Empty audio payload for call {call_sid}")
                        
                elif event == 'stop':
                    logger.info(f"🛑 Voice Agent V1 media stream stopped for call {call_sid}")
                    break
                else:
                    logger.info(f"❓ Unknown event: {event} for call {call_sid}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"🚫 Invalid JSON received from Twilio for call {call_sid}: {e}")
            except Exception as e:
                logger.error(f"💥 Error processing Voice Agent V1 message for call {call_sid}: {e}")
                import traceback
                logger.error(f"💥 Traceback: {traceback.format_exc()}")
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"🔌 Voice Agent V1 WebSocket closed for call {call_sid}")
    except Exception as e:
        logger.error(f"💥 Voice Agent V1 WebSocket error for call {call_sid}: {e}")
        import traceback
        logger.error(f"💥 Traceback: {traceback.format_exc()}")
    finally:
        if voice_agent:
            await voice_agent.close()
        if call_sid in active_voice_agents_v1:
            del active_voice_agents_v1[call_sid]
        logger.info(f"🧹 Cleaned up Voice Agent V1 for call {call_sid}")

async def start_voice_agent_v1_server():
    """Start Voice Agent V1 WebSocket server"""
    # Use environment variable for port, fallback to 8767 for local dev
    port = int(os.environ.get('WEBSOCKET_PORT', 8767))
    
    server = await websockets.serve(
        handle_voice_agent_v1_websocket, 
        "0.0.0.0", 
        port
    )
    logger.info(f"🚀 Voice Agent V1 WebSocket server started on port {port}")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(start_voice_agent_v1_server())
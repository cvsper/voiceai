import asyncio
import websockets
import json
import base64
import logging
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
import audioop
import struct
from voice_agent.functions import book_appointment, get_availability, cancel_appointment, trigger_crm_webhook
from models import db, Call, Transcript
from config import Config
import threading

logger = logging.getLogger(__name__)

class VoiceAgentHandler:
    def __init__(self, call_sid):
        self.call_sid = call_sid
        self.deepgram_client = DeepgramClient(Config.DEEPGRAM_API_KEY)
        self.live_connection = None
        self.twilio_websocket = None
        self.is_connected = False
        self.conversation_context = []
        
    async def initialize_deepgram(self):
        """Initialize Deepgram Live connection with Voice Agent capabilities"""
        try:
            logger.info(f"🎤 Configuring Deepgram options for call {self.call_sid}")
            
            # Configure for telephony with enhanced settings
            options = LiveOptions(
                model="nova-2",
                language="en-US",
                encoding="linear16",  # We'll convert from mulaw
                sample_rate=8000,
                channels=1,
                interim_results=True,
                punctuate=True,
                smart_format=True,
                utterance_end_ms=1500,
                vad_events=True,
                endpointing=300,
                keywords=["appointment", "booking", "schedule", "availability", "cancel"]
            )
            
            logger.info(f"🔗 Creating Deepgram live connection for call {self.call_sid}")
            self.live_connection = self.deepgram_client.listen.live.v("1")
            
            # Set up event handlers
            logger.info(f"🎧 Setting up event handlers for call {self.call_sid}")
            self.live_connection.on(LiveTranscriptionEvents.Open, self._on_open)
            self.live_connection.on(LiveTranscriptionEvents.Transcript, self._on_transcript)
            self.live_connection.on(LiveTranscriptionEvents.Error, self._on_error)
            self.live_connection.on(LiveTranscriptionEvents.Close, self._on_close)
            
            # Start the connection
            logger.info(f"🚀 Starting Deepgram connection for call {self.call_sid}")
            if await self.live_connection.start(options):
                self.is_connected = True
                logger.info(f"✅ Deepgram Voice Agent initialized for call {self.call_sid}")
                
                # Send initial greeting using Deepgram TTS
                logger.info(f"🎙️ Sending initial greeting with aura-2-amalthea-en voice for call {self.call_sid}")
                await self._speak("Hello! Welcome to our AI assistant. I'm here to help you with appointments, availability, and any questions you have about our services. How can I assist you today?")
                
                return True
            else:
                logger.error(f"❌ Failed to start Deepgram connection for call {self.call_sid}")
                return False
                
        except Exception as e:
            logger.error(f"💥 Error initializing Deepgram Voice Agent for call {self.call_sid}: {e}")
            import traceback
            logger.error(f"💥 Traceback: {traceback.format_exc()}")
            return False
    
    async def _speak(self, text):
        """Generate speech using Deepgram TTS with aura-2-amalthea-en voice"""
        try:
            logger.info(f"🗣️ Generating speech for call {self.call_sid}: '{text[:50]}...'")
            
            # Use Deepgram TTS API
            tts_options = {
                "model": "aura-2-amalthea-en",
                "encoding": "linear16",
                "sample_rate": 8000
            }
            
            logger.info(f"🎵 Calling Deepgram TTS with aura-2-amalthea-en for call {self.call_sid}")
            response = await self.deepgram_client.speak.v("1").stream(
                {"text": text}, 
                tts_options
            )
            
            logger.info(f"📡 TTS response status: {response.status_code} for call {self.call_sid}")
            
            if response.status_code == 200:
                logger.info(f"🎧 Streaming audio back to Twilio for call {self.call_sid}")
                chunk_count = 0
                
                # Stream audio back to Twilio
                async for chunk in response.iter_content():
                    if self.twilio_websocket and chunk:
                        chunk_count += 1
                        if chunk_count % 10 == 0:  # Log every 10th chunk
                            logger.debug(f"🎶 Sending audio chunk {chunk_count} ({len(chunk)} bytes) for call {self.call_sid}")
                        
                        # Convert to mulaw for Twilio
                        mulaw_audio = audioop.lin2ulaw(chunk, 2)
                        # Encode as base64
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
                        
                        # Small delay for natural speech flow
                        await asyncio.sleep(0.02)
                
                logger.info(f"✅ Completed streaming {chunk_count} audio chunks to Twilio for call {self.call_sid}")
            else:
                logger.error(f"❌ TTS failed with status {response.status_code} for call {self.call_sid}")
            
        except Exception as e:
            logger.error(f"💥 Error in TTS generation for call {self.call_sid}: {e}")
            import traceback
            logger.error(f"💥 Traceback: {traceback.format_exc()}")
    
    def _on_open(self, *args, **kwargs):
        """Deepgram connection opened"""
        logger.info(f"Deepgram connection opened for call {self.call_sid}")
    
    def _on_transcript(self, *args, **kwargs):
        """Handle transcript from Deepgram"""
        try:
            result = args[0] if args else kwargs.get('result')
            if not result:
                return
                
            transcript = result.channel.alternatives[0].transcript
            if not transcript.strip():
                return
                
            logger.info(f"Transcript for {self.call_sid}: {transcript}")
            
            # Save transcript to database
            transcript_record = Transcript(
                call_id=self.call_sid,
                text=transcript,
                speaker='caller',
                confidence=result.channel.alternatives[0].confidence
            )
            # We'll save this in the main thread to avoid database issues
            
            # Add to conversation context
            self.conversation_context.append({"role": "user", "content": transcript})
            
            # Process with AI and respond
            asyncio.create_task(self._process_and_respond(transcript))
            
        except Exception as e:
            logger.error(f"Error processing transcript: {e}")
    
    async def _process_and_respond(self, transcript):
        """Process transcript and generate AI response"""
        try:
            # Simple intent detection and response
            transcript_lower = transcript.lower()
            
            if any(word in transcript_lower for word in ['appointment', 'book', 'schedule']):
                if 'cancel' in transcript_lower:
                    response = "I can help you cancel an appointment. Could you please provide your appointment reference number or the name it was booked under?"
                else:
                    response = "I'd be happy to help you book an appointment. What type of service are you looking for, and what date would work best for you?"
                    
            elif any(word in transcript_lower for word in ['available', 'availability', 'when', 'time']):
                response = "Let me check our availability for you. What date are you interested in?"
                
            elif any(word in transcript_lower for word in ['hello', 'hi', 'hey']):
                response = "Hello! It's great to speak with you. I can help you book appointments, check our availability, or answer any questions about our services. What can I do for you today?"
                
            elif any(word in transcript_lower for word in ['help', 'service', 'what', 'how']):
                response = "I'm here to help! I can assist you with booking appointments, checking availability, answering questions about our services, or helping you manage existing appointments. What would you like to know?"
                
            elif any(word in transcript_lower for word in ['thank', 'thanks', 'bye', 'goodbye']):
                response = "You're very welcome! Thank you for calling. Have a wonderful day!"
                
            else:
                # Echo understanding and ask for clarification
                response = f"I understand you mentioned {transcript}. I can help you with booking appointments or checking availability. Could you tell me specifically what you'd like to do today?"
            
            # Add AI response to context
            self.conversation_context.append({"role": "assistant", "content": response})
            
            # Speak the response using aura voice
            await self._speak(response)
            
        except Exception as e:
            logger.error(f"Error processing and responding: {e}")
            # Fallback response
            await self._speak("I'm sorry, could you please repeat that? I want to make sure I help you properly.")
    
    def _on_error(self, *args, **kwargs):
        """Handle Deepgram errors"""
        error = args[0] if args else kwargs.get('error')
        logger.error(f"Deepgram error for call {self.call_sid}: {error}")
    
    def _on_close(self, *args, **kwargs):
        """Deepgram connection closed"""
        logger.info(f"Deepgram connection closed for call {self.call_sid}")
        self.is_connected = False
    
    async def process_audio(self, audio_data):
        """Process incoming audio from Twilio"""
        if self.live_connection and self.is_connected:
            try:
                # Convert mulaw to linear16 for Deepgram
                linear_audio = audioop.ulaw2lin(audio_data, 2)
                await self.live_connection.send(linear_audio)
            except Exception as e:
                logger.error(f"Error sending audio to Deepgram: {e}")
    
    async def close(self):
        """Close connections"""
        try:
            if self.live_connection:
                await self.live_connection.finish()
            self.is_connected = False
            logger.info(f"Voice Agent closed for call {self.call_sid}")
        except Exception as e:
            logger.error(f"Error closing Voice Agent: {e}")

# Global store for active voice agents
active_voice_agents = {}

async def handle_voice_agent_websocket(websocket, path):
    """Handle WebSocket connection for Voice Agent"""
    call_sid = None
    voice_agent = None
    
    try:
        # Extract call_sid from path
        if 'call_sid=' in path:
            call_sid = path.split('call_sid=')[1].split('&')[0]
        
        if not call_sid:
            logger.error("No call_sid provided in Voice Agent WebSocket")
            await websocket.close()
            return
        
        logger.info(f"🎯 Voice Agent WebSocket connected for call {call_sid}")
        logger.info(f"🔗 WebSocket path: {path}")
        
        # Create and initialize voice agent
        voice_agent = VoiceAgentHandler(call_sid)
        voice_agent.twilio_websocket = websocket
        active_voice_agents[call_sid] = voice_agent
        
        logger.info(f"🤖 Initializing Deepgram Voice Agent for call {call_sid}")
        success = await voice_agent.initialize_deepgram()
        if not success:
            logger.error(f"❌ Failed to initialize Voice Agent for call {call_sid}")
            await websocket.close()
            return
        
        logger.info(f"✅ Voice Agent initialized successfully for call {call_sid}")
        
        # Handle incoming messages from Twilio
        async for message in websocket:
            try:
                data = json.loads(message)
                event = data.get('event')
                
                logger.info(f"📨 Received Twilio event: {event} for call {call_sid}")
                
                if event == 'connected':
                    logger.info(f"🔌 Twilio connected to Voice Agent for call {call_sid}")
                    await websocket.send(json.dumps({"event": "connected"}))
                    
                elif event == 'start':
                    logger.info(f"🎬 Voice Agent media stream started for call {call_sid}")
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
                    logger.info(f"🛑 Voice Agent media stream stopped for call {call_sid}")
                    break
                else:
                    logger.info(f"❓ Unknown event: {event} for call {call_sid}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"🚫 Invalid JSON received from Twilio for call {call_sid}: {e}")
            except Exception as e:
                logger.error(f"💥 Error processing Voice Agent message for call {call_sid}: {e}")
                import traceback
                logger.error(f"💥 Traceback: {traceback.format_exc()}")
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"🔌 Voice Agent WebSocket closed for call {call_sid}")
    except Exception as e:
        logger.error(f"💥 Voice Agent WebSocket error for call {call_sid}: {e}")
        import traceback
        logger.error(f"💥 Traceback: {traceback.format_exc()}")
    finally:
        if voice_agent:
            await voice_agent.close()
        if call_sid in active_voice_agents:
            del active_voice_agents[call_sid]
        logger.info(f"🧹 Cleaned up Voice Agent for call {call_sid}")

async def start_voice_agent_server():
    """Start Voice Agent WebSocket server"""
    server = await websockets.serve(
        handle_voice_agent_websocket, 
        "0.0.0.0", 
        8766
    )
    logger.info("Voice Agent WebSocket server started on port 8766")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(start_voice_agent_server())
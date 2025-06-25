import asyncio
import websockets
import json
import base64
import logging
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from deepgram.clients.live.v1.client import LiveClient
from voice_agent.agent_config import get_voice_agent_config
from voice_agent.functions import book_appointment, get_availability, cancel_appointment, trigger_crm_webhook
from models import db, Call, Transcript
import threading
from flask import current_app

logger = logging.getLogger(__name__)

class TwilioDeepgramBridge:
    def __init__(self, call_sid, call_id=None):
        self.call_sid = call_sid
        self.call_id = call_id
        self.deepgram = None
        self.deepgram_connection = None
        self.twilio_websocket = None
        self.is_connected = False
        
    async def handle_twilio_websocket(self, websocket, path):
        """Handle incoming Twilio WebSocket connection"""
        self.twilio_websocket = websocket
        logger.info(f"Twilio WebSocket connected for call {self.call_sid}")
        
        try:
            # Initialize Deepgram connection
            await self.setup_deepgram()
            
            async for message in websocket:
                await self.process_twilio_message(message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Twilio WebSocket closed for call {self.call_sid}")
        except Exception as e:
            logger.error(f"Error in Twilio WebSocket handler: {e}")
        finally:
            await self.cleanup()
    
    async def setup_deepgram(self):
        """Initialize Deepgram Voice Agent connection"""
        try:
            config = current_app.config
            self.deepgram = DeepgramClient(config['DEEPGRAM_API_KEY'])
            
            # Configure for telephony (8kHz, mulaw)
            options = LiveOptions(
                model=config['VOICE_AGENT_MODEL'],
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
            
            self.deepgram_connection = self.deepgram.listen.live.v("1")
            
            # Set up event handlers
            self.deepgram_connection.on(LiveTranscriptionEvents.Open, self.on_deepgram_open)
            self.deepgram_connection.on(LiveTranscriptionEvents.Transcript, self.on_deepgram_transcript)
            self.deepgram_connection.on(LiveTranscriptionEvents.Error, self.on_deepgram_error)
            self.deepgram_connection.on(LiveTranscriptionEvents.Close, self.on_deepgram_close)
            
            # Start Deepgram connection
            await self.deepgram_connection.start(options)
            self.is_connected = True
            
        except Exception as e:
            logger.error(f"Failed to setup Deepgram: {e}")
            raise
    
    async def process_twilio_message(self, message):
        """Process incoming message from Twilio"""
        try:
            data = json.loads(message)
            event = data.get('event')
            
            if event == 'connected':
                logger.info(f"Twilio stream connected for call {self.call_sid}")
                
            elif event == 'start':
                logger.info(f"Twilio stream started for call {self.call_sid}")
                
            elif event == 'media':
                # Forward audio to Deepgram
                payload = data.get('media', {}).get('payload')
                if payload and self.deepgram_connection:
                    # Decode base64 mulaw audio
                    audio_data = base64.b64decode(payload)
                    await self.deepgram_connection.send(audio_data)
                    
            elif event == 'stop':
                logger.info(f"Twilio stream stopped for call {self.call_sid}")
                await self.cleanup()
                
        except Exception as e:
            logger.error(f"Error processing Twilio message: {e}")
    
    def on_deepgram_open(self, *args, **kwargs):
        """Deepgram connection opened"""
        logger.info(f"Deepgram connection opened for call {self.call_sid}")
    
    def on_deepgram_transcript(self, *args, **kwargs):
        """Handle transcript from Deepgram"""
        try:
            result = args[0] if args else kwargs.get('result')
            if not result:
                return
                
            transcript = result.channel.alternatives[0].transcript
            if not transcript:
                return
                
            # Save transcript to database
            if self.call_id:
                transcript_record = Transcript(
                    call_id=self.call_id,
                    text=transcript,
                    speaker='caller',
                    confidence=result.channel.alternatives[0].confidence
                )
                db.session.add(transcript_record)
                db.session.commit()
            
            # Check for function calls (this is simplified - real implementation would integrate with Voice Agent)
            # For MVP, we'll trigger functions based on keywords
            asyncio.create_task(self.process_transcript_for_functions(transcript))
            
        except Exception as e:
            logger.error(f"Error processing Deepgram transcript: {e}")
    
    async def process_transcript_for_functions(self, transcript):
        """Process transcript for potential function calls"""
        try:
            transcript_lower = transcript.lower()
            
            # Simple keyword detection for MVP
            if any(word in transcript_lower for word in ['book', 'schedule', 'appointment']):
                # In real implementation, this would be handled by Deepgram Voice Agent
                # For now, we'll just log the intent
                logger.info(f"Detected appointment booking intent: {transcript}")
                
                # Trigger CRM webhook for lead tracking
                crm_data = {
                    "intent": "appointment_booking",
                    "transcript": transcript,
                    "call_sid": self.call_sid
                }
                trigger_crm_webhook("lead", crm_data, self.call_id)
                
        except Exception as e:
            logger.error(f"Error processing transcript for functions: {e}")
    
    def on_deepgram_error(self, *args, **kwargs):
        """Handle Deepgram errors"""
        error = args[0] if args else kwargs.get('error')
        logger.error(f"Deepgram error for call {self.call_sid}: {error}")
    
    def on_deepgram_close(self, *args, **kwargs):
        """Deepgram connection closed"""
        logger.info(f"Deepgram connection closed for call {self.call_sid}")
        self.is_connected = False
    
    async def cleanup(self):
        """Clean up connections"""
        try:
            if self.deepgram_connection:
                await self.deepgram_connection.finish()
            self.is_connected = False
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Function calling handlers for Voice Agent
async def handle_function_call(function_name, parameters, call_id=None):
    """Handle function calls from Deepgram Voice Agent"""
    try:
        if function_name == "book_appointment":
            return book_appointment(
                customer_name=parameters.get('customer_name'),
                customer_phone=parameters.get('customer_phone'),
                appointment_date=parameters.get('appointment_date'),
                appointment_time=parameters.get('appointment_time'),
                service_type=parameters.get('service_type'),
                call_id=call_id
            )
            
        elif function_name == "get_availability":
            return get_availability(
                date=parameters.get('date'),
                call_id=call_id
            )
            
        elif function_name == "cancel_appointment":
            return cancel_appointment(
                reference_id=parameters.get('reference_id'),
                call_id=call_id
            )
            
        elif function_name == "trigger_crm_webhook":
            return trigger_crm_webhook(
                event_type=parameters.get('event_type'),
                data=parameters.get('data'),
                call_id=call_id
            )
        
        else:
            logger.warning(f"Unknown function call: {function_name}")
            return {
                "success": False,
                "message": "I'm sorry, I couldn't process that request."
            }
            
    except Exception as e:
        logger.error(f"Error handling function call {function_name}: {e}")
        return {
            "success": False,
            "message": "I'm sorry, there was an error processing your request."
        }
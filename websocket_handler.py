#!/usr/bin/env python3
"""
WebSocket handler for Twilio-Deepgram real-time voice streaming
Based on Deepgram's official Twilio integration documentation
"""

import asyncio
import websockets
import json
import base64
import logging
from flask import current_app
from services.deepgram_service import DeepgramService
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class TwilioDeepgramHandler:
    def __init__(self):
        self.deepgram_service = None
        self.openai_service = None
        self.call_sid = None
        self.conversation_context = []
        
    async def handle_twilio_stream(self, websocket, path):
        """Handle incoming WebSocket connection from Twilio"""
        logger.info(f"New WebSocket connection: {path}")
        
        try:
            # Initialize services
            self.deepgram_service = DeepgramService()
            self.openai_service = OpenAIService()
            
            # Send initial greeting
            await self.send_greeting(websocket)
            
            # Handle incoming messages
            async for message in websocket:
                await self.process_twilio_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket connection closed for {self.call_sid}")
        except Exception as e:
            logger.error(f"Error in WebSocket handler: {e}")
    
    async def send_greeting(self, websocket):
        """Send initial Deepgram greeting"""
        try:
            greeting_text = "Hello! Thank you for calling. I'm your AI assistant with Aura Amalthea voice technology. How can I help you today?"
            
            # Generate Deepgram TTS for greeting
            audio_data = await self.generate_deepgram_tts(greeting_text)
            
            if audio_data:
                # Send audio to Twilio
                await self.send_audio_to_twilio(websocket, audio_data)
                logger.info("Sent Deepgram greeting")
            else:
                logger.error("Failed to generate greeting audio")
                
        except Exception as e:
            logger.error(f"Error sending greeting: {e}")
    
    async def process_twilio_message(self, websocket, message):
        """Process incoming message from Twilio"""
        try:
            data = json.loads(message)
            event = data.get('event')
            
            if event == 'connected':
                self.call_sid = data.get('callSid')
                logger.info(f"Call connected: {self.call_sid}")
                
            elif event == 'start':
                logger.info(f"Media stream started for {self.call_sid}")
                
            elif event == 'media':
                # Handle incoming audio from caller
                await self.process_audio(websocket, data)
                
            elif event == 'stop':
                logger.info(f"Media stream stopped for {self.call_sid}")
                
        except Exception as e:
            logger.error(f"Error processing Twilio message: {e}")
    
    async def process_audio(self, websocket, data):
        """Process incoming audio and generate AI response"""
        try:
            # Get audio payload
            payload = data.get('media', {}).get('payload')
            if not payload:
                return
            
            # Decode audio (mulaw base64)
            audio_data = base64.b64decode(payload)
            
            # For now, we'll use a simple approach:
            # Accumulate audio and process after silence detection
            # In a full implementation, you'd use Deepgram streaming STT
            
            # Simulate transcription (replace with actual Deepgram streaming)
            transcribed_text = await self.simulate_transcription(audio_data)
            
            if transcribed_text:
                # Generate AI response
                ai_response = await self.generate_ai_response(transcribed_text)
                
                if ai_response:
                    # Generate Deepgram TTS
                    response_audio = await self.generate_deepgram_tts(ai_response)
                    
                    if response_audio:
                        # Send back to Twilio
                        await self.send_audio_to_twilio(websocket, response_audio)
                        logger.info(f"Sent AI response: {ai_response[:50]}...")
                        
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
    
    async def simulate_transcription(self, audio_data):
        """Simulate transcription - replace with actual Deepgram streaming"""
        # This is a placeholder - in real implementation use Deepgram streaming STT
        # For now, return a mock transcription to test the flow
        return "Hello, I need help with scheduling an appointment"
    
    async def generate_ai_response(self, user_input):
        """Generate AI response using OpenAI"""
        try:
            self.conversation_context.append({"role": "user", "content": user_input})
            
            # Use OpenAI to generate response
            intent_result = self.openai_service.analyze_intent(user_input)
            ai_response = intent_result.get('suggested_response', 'I understand. How can I help you?')
            
            self.conversation_context.append({"role": "assistant", "content": ai_response})
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I'm sorry, I didn't understand that. Could you please repeat?"
    
    async def generate_deepgram_tts(self, text):
        """Generate Deepgram TTS audio"""
        try:
            # Use Deepgram TTS with Aura Amalthea
            audio_data = self.deepgram_service.text_to_speech(text)
            return audio_data
            
        except Exception as e:
            logger.error(f"Error generating Deepgram TTS: {e}")
            return None
    
    async def send_audio_to_twilio(self, websocket, audio_data):
        """Send audio data back to Twilio"""
        try:
            # Encode audio as base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Create Twilio media message
            message = {
                "event": "media",
                "streamSid": "placeholder",  # This should be from the stream
                "media": {
                    "payload": audio_base64
                }
            }
            
            # Send to Twilio
            await websocket.send(json.dumps(message))
            
        except Exception as e:
            logger.error(f"Error sending audio to Twilio: {e}")

# WebSocket server
async def start_websocket_server():
    """Start the WebSocket server for Twilio streams"""
    handler = TwilioDeepgramHandler()
    
    # Start server on port 8000
    server = await websockets.serve(
        handler.handle_twilio_stream,
        "0.0.0.0",
        8000
    )
    
    logger.info("WebSocket server started on port 8000")
    return server

if __name__ == "__main__":
    # Run the WebSocket server
    asyncio.get_event_loop().run_until_complete(start_websocket_server())
    asyncio.get_event_loop().run_forever()
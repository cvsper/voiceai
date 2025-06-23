from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class TwilioService:
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        try:
            self.client = Client(
                current_app.config['TWILIO_ACCOUNT_SID'],
                current_app.config['TWILIO_AUTH_TOKEN']
            )
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            raise
    
    def handle_incoming_call(self, call_sid, from_number, to_number):
        """Handle incoming call and return TwiML response with ElevenLabs voice"""
        try:
            response = VoiceResponse()
            base_url = current_app.config.get('BASE_URL', 'https://voiceai-eh24.onrender.com')
            
            # Use Deepgram voice for the most natural AI sound
            try:
                if current_app.config.get('DEEPGRAM_API_KEY'):
                    logger.info(f"Attempting Deepgram TTS for call {call_sid}")
                    # Generate greeting with Deepgram TTS
                    from services.deepgram_service import DeepgramService
                    deepgram_service = DeepgramService()
                    
                    greeting_text = "Hello! Thank you for calling. I'm your AI assistant with Aura Amalthea voice technology. How can I help you today?"
                    
                    # Try to generate Deepgram voice with timeout protection
                    try:
                        audio_url = deepgram_service.text_to_speech_url(greeting_text)
                        
                        if audio_url:
                            response.play(audio_url)
                            logger.info(f"Using Deepgram voice greeting for call {call_sid}: {audio_url}")
                        else:
                            logger.warning(f"Deepgram TTS returned None for call {call_sid}")
                            raise Exception("Deepgram TTS returned None")
                    except Exception as tts_error:
                        logger.error(f"Deepgram TTS generation failed for call {call_sid}: {tts_error}")
                        raise Exception(f"Deepgram TTS failed: {tts_error}")
                else:
                    raise Exception("Deepgram API key not configured")
                    
            except Exception as deepgram_error:
                logger.info(f"Deepgram voice not available, using premium Twilio voice: {deepgram_error}")
                # Fallback to premium Twilio neural voice
                response.say(
                    "Hello! Thank you for calling. I'm your AI assistant powered by advanced voice technology. How can I help you today?",
                    voice='Polly.Joanna-Neural',  # Neural voice for more natural sound
                    language='en-US'
                )
            
            # Start recording for transcription and conversation
            response.record(
                action=f"{base_url}/webhooks/recording",
                method='POST',
                max_length=300,  # 5 minutes max
                transcribe=True,
                transcribe_callback=f"{base_url}/webhooks/transcribe",
                play_beep=False  # More natural conversation
            )
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Error handling incoming call {call_sid}: {e}")
            response = VoiceResponse()
            response.say("Hello! Thank you for calling.", voice='Polly.Joanna')
            return str(response)
    
    def handle_conference_call(self, call_sid, participants):
        """Set up conference call for monitoring human-to-human conversations"""
        try:
            response = VoiceResponse()
            
            # Create conference room
            dial = response.dial()
            conference = dial.conference(
                f"monitor-{call_sid}",
                start_conference_on_enter=True,
                end_conference_on_exit=False,
                record=True,
                status_callback=f"{current_app.config['BASE_URL']}/webhooks/conference-status",
                status_callback_event="start end join leave mute hold"
            )
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Error setting up conference call {call_sid}: {e}")
            response = VoiceResponse()
            response.say("I'm sorry, there was an error setting up the conference. Please try again.")
            return str(response)
    
    def generate_ai_response(self, user_input, call_sid):
        """Generate TwiML response with AI-generated speech"""
        try:
            response = VoiceResponse()
            
            # This will be replaced with actual AI response
            ai_text = f"I understand you said: {user_input}. Let me help you with that."
            
            response.say(ai_text, voice='alice', language='en-US')
            
            # Continue recording for more input
            response.record(
                action=f"{current_app.config['BASE_URL']}/webhooks/recording",
                method='POST',
                max_length=300,
                transcribe=True,
                transcribe_callback=f"{current_app.config['BASE_URL']}/webhooks/transcribe"
            )
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Error generating AI response for call {call_sid}: {e}")
            response = VoiceResponse()
            response.say("I'm sorry, I didn't understand that. Could you please repeat?")
            return str(response)
    
    def end_call(self, call_sid):
        """End the call gracefully"""
        try:
            response = VoiceResponse()
            response.say("Thank you for calling. Have a great day!")
            response.hangup()
            return str(response)
        except Exception as e:
            logger.error(f"Error ending call {call_sid}: {e}")
            response = VoiceResponse()
            response.hangup()
            return str(response)
    
    def make_outbound_call(self, to_number, message):
        """Make an outbound call with a message"""
        try:
            call = self.client.calls.create(
                twiml=f'<Response><Say>{message}</Say></Response>',
                to=to_number,
                from_=current_app.config['TWILIO_PHONE_NUMBER']
            )
            return call.sid
        except Exception as e:
            logger.error(f"Error making outbound call to {to_number}: {e}")
            raise
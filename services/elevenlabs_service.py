import requests
import logging
from flask import current_app
import io

logger = logging.getLogger(__name__)

class ElevenLabsService:
    def __init__(self):
        self.api_key = None
        self.voice_id = None
        self.base_url = "https://api.elevenlabs.io/v1"
        self._initialize_client()
    
    def _initialize_client(self):
        try:
            self.api_key = current_app.config['ELEVENLABS_API_KEY']
            self.voice_id = current_app.config['ELEVENLABS_VOICE_ID']
        except Exception as e:
            logger.error(f"Failed to initialize ElevenLabs client: {e}")
            raise
    
    def text_to_speech(self, text, voice_id=None):
        """Convert text to speech using ElevenLabs API"""
        try:
            if not voice_id:
                voice_id = self.voice_id
            
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error converting text to speech: {e}")
            return None
    
    def text_to_speech_stream(self, text, voice_id=None):
        """Convert text to speech with streaming for faster response"""
        try:
            if not voice_id:
                voice_id = self.voice_id
            
            url = f"{self.base_url}/text-to-speech/{voice_id}/stream"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            response = requests.post(url, json=data, headers=headers, stream=True)
            
            if response.status_code == 200:
                audio_chunks = []
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        audio_chunks.append(chunk)
                return b''.join(audio_chunks)
            else:
                logger.error(f"ElevenLabs streaming API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error in streaming text to speech: {e}")
            return None
    
    def get_voices(self):
        """Get available voices from ElevenLabs"""
        try:
            url = f"{self.base_url}/voices"
            
            headers = {
                "Accept": "application/json",
                "xi-api-key": self.api_key
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error fetching voices: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return None
    
    def create_twilio_compatible_audio(self, text, voice_id=None):
        """Create audio compatible with Twilio's requirements"""
        try:
            # Get audio from ElevenLabs
            audio_data = self.text_to_speech_stream(text, voice_id)
            
            if audio_data:
                # Twilio expects specific audio formats
                # We might need to convert the audio format here
                # For now, returning the raw audio data
                return audio_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating Twilio-compatible audio: {e}")
            return None
    
    def save_audio_file(self, audio_data, filename):
        """Save audio data to file"""
        try:
            with open(filename, 'wb') as f:
                f.write(audio_data)
            return True
        except Exception as e:
            logger.error(f"Error saving audio file {filename}: {e}")
            return False
    
    def text_to_speech_url(self, text, voice_id=None):
        """Convert text to speech and return a URL for Twilio to play"""
        try:
            import os
            import uuid
            from flask import url_for
            
            # Generate audio
            audio_data = self.text_to_speech_stream(text, voice_id)
            
            if audio_data:
                # Create unique filename
                audio_id = str(uuid.uuid4())
                audio_filename = f"{audio_id}.mp3"
                
                # Save to static directory that Flask can serve
                static_dir = os.path.join(current_app.instance_path, 'static', 'audio')
                os.makedirs(static_dir, exist_ok=True)
                
                audio_path = os.path.join(static_dir, audio_filename)
                
                if self.save_audio_file(audio_data, audio_path):
                    # Return URL that Twilio can access
                    base_url = current_app.config.get('BASE_URL', 'http://localhost:5001')
                    audio_url = f"{base_url}/static/audio/{audio_filename}"
                    return audio_url
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating audio URL: {e}")
            return None
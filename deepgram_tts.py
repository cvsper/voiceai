import asyncio
import logging
from deepgram import DeepgramClient
from config import Config
import os
import tempfile
import uuid

logger = logging.getLogger(__name__)

class DeepgramTTS:
    def __init__(self):
        self.client = DeepgramClient(Config.DEEPGRAM_API_KEY)
    
    async def text_to_speech(self, text, voice="aura-2-amalthea-en"):
        """Convert text to speech using Deepgram's aura voice"""
        try:
            # Configure TTS options
            options = {
                "model": voice,
                "encoding": "mp3",
                "container": "mp3"
            }
            
            # Generate speech
            response = await self.client.speak.v("1").stream_raw(
                {"text": text},
                options
            )
            
            if response.status_code == 200:
                # Save to temporary file
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix='.mp3',
                    dir='/tmp'
                )
                
                with open(temp_file.name, 'wb') as f:
                    async for chunk in response.iter_bytes():
                        f.write(chunk)
                
                return temp_file.name
            else:
                logger.error(f"Deepgram TTS failed with status: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error in Deepgram TTS: {e}")
            return None

# Global TTS instance
deepgram_tts = DeepgramTTS()

async def generate_speech_file(text, voice="aura-2-amalthea-en"):
    """Generate speech file using Deepgram TTS"""
    return await deepgram_tts.text_to_speech(text, voice)
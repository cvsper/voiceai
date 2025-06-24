import json
import logging
from flask import current_app

logger = logging.getLogger(__name__)

class DeepgramService:
    def __init__(self):
        self.api_key = None
        self.deepgram = None
        self._audio_cache = {}
        self._initialize_client()
        self._pregenerate_common_responses()
    
    def _initialize_client(self):
        try:
            self.api_key = current_app.config.get('DEEPGRAM_API_KEY')
            if not self.api_key:
                logger.warning("Deepgram API key not configured")
            else:
                # Try to import and initialize Deepgram client
                try:
                    from deepgram import DeepgramClient
                    self.deepgram = DeepgramClient(self.api_key)
                    logger.info("Deepgram client initialized successfully")
                except ImportError:
                    logger.warning("Deepgram SDK not available, using mock implementation")
        except Exception as e:
            logger.error(f"Failed to initialize Deepgram client: {e}")
    
    async def transcribe_streaming(self, audio_stream, callback):
        """Transcribe streaming audio in real-time"""
        # Simplified version - for now just mock the callback
        logger.info("Streaming transcription requested - using mock implementation")
        try:
            # This would be implemented with actual Deepgram streaming
            await callback({
                'transcript': 'Mock transcription from audio stream',
                'is_final': True,
                'confidence': 0.9,
                'speaker': 'speaker_0',
                'timestamp': 0
            })
        except Exception as e:
            logger.error(f"Error in streaming transcription: {e}")
    
    def transcribe_file(self, audio_file_url):
        """Transcribe a recorded audio file"""
        try:
            if not self.deepgram:
                logger.warning("Deepgram client not available, returning mock data")
                return [{
                    'text': 'Mock transcription of recorded audio file',
                    'start': 0,
                    'end': 30,
                    'speaker': 0,
                    'confidence': 0.85
                }]
            
            # Try to use actual Deepgram transcription
            try:
                from deepgram import PrerecordedOptions
                
                options = PrerecordedOptions(
                    model="nova-2",
                    smart_format=True,
                    punctuate=True,
                    diarize=True,
                    language="en-US"
                )
                
                # For Twilio URLs, we need to download the file first since they require auth
                if "twilio.com" in audio_file_url:
                    # Download the file using Twilio credentials
                    import requests
                    import tempfile
                    import os
                    
                    twilio_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
                    twilio_token = current_app.config.get('TWILIO_AUTH_TOKEN')
                    
                    if twilio_sid and twilio_token:
                        try:
                            # Twilio recording URLs need .mp3 appended to get the actual media
                            media_url = audio_file_url
                            if not media_url.endswith(('.mp3', '.wav')):
                                media_url = f"{audio_file_url}.mp3"
                            
                            auth = (twilio_sid, twilio_token)
                            logger.info(f"Downloading recording from: {media_url}")
                            
                            # Retry mechanism - recordings might not be immediately available
                            import time
                            max_retries = 5
                            retry_delay = 3  # seconds
                            
                            response_download = None
                            for attempt in range(max_retries):
                                try:
                                    response_download = requests.get(media_url, auth=auth, timeout=30)
                                    response_download.raise_for_status()
                                    logger.info(f"Successfully downloaded recording on attempt {attempt + 1}")
                                    break
                                except requests.exceptions.HTTPError as e:
                                    if e.response.status_code == 404 and attempt < max_retries - 1:
                                        logger.info(f"Recording not ready yet (attempt {attempt + 1}/{max_retries}), waiting {retry_delay}s...")
                                        time.sleep(retry_delay)
                                        retry_delay *= 1.5  # Exponential backoff
                                    else:
                                        raise
                            
                            if not response_download:
                                raise Exception("Failed to download after all retries")
                            
                            # Create temporary file
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                                temp_file.write(response_download.content)
                                temp_path = temp_file.name
                            
                            # Transcribe using file
                            logger.info(f"Starting Deepgram transcription for file: {temp_path}")
                            with open(temp_path, 'rb') as audio_file:
                                payload = {"buffer": audio_file.read()}
                                response = self.deepgram.listen.prerecorded.v("1").transcribe_file(
                                    payload, options
                                )
                                logger.info("Deepgram transcription request completed")
                            
                            # Clean up temp file
                            os.unlink(temp_path)
                            
                        except Exception as download_error:
                            logger.error(f"Failed to download Twilio recording: {download_error}")
                            return self._get_mock_data()
                    else:
                        logger.error("Twilio credentials not configured for recording download")
                        return self._get_mock_data()
                else:
                    # Direct URL transcription for non-Twilio URLs
                    response = self.deepgram.listen.prerecorded.v("1").transcribe_url(
                        {"url": audio_file_url}, options
                    )
                
                # Process response
                if response.results and response.results.channels:
                    transcript_data = []
                    channel = response.results.channels[0]
                    
                    if channel.alternatives:
                        alternative = channel.alternatives[0]
                        
                        # Check if we have paragraphs (diarization) or just transcript
                        if hasattr(alternative, 'paragraphs') and alternative.paragraphs:
                            for paragraph in alternative.paragraphs.paragraphs:
                                for sentence in paragraph.sentences:
                                    transcript_data.append({
                                        'text': sentence.text,
                                        'start': sentence.start,
                                        'end': sentence.end,
                                        'speaker': getattr(paragraph, 'speaker', 0),
                                        'confidence': getattr(sentence, 'confidence', alternative.confidence if hasattr(alternative, 'confidence') else 0.9)
                                    })
                        else:
                            # Fallback to simple transcript without diarization
                            transcript_data.append({
                                'text': alternative.transcript,
                                'start': 0,
                                'end': 0,
                                'speaker': 0,
                                'confidence': getattr(alternative, 'confidence', 0.9)
                            })
                    
                    return transcript_data if transcript_data else self._get_mock_data()
                
            except Exception as deepgram_error:
                logger.error(f"Deepgram transcription failed: {deepgram_error}")
                return self._get_mock_data()
            
        except Exception as e:
            logger.error(f"Error transcribing file {audio_file_url}: {e}")
            return []
    
    def _get_mock_data(self):
        """Return mock transcription data"""
        return [{
            'text': 'This is a mock transcription of the audio file. The actual Deepgram integration will replace this when properly configured.',
            'start': 0,
            'end': 30,
            'speaker': 0,
            'confidence': 0.85
        }]
    
    def text_to_speech(self, text):
        """Convert text to speech using Deepgram's TTS API"""
        try:
            if not self.deepgram or not self.api_key:
                logger.warning("Deepgram TTS not available - client not initialized")
                return None
            
            # Use Deepgram's text-to-speech with Aura 2 - Amalthea voice
            from deepgram import SpeakOptions
            
            options = SpeakOptions(
                model="aura-2-amalthea-en",  # Aura 2 - Amalthea (Filipina, feminine voice)
                encoding="mulaw",     # Faster mulaw encoding for telephony
                sample_rate=8000,     # 8kHz telephony sample rate  
                container="wav"       # WAV container for compatibility
            )
            
            # Use the correct API method for streaming audio
            logger.info(f"Generating Deepgram TTS with Aura Amalthea for text: {text[:50]}...")
            
            response = self.deepgram.speak.v("1").stream(
                {"text": text}, 
                options
            )
            
            # Handle the streaming response
            if hasattr(response, 'stream'):
                # Collect audio chunks
                audio_chunks = []
                for chunk in response.stream:
                    audio_chunks.append(chunk)
                
                if audio_chunks:
                    audio_data = b''.join(audio_chunks)
                    logger.info(f"Deepgram TTS (Aura Amalthea) conversion successful - {len(audio_data)} bytes")
                    return audio_data
                else:
                    logger.warning("Deepgram TTS stream contained no data")
                    return None
            elif hasattr(response, 'content'):
                # Direct response content
                logger.info(f"Deepgram TTS (Aura Amalthea) conversion successful - {len(response.content)} bytes")
                return response.content
            else:
                # Try to read response as bytes
                try:
                    if isinstance(response, bytes):
                        logger.info(f"Deepgram TTS (Aura Amalthea) conversion successful - {len(response)} bytes")
                        return response
                    else:
                        logger.warning(f"Unexpected Deepgram response type: {type(response)}")
                        return None
                except Exception as resp_error:
                    logger.error(f"Error processing Deepgram response: {resp_error}")
                    return None
                
        except Exception as e:
            logger.error(f"Error in Deepgram text-to-speech: {e}")
            return None
    
    def text_to_speech_url(self, text):
        """Convert text to speech and return a URL for Twilio to play"""
        try:
            import uuid
            from flask import current_app
            
            # Generate audio
            audio_data = self.text_to_speech(text)
            
            if audio_data:
                # Store audio data in app context instead of file system
                audio_id = str(uuid.uuid4())
                
                # Store in Flask app context for serving
                if not hasattr(current_app, '_deepgram_audio_cache'):
                    current_app._deepgram_audio_cache = {}
                
                current_app._deepgram_audio_cache[audio_id] = audio_data
                logger.info(f"Stored Deepgram audio in memory: {audio_id} ({len(audio_data)} bytes)")
                
                # Return URL that Twilio can access
                base_url = current_app.config.get('BASE_URL', 'http://localhost:5001')
                audio_url = f"{base_url}/api/audio/{audio_id}"
                logger.info(f"Deepgram TTS URL: {audio_url}")
                return audio_url
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating Deepgram TTS URL: {e}")
            return None
    
    def _pregenerate_common_responses(self):
        """Pre-generate audio for common responses to reduce delay"""
        try:
            if not self.deepgram:
                return
                
            common_responses = [
                "I'm processing your request. Please continue.",
                "I understand. How can I help you with that?",
                "Thank you for that information. What else can I help you with?",
                "I'm here to help you. Please tell me more.",
                "Let me help you with that request.",
                "I understand your request. Let me assist you.",
                "Thank you for calling. How may I help you today?",
                "I'm listening. Please continue.",
                "How can I assist you further?",
                "I'm ready to help you with that."
            ]
            
            logger.info("Pre-generating common response audio...")
            for response_text in common_responses:
                try:
                    audio_data = self.text_to_speech(response_text)
                    if audio_data:
                        # Cache using a hash of the text
                        import hashlib
                        text_hash = hashlib.md5(response_text.encode()).hexdigest()
                        self._audio_cache[text_hash] = {
                            'text': response_text,
                            'audio_data': audio_data
                        }
                        logger.info(f"Pre-generated audio for: {response_text[:30]}...")
                except Exception as e:
                    logger.warning(f"Failed to pre-generate audio for '{response_text[:30]}...': {e}")
                    
            logger.info(f"Pre-generated {len(self._audio_cache)} common responses")
            
        except Exception as e:
            logger.error(f"Error in pre-generation: {e}")
    
    def get_cached_response_url(self, text):
        """Get pre-cached audio URL for common responses"""
        try:
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            
            if text_hash in self._audio_cache:
                cached_item = self._audio_cache[text_hash]
                audio_data = cached_item['audio_data']
                
                # Store in Flask app context for serving
                import uuid
                from flask import current_app
                
                audio_id = str(uuid.uuid4())
                if not hasattr(current_app, '_deepgram_audio_cache'):
                    current_app._deepgram_audio_cache = {}
                
                current_app._deepgram_audio_cache[audio_id] = audio_data
                
                base_url = current_app.config.get('BASE_URL', 'http://localhost:5001')
                audio_url = f"{base_url}/api/audio/{audio_id}"
                
                logger.info(f"Using pre-cached audio for: {text[:30]}...")
                return audio_url
                
        except Exception as e:
            logger.error(f"Error getting cached response: {e}")
            
        return None
    
    def process_twilio_transcription(self, transcription_text, call_sid):
        """Process Twilio's built-in transcription"""
        try:
            return {
                'text': transcription_text,
                'source': 'twilio',
                'call_sid': call_sid,
                'processed_at': 'now'
            }
        except Exception as e:
            logger.error(f"Error processing Twilio transcription for call {call_sid}: {e}")
            return None
import json
import logging
from flask import current_app

logger = logging.getLogger(__name__)

class DeepgramService:
    def __init__(self):
        self.api_key = None
        self.deepgram = None
        self._initialize_client()
    
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
                            
                            # Download the recording with auth
                            auth = (twilio_sid, twilio_token)
                            logger.info(f"Downloading recording from: {media_url}")
                            response_download = requests.get(media_url, auth=auth)
                            response_download.raise_for_status()
                            
                            # Create temporary file
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                                temp_file.write(response_download.content)
                                temp_path = temp_file.name
                            
                            # Transcribe using file
                            with open(temp_path, 'rb') as audio_file:
                                response = self.deepgram.listen.prerecorded.v("1").transcribe_file(
                                    {"buffer": audio_file}, options
                                )
                            
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
                        for paragraph in channel.alternatives[0].paragraphs.paragraphs:
                            for sentence in paragraph.sentences:
                                transcript_data.append({
                                    'text': sentence.text,
                                    'start': sentence.start,
                                    'end': sentence.end,
                                    'speaker': paragraph.speaker,
                                    'confidence': sentence.confidence
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
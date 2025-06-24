import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///voiceai.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Quart/Flask compatibility settings
    PROVIDE_AUTOMATIC_OPTIONS = True
    CORS_HEADERS = 'Content-Type'
    EXPLAIN_TEMPLATE_LOADING = False
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    
    # Deepgram Configuration
    DEEPGRAM_API_KEY = os.environ.get('DEEPGRAM_API_KEY')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # ElevenLabs Configuration
    ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY')
    ELEVENLABS_VOICE_ID = os.environ.get('ELEVENLABS_VOICE_ID')
    
    # Google Calendar Configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI')
    
    # Basic Authentication
    AUTH_USERNAME = os.environ.get('AUTH_USERNAME') or 'admin'
    AUTH_PASSWORD = os.environ.get('AUTH_PASSWORD') or 'password'
    
    # App Configuration
    BASE_URL = os.environ.get('BASE_URL') or 'http://localhost:5000'
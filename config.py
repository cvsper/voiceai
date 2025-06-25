import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///voiceai.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Deepgram
    DEEPGRAM_API_KEY = os.environ.get('DEEPGRAM_API_KEY')
    
    # Twilio
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    
    # CRM
    CRM_WEBHOOK_URL = os.environ.get('CRM_WEBHOOK_URL')
    
    # Voice Agent Configuration
    VOICE_AGENT_MODEL = 'nova-2'
    VOICE_AGENT_VOICE = 'aura-asteria-en'
#!/usr/bin/env python3
"""
Generate ElevenLabs greeting audio file for Twilio calls
Run this script to create the static greeting file
"""

import os
import sys
from flask import Flask
from config import Config
from services.elevenlabs_service import ElevenLabsService

def generate_greeting_audio():
    """Generate ElevenLabs greeting audio file"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    with app.app_context():
        try:
            elevenlabs_service = ElevenLabsService()
            
            # Generate greeting text
            greeting_text = "Hello! Thank you for calling. I'm your AI assistant powered by advanced voice technology. How can I help you today?"
            
            # Generate audio
            print("Generating ElevenLabs audio...")
            audio_data = elevenlabs_service.text_to_speech_stream(greeting_text)
            
            if audio_data:
                # Create static directory
                static_dir = "static"
                os.makedirs(static_dir, exist_ok=True)
                
                # Save greeting file
                greeting_path = os.path.join(static_dir, "greeting.mp3")
                with open(greeting_path, 'wb') as f:
                    f.write(audio_data)
                
                print(f"✅ ElevenLabs greeting saved to: {greeting_path}")
                print(f"📁 File size: {len(audio_data)} bytes")
                
                return True
            else:
                print("❌ Failed to generate ElevenLabs audio")
                return False
                
        except Exception as e:
            print(f"❌ Error generating greeting: {e}")
            return False

if __name__ == "__main__":
    success = generate_greeting_audio()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Basic test script to verify the Flask app can start
"""

if __name__ == '__main__':
    try:
        print("Testing basic imports...")
        
        from flask import Flask
        print("✅ Flask import successful")
        
        from config import Config
        print("✅ Config import successful")
        
        from models import db
        print("✅ Models import successful")
        
        # Test basic Flask app creation
        app = Flask(__name__)
        app.config.from_object(Config)
        print("✅ Flask app creation successful")
        
        # Test basic route
        @app.route('/')
        def test():
            return {'status': 'ok'}
        
        print("✅ Basic route creation successful")
        print("🎉 All basic tests passed - Flask app should start!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
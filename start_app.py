#!/usr/bin/env python3
"""
Startup script for Voice AI Dashboard
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def main():
    print("🚀 Starting Voice AI Dashboard...")
    
    # Change to the app directory
    app_dir = Path(__file__).parent
    os.chdir(app_dir)
    
    # Check if .env exists
    if not Path('.env').exists():
        print("❌ .env file not found!")
        print("Please create .env file with your API keys")
        return False
    
    # Check if frontend is built
    dist_dir = Path('demo/dist')
    if not dist_dir.exists():
        print("📦 Building frontend...")
        try:
            subprocess.run(['python3', 'build_frontend.py'], check=True)
        except subprocess.CalledProcessError:
            print("❌ Frontend build failed")
            return False
    
    print("✅ Environment check passed")
    print("🌐 Starting Flask server on http://localhost:5001")
    print("📊 Dashboard will be available at http://localhost:5001")
    print("🔑 Login with: admin / password")
    print("\n" + "="*50)
    print("Press Ctrl+C to stop the server")
    print("="*50 + "\n")
    
    # Start the Flask app
    try:
        subprocess.run(['python3', 'app.py'], check=True)
    except KeyboardInterrupt:
        print("\n👋 Shutting down Voice AI Dashboard...")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Flask app failed to start: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
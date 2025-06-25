#!/usr/bin/env python3
"""
Ultra-simple Flask app for Railway deployment testing
"""
import os
import logging
from flask import Flask, jsonify
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create simple Flask app
app = Flask(__name__)

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'status': 'Voice AI Assistant',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'message': 'Railway deployment successful!'
    })

@app.route('/api/health')
def health():
    """Ultra-simple health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/webhooks/voice', methods=['POST'])
def voice_webhook():
    """Simple voice webhook"""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">Hello! This is a test of our Railway deployment. The webhook is working!</Say>
    <Hangup/>
</Response>''', 200, {'Content-Type': 'text/xml'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    logger.info(f"🚀 Starting simple Flask app on port {port}")
    
    app.run(
        debug=False,
        host='0.0.0.0',
        port=port,
        threaded=True
    )
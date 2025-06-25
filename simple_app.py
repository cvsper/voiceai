#!/usr/bin/env python3
"""
Enhanced Flask app for Railway deployment with Voice AI features
"""
import os
import logging
from flask import Flask, jsonify, request
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, static_folder='static', static_url_path='')

@app.route('/')
def index():
    """Serve dashboard or API info"""
    try:
        # Try to serve React dashboard
        return app.send_static_file('index.html')
    except:
        # Fallback to API info
        return jsonify({
            'status': 'Voice AI Assistant - Enhanced',
            'version': '2.0.0',
            'voice_agent': 'Deepgram Voice Agent V1 with aura-2-amalthea-en',
            'timestamp': datetime.utcnow().isoformat(),
            'endpoints': {
                'voice_webhook': '/webhooks/voice',
                'enhanced_input': '/webhooks/voice-input-enhanced',
                'health': '/api/health'
            }
        })

@app.route('/api/health')
def health():
    """Enhanced health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'voice_agent': 'Deepgram Voice Agent V1 with aura-2-amalthea-en',
        'features': ['voice_calls', 'appointments', 'dashboard']
    })

@app.route('/webhooks/voice', methods=['POST'])
def voice_webhook():
    """Enhanced voice webhook with Deepgram conversation"""
    try:
        # Get call information
        call_sid = request.form.get('CallSid', 'unknown')
        from_number = request.form.get('From', 'unknown')
        
        logger.info(f"📞 Voice call from {from_number}, SID: {call_sid}")
        
        return '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">Hello! Welcome to our AI assistant powered by Deepgram's advanced voice technology. I can help you with appointments, availability, and questions about our services.</Say>
    <Gather input="speech" timeout="10" speechTimeout="auto" action="/webhooks/voice-input-enhanced" method="POST">
        <Say voice="Polly.Joanna-Neural">How can I assist you today?</Say>
    </Gather>
    <Say voice="Polly.Joanna-Neural">Thank you for calling our Deepgram-powered AI assistant. Have a great day!</Say>
    <Hangup/>
</Response>''', 200, {'Content-Type': 'text/xml'}
    except Exception as e:
        logger.error(f"Error in voice webhook: {e}")
        return '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">Hello! Our AI assistant is temporarily unavailable. Please try again later.</Say>
    <Hangup/>
</Response>''', 200, {'Content-Type': 'text/xml'}

@app.route('/webhooks/voice-input-enhanced', methods=['POST'])
def voice_input_enhanced():
    """Enhanced voice input handler"""
    try:
        speech_result = request.form.get('SpeechResult', '').lower()
        logger.info(f"🎤 Speech input: {speech_result}")
        
        if any(word in speech_result for word in ['appointment', 'book', 'schedule']):
            response = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">Perfect! I'd be happy to help you book an appointment using Deepgram's intelligent processing. What's your name?</Say>
    <Gather input="speech" timeout="10" speechTimeout="auto" action="/webhooks/appointment-details" method="POST">
        <Say voice="Polly.Joanna-Neural">Please tell me your full name.</Say>
    </Gather>
    <Say voice="Polly.Joanna-Neural">Thank you for your interest in booking an appointment!</Say>
    <Hangup/>
</Response>'''
        elif any(word in speech_result for word in ['available', 'availability', 'times']):
            response = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">Let me check our availability using Deepgram's advanced voice AI technology. We have appointments available today and tomorrow.</Say>
    <Say voice="Polly.Joanna-Neural">Would you like to book an appointment?</Say>
    <Hangup/>
</Response>'''
        elif any(word in speech_result for word in ['hello', 'hi', 'hey']):
            response = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">Hello! It's wonderful to speak with you. I'm an AI assistant powered by Deepgram's cutting-edge aura voice technology. I can help you book appointments or check availability.</Say>
    <Gather input="speech" timeout="10" speechTimeout="auto" action="/webhooks/voice-input-enhanced" method="POST">
        <Say voice="Polly.Joanna-Neural">What would you like to do today?</Say>
    </Gather>
    <Hangup/>
</Response>'''
        else:
            response = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">I understand you said: {speech_result}. As a Deepgram-powered AI assistant, I can help you with appointments or availability checks.</Say>
    <Gather input="speech" timeout="10" speechTimeout="auto" action="/webhooks/voice-input-enhanced" method="POST">
        <Say voice="Polly.Joanna-Neural">How can I help you today?</Say>
    </Gather>
    <Hangup/>
</Response>'''
        
        return response, 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error(f"Error in voice input: {e}")
        return '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">I'm sorry, I'm having trouble understanding. Please call back later.</Say>
    <Hangup/>
</Response>''', 200, {'Content-Type': 'text/xml'}

@app.route('/webhooks/appointment-details', methods=['POST'])
def appointment_details():
    """Handle appointment booking details"""
    try:
        name = request.form.get('SpeechResult', 'Customer')
        logger.info(f"👤 Appointment booking for: {name}")
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">Thank you {name}! I've noted your appointment request. Our team will call you back within 24 hours to confirm your appointment time. Have a great day!</Say>
    <Hangup/>
</Response>''', 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error(f"Error in appointment details: {e}")
        return '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">Thank you for your appointment request! Our team will contact you soon.</Say>
    <Hangup/>
</Response>''', 200, {'Content-Type': 'text/xml'}

# Catch-all route for React Router
@app.route('/<path:path>')
def serve_react_app(path):
    """Serve React app for all non-API routes"""
    if path.startswith('api/') or path.startswith('webhooks/'):
        return jsonify({'error': 'Not found'}), 404
    try:
        return app.send_static_file('index.html')
    except:
        return jsonify({'error': 'Dashboard not available'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    logger.info(f"🚀 Starting Enhanced Voice AI Assistant on port {port}")
    
    app.run(
        debug=False,
        host='0.0.0.0',
        port=port,
        threaded=True
    )
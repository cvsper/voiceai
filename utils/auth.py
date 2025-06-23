from functools import wraps
from flask import request, jsonify, current_app
import base64

def require_auth(f):
    """Decorator for basic HTTP authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated_function

def check_auth(username, password):
    """Check if username/password combination is valid"""
    return (username == current_app.config['AUTH_USERNAME'] and 
            password == current_app.config['AUTH_PASSWORD'])

def authenticate():
    """Send 401 response with authentication challenge"""
    return jsonify({
        'error': 'Authentication required',
        'message': 'Please provide valid credentials'
    }), 401, {'WWW-Authenticate': 'Basic realm="VoiceAI API"'}

def require_api_key(f):
    """Decorator for API key authentication (alternative to basic auth)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or not validate_api_key(api_key):
            return jsonify({
                'error': 'Invalid API key',
                'message': 'Please provide a valid API key in X-API-Key header'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def validate_api_key(api_key):
    """Validate API key - implement your own logic here"""
    # For MVP, using a simple key comparison
    # In production, store API keys in database with proper hashing
    valid_keys = [
        current_app.config.get('API_KEY', 'your-secret-api-key-here')
    ]
    return api_key in valid_keys
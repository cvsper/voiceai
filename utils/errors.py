import logging
from flask import jsonify, current_app
from functools import wraps

logger = logging.getLogger(__name__)

class VoiceAIError(Exception):
    """Base exception class for VoiceAI application"""
    def __init__(self, message, status_code=500, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        result = {'error': self.message}
        if self.payload:
            result.update(self.payload)
        return result

class TwilioError(VoiceAIError):
    """Twilio-specific errors"""
    def __init__(self, message, status_code=503):
        super().__init__(message, status_code)

class DeepgramError(VoiceAIError):
    """Deepgram-specific errors"""
    def __init__(self, message, status_code=503):
        super().__init__(message, status_code)

class OpenAIError(VoiceAIError):
    """OpenAI-specific errors"""
    def __init__(self, message, status_code=503):
        super().__init__(message, status_code)

class CalendarError(VoiceAIError):
    """Calendar-specific errors"""
    def __init__(self, message, status_code=503):
        super().__init__(message, status_code)

class CRMError(VoiceAIError):
    """CRM-specific errors"""
    def __init__(self, message, status_code=503):
        super().__init__(message, status_code)

def handle_errors(app):
    """Register error handlers with Flask app"""
    
    @app.errorhandler(VoiceAIError)
    def handle_voiceai_error(error):
        logger.error(f"VoiceAI Error: {error.message}")
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({
            'error': 'Not found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        return jsonify({
            'error': 'Method not allowed',
            'message': 'The method is not allowed for the requested URL'
        }), 405
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        return jsonify({
            'error': 'Bad request',
            'message': 'The request could not be understood by the server'
        }), 400
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        logger.error(f"Internal Server Error: {error}")
        if current_app.debug:
            return jsonify({
                'error': 'Internal server error',
                'message': str(error)
            }), 500
        else:
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred'
            }), 500

def safe_execute(func, error_class=VoiceAIError, default_message="An error occurred"):
    """Decorator to safely execute functions and handle exceptions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except error_class as e:
            raise e
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise error_class(f"{default_message}: {str(e)}")
    return wrapper

def validate_request_data(required_fields=None, optional_fields=None):
    """Decorator to validate JSON request data"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request
            
            if not request.is_json:
                raise VoiceAIError("Request must be JSON", 400)
            
            data = request.get_json()
            if not data:
                raise VoiceAIError("Request body cannot be empty", 400)
            
            # Check required fields
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    raise VoiceAIError(
                        f"Missing required fields: {', '.join(missing_fields)}", 
                        400
                    )
            
            # Filter allowed fields
            if optional_fields is not None:
                allowed_fields = (required_fields or []) + optional_fields
                filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
                request._validated_json = filtered_data
            else:
                request._validated_json = data
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def log_api_call(func):
    """Decorator to log API calls for monitoring"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        from flask import request
        
        start_time = logger.time()
        
        try:
            result = func(*args, **kwargs)
            duration = logger.time() - start_time
            
            logger.info(f"API Call: {request.method} {request.path} - "
                       f"Status: Success - Duration: {duration:.3f}s")
            
            return result
            
        except Exception as e:
            duration = logger.time() - start_time
            
            logger.error(f"API Call: {request.method} {request.path} - "
                        f"Status: Error - Duration: {duration:.3f}s - Error: {str(e)}")
            
            raise
    
    return wrapper
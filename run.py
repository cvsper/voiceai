#!/usr/bin/env python3
"""
Production-ready entry point for the Voice AI Assistant
"""

from app import create_app
from utils.errors import handle_errors
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_production_app():
    """Create and configure the Flask app for production"""
    app = create_app()
    
    # Register error handlers
    handle_errors(app)
    
    # Production-specific configurations
    if not app.debug:
        # Disable Flask's debug mode in production
        app.config['DEBUG'] = False
        
        # Set up proper logging
        if not app.logger.handlers:
            file_handler = logging.FileHandler('voiceai.log')
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            app.logger.addHandler(file_handler)
    
    return app

# Create the application instance
application = create_production_app()
app = application  # For compatibility with different WSGI servers

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
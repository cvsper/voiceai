from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Stream
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class TwilioService:
    def __init__(self):
        self.client = None
    
    def initialize(self, account_sid, auth_token):
        """Initialize Twilio client"""
        self.client = Client(account_sid, auth_token)
    
    def create_call_response(self, call_sid, websocket_url):
        """Create TwiML response to start media streaming"""
        response = VoiceResponse()
        
        # Greet the caller
        response.say("Hello! Welcome to our AI assistant. I'm connecting you now.", voice='alice')
        
        # Start media stream
        stream = Stream(url=websocket_url)
        response.append(stream)
        
        # Keep the call active for up to 5 minutes  
        response.pause(length=300)
        
        return str(response)
    
    def make_test_call(self, to_number, from_number, webhook_url):
        """Make a test call"""
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=from_number,
                url=webhook_url,
                method='POST'
            )
            return {"success": True, "call_sid": call.sid}
        except Exception as e:
            logger.error(f"Error making test call: {e}")
            return {"success": False, "error": str(e)}
    
    def get_call_details(self, call_sid):
        """Get call details from Twilio"""
        try:
            call = self.client.calls(call_sid).fetch()
            return {
                "sid": call.sid,
                "from": call.from_,
                "to": call.to,
                "status": call.status,
                "start_time": call.start_time,
                "end_time": call.end_time,
                "duration": call.duration,
                "price": call.price,
                "direction": call.direction
            }
        except Exception as e:
            logger.error(f"Error fetching call details: {e}")
            return None
    
    def get_call_recordings(self, call_sid):
        """Get recordings for a call"""
        try:
            recordings = self.client.recordings.list(call_sid=call_sid)
            return [
                {
                    "sid": rec.sid,
                    "uri": rec.uri,
                    "duration": rec.duration,
                    "date_created": rec.date_created
                }
                for rec in recordings
            ]
        except Exception as e:
            logger.error(f"Error fetching recordings: {e}")
            return []

# Global Twilio service instance
twilio_service = TwilioService()
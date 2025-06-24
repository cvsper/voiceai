from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
import pytz
import logging
from flask import current_app

logger = logging.getLogger(__name__)

class CalendarService:
    def __init__(self):
        self.service = None
        self.calendar_id = 'primary'  # Can be configured
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Calendar service"""
        try:
            # For service account authentication (recommended for server-to-server)
            # You'll need to create a service account and download the JSON key
            # For now, using OAuth2 flow credentials
            
            # This is a simplified version - you'll need to implement proper OAuth2 flow
            # or use service account credentials
            creds = None
            
            # If you have service account credentials file
            # creds = service_account.Credentials.from_service_account_file(
            #     'path/to/service-account.json',
            #     scopes=['https://www.googleapis.com/auth/calendar']
            # )
            
            # For OAuth2 (requires user consent flow)
            # This is a placeholder - implement proper OAuth2 flow
            
            self.service = build('calendar', 'v3', credentials=creds)
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar service: {e}")
            # Don't raise here - let the app continue without calendar functionality
    
    def create_appointment(self, appointment_data):
        """Create an appointment in Google Calendar"""
        try:
            if not self.service:
                logger.error("Calendar service not initialized")
                return None
            
            # Parse appointment data
            start_time = datetime.fromisoformat(appointment_data['start_time'])
            end_time = datetime.fromisoformat(appointment_data['end_time'])
            
            # Convert to RFC3339 format with timezone
            timezone = pytz.timezone('UTC')  # Configure your timezone
            start_time = timezone.localize(start_time) if start_time.tzinfo is None else start_time
            end_time = timezone.localize(end_time) if end_time.tzinfo is None else end_time
            
            event = {
                'summary': appointment_data.get('title', 'Appointment'),
                'description': appointment_data.get('description', ''),
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': str(timezone),
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': str(timezone),
                },
                'attendees': [],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 24 hours
                        {'method': 'popup', 'minutes': 10},
                    ],
                },
            }
            
            # Add attendee if email provided
            if appointment_data.get('attendee_email'):
                event['attendees'].append({
                    'email': appointment_data['attendee_email']
                })
            
            # Create the event
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            logger.info(f"Appointment created: {created_event['id']}")
            
            return {
                'event_id': created_event['id'],
                'event_link': created_event.get('htmlLink'),
                'status': 'created'
            }
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            return None
    
    def get_available_slots(self, date, duration_minutes=30):
        """Get available time slots for a given date"""
        try:
            if not self.service:
                return []
            
            # Define business hours (9 AM to 5 PM)
            start_time = datetime.combine(date, datetime.min.time().replace(hour=9))
            end_time = datetime.combine(date, datetime.min.time().replace(hour=17))
            
            timezone = pytz.timezone('UTC')
            start_time = timezone.localize(start_time)
            end_time = timezone.localize(end_time)
            
            # Get existing events for the day
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Find available slots
            available_slots = []
            current_time = start_time
            
            for event in events:
                event_start = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
                event_end = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))
                
                # Check if there's a gap before this event
                if (event_start - current_time).total_seconds() >= duration_minutes * 60:
                    available_slots.append({
                        'start': current_time.isoformat(),
                        'end': event_start.isoformat(),
                        'duration': int((event_start - current_time).total_seconds() / 60)
                    })
                
                current_time = max(current_time, event_end)
            
            # Check if there's time after the last event
            if (end_time - current_time).total_seconds() >= duration_minutes * 60:
                available_slots.append({
                    'start': current_time.isoformat(),
                    'end': end_time.isoformat(),
                    'duration': int((end_time - current_time).total_seconds() / 60)
                })
            
            return available_slots
            
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            return []
    
    def cancel_appointment(self, event_id):
        """Cancel an appointment"""
        try:
            if not self.service:
                return False
            
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"Appointment cancelled: {event_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Error cancelling appointment: {e}")
            return False
        except Exception as e:
            logger.error(f"Error cancelling appointment: {e}")
            return False
    
    def reschedule_appointment(self, event_id, new_start_time, new_end_time):
        """Reschedule an existing appointment"""
        try:
            if not self.service:
                return None
            
            # Get the existing event
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # Update the times
            timezone = pytz.timezone('UTC')
            start_time = timezone.localize(new_start_time) if new_start_time.tzinfo is None else new_start_time
            end_time = timezone.localize(new_end_time) if new_end_time.tzinfo is None else new_end_time
            
            event['start']['dateTime'] = start_time.isoformat()
            event['end']['dateTime'] = end_time.isoformat()
            
            # Update the event
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            logger.info(f"Appointment rescheduled: {event_id}")
            
            return {
                'event_id': updated_event['id'],
                'event_link': updated_event.get('htmlLink'),
                'status': 'rescheduled'
            }
            
        except Exception as e:
            logger.error(f"Error rescheduling appointment: {e}")
            return None
    
    def get_appointment_details(self, event_id):
        """Get details of a specific appointment"""
        try:
            if not self.service:
                return None
            
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            return {
                'id': event['id'],
                'title': event.get('summary', ''),
                'description': event.get('description', ''),
                'start_time': event['start']['dateTime'],
                'end_time': event['end']['dateTime'],
                'attendees': [attendee['email'] for attendee in event.get('attendees', [])],
                'status': event.get('status', ''),
                'html_link': event.get('htmlLink', '')
            }
            
        except Exception as e:
            logger.error(f"Error getting appointment details: {e}")
            return None
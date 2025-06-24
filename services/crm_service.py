import requests
import json
import logging
from datetime import datetime
from flask import current_app
from models import CRMWebhook, db

logger = logging.getLogger(__name__)

class CRMService:
    def __init__(self):
        self.default_timeout = 30
    
    def trigger_webhook(self, webhook_url, payload, call_id=None):
        """Trigger a CRM webhook with the provided payload"""
        try:
            # Prepare the webhook record
            webhook_record = CRMWebhook(
                call_id=call_id,
                webhook_url=webhook_url
            )
            webhook_record.set_payload(payload)
            
            # Make the webhook request
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'VoiceAI-Webhook/1.0'
            }
            
            response = requests.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=self.default_timeout
            )
            
            # Record the response
            webhook_record.response_status = response.status_code
            webhook_record.response_body = response.text[:1000]  # Limit response body size
            
            # Save to database
            db.session.add(webhook_record)
            db.session.commit()
            
            logger.info(f"Webhook triggered successfully: {webhook_url} - Status: {response.status_code}")
            
            return {
                'success': True,
                'status_code': response.status_code,
                'webhook_id': webhook_record.id,
                'response': response.text[:500]  # Truncated response
            }
            
        except requests.exceptions.Timeout:
            logger.error(f"Webhook timeout: {webhook_url}")
            webhook_record.response_status = 408
            webhook_record.response_body = "Request timeout"
            db.session.add(webhook_record)
            db.session.commit()
            
            return {
                'success': False,
                'error': 'timeout',
                'webhook_id': webhook_record.id
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Webhook request failed: {webhook_url} - {e}")
            webhook_record.response_status = 0
            webhook_record.response_body = str(e)
            db.session.add(webhook_record)
            db.session.commit()
            
            return {
                'success': False,
                'error': str(e),
                'webhook_id': webhook_record.id
            }
            
        except Exception as e:
            logger.error(f"Unexpected error triggering webhook: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def trigger_call_started(self, call_data):
        """Trigger webhook when a call starts"""
        payload = {
            'event': 'call_started',
            'timestamp': datetime.utcnow().isoformat(),
            'call_sid': call_data.get('call_sid'),
            'from_number': call_data.get('from_number'),
            'to_number': call_data.get('to_number'),
            'call_type': call_data.get('call_type', 'inbound')
        }
        
        # Get webhook URL from configuration or database
        webhook_url = self._get_webhook_url('call_started')
        if webhook_url:
            return self.trigger_webhook(webhook_url, payload, call_data.get('call_id'))
        
        return {'success': False, 'error': 'No webhook URL configured'}
    
    def trigger_call_ended(self, call_data, transcript_summary=None):
        """Trigger webhook when a call ends"""
        payload = {
            'event': 'call_ended',
            'timestamp': datetime.utcnow().isoformat(),
            'call_sid': call_data.get('call_sid'),
            'from_number': call_data.get('from_number'),
            'to_number': call_data.get('to_number'),
            'duration': call_data.get('duration'),
            'status': call_data.get('status'),
            'transcript_summary': transcript_summary
        }
        
        webhook_url = self._get_webhook_url('call_ended')
        if webhook_url:
            return self.trigger_webhook(webhook_url, payload, call_data.get('call_id'))
        
        return {'success': False, 'error': 'No webhook URL configured'}
    
    def trigger_appointment_booked(self, appointment_data, call_data=None):
        """Trigger webhook when an appointment is booked"""
        payload = {
            'event': 'appointment_booked',
            'timestamp': datetime.utcnow().isoformat(),
            'appointment': {
                'id': appointment_data.get('id'),
                'title': appointment_data.get('title'),
                'start_time': appointment_data.get('start_time'),
                'end_time': appointment_data.get('end_time'),
                'attendee_email': appointment_data.get('attendee_email'),
                'attendee_phone': appointment_data.get('attendee_phone'),
                'google_event_id': appointment_data.get('google_event_id')
            }
        }
        
        if call_data:
            payload['call_data'] = {
                'call_sid': call_data.get('call_sid'),
                'from_number': call_data.get('from_number')
            }
        
        webhook_url = self._get_webhook_url('appointment_booked')
        if webhook_url:
            return self.trigger_webhook(webhook_url, payload, call_data.get('call_id') if call_data else None)
        
        return {'success': False, 'error': 'No webhook URL configured'}
    
    def trigger_intent_detected(self, intent_data, call_data):
        """Trigger webhook when a high-confidence intent is detected"""
        payload = {
            'event': 'intent_detected',
            'timestamp': datetime.utcnow().isoformat(),
            'intent': intent_data.get('intent'),
            'confidence': intent_data.get('confidence'),
            'entities': intent_data.get('entities', []),
            'user_input': intent_data.get('user_input'),
            'call_data': {
                'call_sid': call_data.get('call_sid'),
                'from_number': call_data.get('from_number')
            }
        }
        
        webhook_url = self._get_webhook_url('intent_detected')
        if webhook_url:
            return self.trigger_webhook(webhook_url, payload, call_data.get('call_id'))
        
        return {'success': False, 'error': 'No webhook URL configured'}
    
    def trigger_custom_event(self, event_name, custom_data, call_id=None):
        """Trigger a custom webhook event"""
        payload = {
            'event': event_name,
            'timestamp': datetime.utcnow().isoformat(),
            'data': custom_data
        }
        
        webhook_url = self._get_webhook_url(event_name)
        if webhook_url:
            return self.trigger_webhook(webhook_url, payload, call_id)
        
        return {'success': False, 'error': 'No webhook URL configured'}
    
    def _get_webhook_url(self, event_type):
        """Get webhook URL for a specific event type"""
        # This is a simplified version - in production, you might want to
        # store webhook URLs in the database or configuration
        
        webhook_urls = {
            'call_started': 'https://your-crm.com/webhooks/call-started',
            'call_ended': 'https://your-crm.com/webhooks/call-ended',
            'appointment_booked': 'https://your-crm.com/webhooks/appointment-booked',
            'intent_detected': 'https://your-crm.com/webhooks/intent-detected'
        }
        
        return webhook_urls.get(event_type)
    
    def retry_failed_webhook(self, webhook_id):
        """Retry a failed webhook"""
        try:
            webhook_record = CRMWebhook.query.get(webhook_id)
            if not webhook_record:
                return {'success': False, 'error': 'Webhook record not found'}
            
            # Retry the webhook
            payload = webhook_record.get_payload()
            result = self.trigger_webhook(
                webhook_record.webhook_url,
                payload,
                webhook_record.call_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrying webhook {webhook_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_webhook_logs(self, call_id=None, limit=100):
        """Get webhook logs, optionally filtered by call_id"""
        try:
            query = CRMWebhook.query
            
            if call_id:
                query = query.filter_by(call_id=call_id)
            
            webhooks = query.order_by(CRMWebhook.triggered_at.desc()).limit(limit).all()
            
            return [webhook.to_dict() for webhook in webhooks]
            
        except Exception as e:
            logger.error(f"Error getting webhook logs: {e}")
            return []
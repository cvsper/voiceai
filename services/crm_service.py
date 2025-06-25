import requests
import json
import logging
from flask import current_app
from models import db, WebhookLog

logger = logging.getLogger(__name__)

def send_crm_webhook(event_type, data, call_id=None):
    """Send webhook to CRM system"""
    webhook_url = current_app.config.get('CRM_WEBHOOK_URL')
    
    if not webhook_url:
        logger.warning("CRM_WEBHOOK_URL not configured, skipping webhook")
        return {"success": False, "message": "CRM webhook not configured"}
    
    # Create webhook log entry
    webhook_log = WebhookLog(
        call_id=call_id,
        event_type=event_type
    )
    webhook_log.set_payload(data)
    
    try:
        # Prepare payload
        payload = {
            "event_type": event_type,
            "timestamp": data.get('timestamp') or None,
            "call_id": call_id,
            "data": data
        }
        
        # Send webhook
        response = requests.post(
            webhook_url,
            json=payload,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'VoiceAI-Webhook/1.0'
            },
            timeout=10
        )
        
        # Log response
        webhook_log.response_status = response.status_code
        webhook_log.response_body = response.text[:1000]  # Limit response body length
        
        if response.status_code >= 200 and response.status_code < 300:
            logger.info(f"CRM webhook sent successfully: {event_type}")
            db.session.add(webhook_log)
            db.session.commit()
            return {"success": True, "status_code": response.status_code}
        else:
            logger.error(f"CRM webhook failed with status {response.status_code}: {response.text}")
            webhook_log.error_message = f"HTTP {response.status_code}: {response.text}"
            db.session.add(webhook_log)
            db.session.commit()
            return {"success": False, "status_code": response.status_code, "error": response.text}
            
    except requests.exceptions.Timeout:
        error_msg = "CRM webhook timed out"
        logger.error(error_msg)
        webhook_log.error_message = error_msg
        db.session.add(webhook_log)
        db.session.commit()
        return {"success": False, "error": error_msg}
        
    except requests.exceptions.RequestException as e:
        error_msg = f"CRM webhook request failed: {str(e)}"
        logger.error(error_msg)
        webhook_log.error_message = error_msg
        db.session.add(webhook_log)
        db.session.commit()
        return {"success": False, "error": error_msg}
        
    except Exception as e:
        error_msg = f"Unexpected error sending CRM webhook: {str(e)}"
        logger.error(error_msg)
        webhook_log.error_message = error_msg
        db.session.add(webhook_log)
        db.session.commit()
        return {"success": False, "error": error_msg}

def test_crm_webhook():
    """Test CRM webhook connectivity"""
    test_data = {
        "test": True,
        "message": "Testing CRM webhook connectivity"
    }
    
    return send_crm_webhook("test", test_data)
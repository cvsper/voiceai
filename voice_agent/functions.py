import uuid
from datetime import datetime, date, time
from models import db, Appointment, WebhookLog
from services.crm_service import send_crm_webhook
import logging

logger = logging.getLogger(__name__)

def book_appointment(customer_name, customer_phone, appointment_date, appointment_time, service_type=None, call_id=None):
    """Book an appointment and return confirmation details"""
    try:
        # Parse date and time
        appt_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        appt_time = datetime.strptime(appointment_time, '%H:%M').time()
        
        # Check if slot is available (simple check - no overlapping appointments)
        existing = Appointment.query.filter_by(
            appointment_date=appt_date,
            appointment_time=appt_time,
            status='scheduled'
        ).first()
        
        if existing:
            return {
                "success": False,
                "message": f"Sorry, {appointment_time} on {appointment_date} is already booked. Please choose a different time."
            }
        
        # Generate reference ID
        reference_id = f"APT-{uuid.uuid4().hex[:8].upper()}"
        
        # Create appointment
        appointment = Appointment(
            call_id=call_id,
            reference_id=reference_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            service_type=service_type,
            appointment_date=appt_date,
            appointment_time=appt_time,
            status='scheduled'
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        # Trigger CRM webhook
        try:
            crm_data = {
                "event": "appointment_booked",
                "appointment_id": reference_id,
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "service_type": service_type,
                "appointment_date": appointment_date,
                "appointment_time": appointment_time
            }
            send_crm_webhook("appointment", crm_data, call_id)
        except Exception as e:
            logger.error(f"CRM webhook failed: {e}")
        
        return {
            "success": True,
            "message": f"Perfect! I've booked your appointment for {appointment_time} on {appointment_date}. Your reference number is {reference_id}.",
            "reference_id": reference_id,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time
        }
        
    except Exception as e:
        logger.error(f"Error booking appointment: {e}")
        return {
            "success": False,
            "message": "I'm sorry, there was an error booking your appointment. Please try again or call back later."
        }

def get_availability(date, call_id=None):
    """Get available appointment slots for a given date"""
    try:
        appt_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Get existing appointments for the date
        existing_appointments = Appointment.query.filter_by(
            appointment_date=appt_date,
            status='scheduled'
        ).all()
        
        # Define business hours (9 AM to 5 PM)
        business_hours = [
            "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
            "12:00", "12:30", "13:00", "13:30", "14:00", "14:30",
            "15:00", "15:30", "16:00", "16:30"
        ]
        
        # Remove booked slots
        booked_times = [appt.appointment_time.strftime('%H:%M') for appt in existing_appointments]
        available_times = [t for t in business_hours if t not in booked_times]
        
        if available_times:
            available_str = ", ".join(available_times[:6])  # Show first 6 slots
            if len(available_times) > 6:
                available_str += f" and {len(available_times) - 6} more slots"
            
            return {
                "success": True,
                "message": f"Available times on {date}: {available_str}",
                "available_slots": available_times
            }
        else:
            return {
                "success": False,
                "message": f"I'm sorry, we're fully booked on {date}. Would you like to try a different date?"
            }
            
    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        return {
            "success": False,
            "message": "I'm sorry, I couldn't check availability right now. Please try again."
        }

def cancel_appointment(reference_id, call_id=None):
    """Cancel an appointment by reference ID"""
    try:
        appointment = Appointment.query.filter_by(reference_id=reference_id).first()
        
        if not appointment:
            return {
                "success": False,
                "message": f"I couldn't find an appointment with reference {reference_id}. Please check the reference number."
            }
        
        if appointment.status == 'cancelled':
            return {
                "success": False,
                "message": f"Appointment {reference_id} is already cancelled."
            }
        
        # Cancel the appointment
        appointment.status = 'cancelled'
        appointment.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Trigger CRM webhook
        try:
            crm_data = {
                "event": "appointment_cancelled",
                "appointment_id": reference_id,
                "customer_name": appointment.customer_name,
                "customer_phone": appointment.customer_phone,
                "appointment_date": appointment.appointment_date.isoformat(),
                "appointment_time": appointment.appointment_time.isoformat()
            }
            send_crm_webhook("appointment", crm_data, call_id)
        except Exception as e:
            logger.error(f"CRM webhook failed: {e}")
        
        return {
            "success": True,
            "message": f"I've successfully cancelled appointment {reference_id} for {appointment.customer_name}."
        }
        
    except Exception as e:
        logger.error(f"Error cancelling appointment: {e}")
        return {
            "success": False,
            "message": "I'm sorry, there was an error cancelling the appointment. Please try again."
        }

def trigger_crm_webhook(event_type, data, call_id=None):
    """Trigger a CRM webhook with custom data"""
    try:
        result = send_crm_webhook(event_type, data, call_id)
        
        if result.get('success'):
            return {
                "success": True,
                "message": "Information has been sent to our system successfully."
            }
        else:
            return {
                "success": False,
                "message": "There was an issue sending the information. We'll follow up manually."
            }
            
    except Exception as e:
        logger.error(f"Error triggering CRM webhook: {e}")
        return {
            "success": False,
            "message": "There was an issue sending the information. We'll follow up manually."
        }
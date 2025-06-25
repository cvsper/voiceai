from flask import Blueprint, request, jsonify
from models import db, Appointment
from sqlalchemy import desc, func
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)

appointments_bp = Blueprint('appointments', __name__)

@appointments_bp.route('/api/appointments', methods=['GET'])
def get_appointments():
    """Get paginated list of appointments"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', None)
        date_filter = request.args.get('date', None)
        
        # Build query
        query = Appointment.query
        
        if status:
            query = query.filter(Appointment.status == status)
        
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                query = query.filter(Appointment.appointment_date == filter_date)
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Paginate
        appointments = query.order_by(
            Appointment.appointment_date.desc(),
            Appointment.appointment_time.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        # Format response
        appointments_data = [appt.to_dict() for appt in appointments.items]
        
        return jsonify({
            'appointments': appointments_data,
            'pagination': {
                'page': appointments.page,
                'per_page': appointments.per_page,
                'total': appointments.total,
                'pages': appointments.pages,
                'has_next': appointments.has_next,
                'has_prev': appointments.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching appointments: {e}")
        return jsonify({'error': 'Failed to fetch appointments'}), 500

@appointments_bp.route('/api/appointments/<int:appointment_id>', methods=['GET'])
def get_appointment(appointment_id):
    """Get specific appointment"""
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        appointment_data = appointment.to_dict()
        
        # Add call information if available
        if appointment.call:
            appointment_data['call'] = appointment.call.to_dict()
        
        return jsonify(appointment_data)
        
    except Exception as e:
        logger.error(f"Error fetching appointment {appointment_id}: {e}")
        return jsonify({'error': 'Failed to fetch appointment'}), 500

@appointments_bp.route('/api/appointments/<int:appointment_id>', methods=['PUT'])
def update_appointment(appointment_id):
    """Update appointment status or details"""
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        data = request.get_json()
        
        # Update allowed fields
        if 'status' in data:
            if data['status'] in ['scheduled', 'confirmed', 'cancelled', 'completed']:
                appointment.status = data['status']
            else:
                return jsonify({'error': 'Invalid status'}), 400
        
        if 'notes' in data:
            appointment.notes = data['notes']
        
        if 'service_type' in data:
            appointment.service_type = data['service_type']
        
        appointment.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(appointment.to_dict())
        
    except Exception as e:
        logger.error(f"Error updating appointment {appointment_id}: {e}")
        return jsonify({'error': 'Failed to update appointment'}), 500

@appointments_bp.route('/api/appointments/<int:appointment_id>', methods=['DELETE'])
def delete_appointment(appointment_id):
    """Delete appointment"""
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        db.session.delete(appointment)
        db.session.commit()
        
        return jsonify({'message': 'Appointment deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting appointment {appointment_id}: {e}")
        return jsonify({'error': 'Failed to delete appointment'}), 500

@appointments_bp.route('/api/appointments/stats', methods=['GET'])
def get_appointment_stats():
    """Get appointment statistics"""
    try:
        today = date.today()
        
        # Total appointments
        total = Appointment.query.count()
        
        # By status
        stats = db.session.query(
            Appointment.status,
            func.count(Appointment.id)
        ).group_by(Appointment.status).all()
        
        status_counts = {status: count for status, count in stats}
        
        # Today's appointments
        today_appointments = Appointment.query.filter(
            Appointment.appointment_date == today
        ).count()
        
        # This week's appointments
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        week_appointments = Appointment.query.filter(
            Appointment.appointment_date >= week_start,
            Appointment.appointment_date <= week_end
        ).count()
        
        # Most popular services
        service_stats = db.session.query(
            Appointment.service_type,
            func.count(Appointment.id)
        ).filter(Appointment.service_type.isnot(None)).group_by(
            Appointment.service_type
        ).order_by(func.count(Appointment.id).desc()).limit(5).all()
        
        return jsonify({
            'total_appointments': total,
            'status_breakdown': status_counts,
            'today_appointments': today_appointments,
            'week_appointments': week_appointments,
            'popular_services': [
                {'service': service, 'count': count} 
                for service, count in service_stats
            ]
        })
        
    except Exception as e:
        logger.error(f"Error fetching appointment stats: {e}")
        return jsonify({'error': 'Failed to fetch appointment statistics'}), 500

@appointments_bp.route('/api/appointments/availability/<date_str>', methods=['GET'])
def check_availability(date_str):
    """Check availability for a specific date"""
    try:
        # Parse date
        check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get existing appointments for the date
        existing_appointments = Appointment.query.filter_by(
            appointment_date=check_date,
            status='scheduled'
        ).all()
        
        # Define business hours (9 AM to 5 PM, 30-minute slots)
        business_hours = []
        for hour in range(9, 17):
            for minute in [0, 30]:
                business_hours.append(f"{hour:02d}:{minute:02d}")
        
        # Remove booked slots
        booked_times = [appt.appointment_time.strftime('%H:%M') for appt in existing_appointments]
        available_times = [t for t in business_hours if t not in booked_times]
        
        return jsonify({
            'date': date_str,
            'available_slots': available_times,
            'booked_slots': booked_times,
            'total_available': len(available_times),
            'total_booked': len(booked_times)
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        logger.error(f"Error checking availability for {date_str}: {e}")
        return jsonify({'error': 'Failed to check availability'}), 500
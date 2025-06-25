from flask import Blueprint, request, jsonify
from models import db, Call, Appointment, Transcript, WebhookLog
from sqlalchemy import func, desc
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/api/dashboard/metrics', methods=['GET'])
def get_dashboard_metrics():
    """Get real-time dashboard metrics"""
    try:
        # Date ranges
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        # Call metrics
        total_calls = Call.query.count()
        today_calls = Call.query.filter(func.date(Call.created_at) == today).count()
        week_calls = Call.query.filter(func.date(Call.created_at) >= week_start).count()
        month_calls = Call.query.filter(func.date(Call.created_at) >= month_start).count()
        
        # Call status breakdown
        call_status_stats = db.session.query(
            Call.status,
            func.count(Call.id)
        ).group_by(Call.status).all()
        
        call_status_counts = {status: count for status, count in call_status_stats}
        
        # Average call duration
        avg_duration = db.session.query(
            func.avg(Call.duration)
        ).filter(Call.duration.isnot(None)).scalar()
        
        # Appointment metrics
        total_appointments = Appointment.query.count()
        today_appointments = Appointment.query.filter(
            Appointment.appointment_date == today
        ).count()
        
        # Appointment status breakdown
        appt_status_stats = db.session.query(
            Appointment.status,
            func.count(Appointment.id)
        ).group_by(Appointment.status).all()
        
        appt_status_counts = {status: count for status, count in appt_status_stats}
        
        # Recent activity
        recent_calls = Call.query.order_by(desc(Call.created_at)).limit(5).all()
        recent_appointments = Appointment.query.order_by(desc(Appointment.created_at)).limit(5).all()
        
        # Conversion rate (appointments booked per call)
        conversion_rate = 0
        if total_calls > 0:
            calls_with_appointments = db.session.query(Call.id).join(Appointment).distinct().count()
            conversion_rate = (calls_with_appointments / total_calls) * 100
        
        # Top services
        top_services = db.session.query(
            Appointment.service_type,
            func.count(Appointment.id)
        ).filter(Appointment.service_type.isnot(None)).group_by(
            Appointment.service_type
        ).order_by(func.count(Appointment.id).desc()).limit(5).all()
        
        # Webhook success rate
        total_webhooks = WebhookLog.query.count()
        successful_webhooks = WebhookLog.query.filter(
            WebhookLog.response_status >= 200,
            WebhookLog.response_status < 300
        ).count()
        
        webhook_success_rate = 0
        if total_webhooks > 0:
            webhook_success_rate = (successful_webhooks / total_webhooks) * 100
        
        return jsonify({
            'call_metrics': {
                'total_calls': total_calls,
                'today_calls': today_calls,
                'week_calls': week_calls,
                'month_calls': month_calls,
                'status_breakdown': call_status_counts,
                'average_duration': round(avg_duration or 0, 2)
            },
            'appointment_metrics': {
                'total_appointments': total_appointments,
                'today_appointments': today_appointments,
                'status_breakdown': appt_status_counts,
                'conversion_rate': round(conversion_rate, 2)
            },
            'recent_activity': {
                'recent_calls': [call.to_dict() for call in recent_calls],
                'recent_appointments': [appt.to_dict() for appt in recent_appointments]
            },
            'top_services': [
                {'service': service, 'count': count} 
                for service, count in top_services
            ],
            'webhook_metrics': {
                'total_webhooks': total_webhooks,
                'successful_webhooks': successful_webhooks,
                'success_rate': round(webhook_success_rate, 2)
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching dashboard metrics: {e}")
        return jsonify({'error': 'Failed to fetch dashboard metrics'}), 500

@dashboard_bp.route('/api/dashboard/call-trends', methods=['GET'])
def get_call_trends():
    """Get call trends over time"""
    try:
        days = request.args.get('days', 7, type=int)
        
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        # Get daily call counts
        daily_calls = db.session.query(
            func.date(Call.created_at).label('date'),
            func.count(Call.id).label('count')
        ).filter(
            func.date(Call.created_at) >= start_date,
            func.date(Call.created_at) <= end_date
        ).group_by(func.date(Call.created_at)).order_by('date').all()
        
        # Fill in missing dates with zero counts
        date_range = [start_date + timedelta(days=i) for i in range(days)]
        call_counts = {str(date): 0 for date in date_range}
        
        for date_str, count in daily_calls:
            call_counts[str(date_str)] = count
        
        # Get daily appointment counts
        daily_appointments = db.session.query(
            func.date(Appointment.created_at).label('date'),
            func.count(Appointment.id).label('count')
        ).filter(
            func.date(Appointment.created_at) >= start_date,
            func.date(Appointment.created_at) <= end_date
        ).group_by(func.date(Appointment.created_at)).order_by('date').all()
        
        appointment_counts = {str(date): 0 for date in date_range}
        
        for date_str, count in daily_appointments:
            appointment_counts[str(date_str)] = count
        
        # Format response
        trends = []
        for date_str in sorted(call_counts.keys()):
            trends.append({
                'date': date_str,
                'calls': call_counts[date_str],
                'appointments': appointment_counts[date_str]
            })
        
        return jsonify({
            'trends': trends,
            'period': f"{days} days",
            'start_date': str(start_date),
            'end_date': str(end_date)
        })
        
    except Exception as e:
        logger.error(f"Error fetching call trends: {e}")
        return jsonify({'error': 'Failed to fetch call trends'}), 500

@dashboard_bp.route('/api/dashboard/live-stats', methods=['GET'])
def get_live_stats():
    """Get live statistics for real-time updates"""
    try:
        # Calls in last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_calls = Call.query.filter(Call.created_at >= one_hour_ago).count()
        
        # Active calls (in-progress)
        active_calls = Call.query.filter(Call.status == 'in-progress').count()
        
        # Appointments booked today
        today = date.today()
        today_appointments = Appointment.query.filter(
            func.date(Appointment.created_at) == today
        ).count()
        
        # Recent webhook failures
        recent_webhook_failures = WebhookLog.query.filter(
            WebhookLog.created_at >= one_hour_ago,
            WebhookLog.response_status >= 400
        ).count()
        
        # System health indicators
        total_errors = WebhookLog.query.filter(
            WebhookLog.error_message.isnot(None)
        ).count()
        
        return jsonify({
            'live_stats': {
                'recent_calls': recent_calls,
                'active_calls': active_calls,
                'today_appointments': today_appointments,
                'recent_webhook_failures': recent_webhook_failures,
                'total_errors': total_errors
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching live stats: {e}")
        return jsonify({'error': 'Failed to fetch live statistics'}), 500

@dashboard_bp.route('/api/dashboard/system-health', methods=['GET'])
def get_system_health():
    """Get system health information"""
    try:
        # Database connectivity (if we got here, DB is working)
        db_healthy = True
        
        # Recent error rate
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_errors = WebhookLog.query.filter(
            WebhookLog.created_at >= one_hour_ago,
            WebhookLog.error_message.isnot(None)
        ).count()
        
        recent_total = WebhookLog.query.filter(
            WebhookLog.created_at >= one_hour_ago
        ).count()
        
        error_rate = 0
        if recent_total > 0:
            error_rate = (recent_errors / recent_total) * 100
        
        # Service status
        health_status = "healthy"
        if error_rate > 10:
            health_status = "degraded"
        elif error_rate > 25:
            health_status = "unhealthy"
        
        return jsonify({
            'system_health': {
                'status': health_status,
                'database_healthy': db_healthy,
                'error_rate': round(error_rate, 2),
                'recent_errors': recent_errors,
                'recent_total': recent_total
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        return jsonify({'error': 'Failed to check system health'}), 500
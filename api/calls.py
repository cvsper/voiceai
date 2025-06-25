from flask import Blueprint, request, jsonify
from models import db, Call, Transcript
from sqlalchemy import desc
import logging

logger = logging.getLogger(__name__)

calls_bp = Blueprint('calls', __name__)

@calls_bp.route('/api/calls', methods=['GET'])
def get_calls():
    """Get paginated list of calls with transcripts"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', None)
        
        # Build query
        query = Call.query
        
        if status:
            query = query.filter(Call.status == status)
        
        # Paginate
        calls = query.order_by(desc(Call.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Format response
        calls_data = []
        for call in calls.items:
            call_data = call.to_dict()
            
            # Add transcript count
            transcript_count = Transcript.query.filter_by(call_id=call.id).count()
            call_data['transcript_count'] = transcript_count
            
            # Add latest transcript
            latest_transcript = Transcript.query.filter_by(call_id=call.id).order_by(desc(Transcript.timestamp)).first()
            if latest_transcript:
                call_data['latest_transcript'] = latest_transcript.to_dict()
            
            calls_data.append(call_data)
        
        return jsonify({
            'calls': calls_data,
            'pagination': {
                'page': calls.page,
                'per_page': calls.per_page,
                'total': calls.total,
                'pages': calls.pages,
                'has_next': calls.has_next,
                'has_prev': calls.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching calls: {e}")
        return jsonify({'error': 'Failed to fetch calls'}), 500

@calls_bp.route('/api/calls/<int:call_id>', methods=['GET'])
def get_call(call_id):
    """Get specific call with full transcript"""
    try:
        call = Call.query.get_or_404(call_id)
        call_data = call.to_dict()
        
        # Add transcripts
        transcripts = Transcript.query.filter_by(call_id=call_id).order_by(Transcript.timestamp).all()
        call_data['transcripts'] = [t.to_dict() for t in transcripts]
        
        # Add appointments
        call_data['appointments'] = [a.to_dict() for a in call.appointments]
        
        # Add webhook logs
        call_data['webhook_logs'] = [w.to_dict() for w in call.webhook_logs]
        
        return jsonify(call_data)
        
    except Exception as e:
        logger.error(f"Error fetching call {call_id}: {e}")
        return jsonify({'error': 'Failed to fetch call'}), 500

@calls_bp.route('/api/calls/<int:call_id>/transcript', methods=['GET'])
def get_call_transcript(call_id):
    """Get full transcript for a call"""
    try:
        call = Call.query.get_or_404(call_id)
        
        transcripts = Transcript.query.filter_by(call_id=call_id).order_by(Transcript.timestamp).all()
        
        return jsonify({
            'call_id': call_id,
            'call_sid': call.sid,
            'transcripts': [t.to_dict() for t in transcripts],
            'total_segments': len(transcripts)
        })
        
    except Exception as e:
        logger.error(f"Error fetching transcript for call {call_id}: {e}")
        return jsonify({'error': 'Failed to fetch transcript'}), 500

@calls_bp.route('/api/calls/search', methods=['GET'])
def search_calls():
    """Search calls by phone number or transcript content"""
    try:
        query = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Search by phone number
        calls_query = Call.query.filter(
            (Call.from_number.contains(query)) |
            (Call.to_number.contains(query))
        )
        
        # Also search transcript content
        transcript_call_ids = db.session.query(Transcript.call_id).filter(
            Transcript.text.contains(query)
        ).distinct().subquery()
        
        calls_query = calls_query.union(
            Call.query.filter(Call.id.in_(transcript_call_ids))
        )
        
        # Paginate
        calls = calls_query.order_by(desc(Call.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Format response
        calls_data = []
        for call in calls.items:
            call_data = call.to_dict()
            
            # Add matching transcripts
            matching_transcripts = Transcript.query.filter(
                Transcript.call_id == call.id,
                Transcript.text.contains(query)
            ).order_by(Transcript.timestamp).all()
            
            call_data['matching_transcripts'] = [t.to_dict() for t in matching_transcripts]
            calls_data.append(call_data)
        
        return jsonify({
            'calls': calls_data,
            'query': query,
            'pagination': {
                'page': calls.page,
                'per_page': calls.per_page,
                'total': calls.total,
                'pages': calls.pages,
                'has_next': calls.has_next,
                'has_prev': calls.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error searching calls: {e}")
        return jsonify({'error': 'Failed to search calls'}), 500
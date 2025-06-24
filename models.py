from quart_sqlalchemy import QuartSQLAlchemy
from datetime import datetime
import json

db = QuartSQLAlchemy()

class Call(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    call_sid = db.Column(db.String(100), unique=True, nullable=False)
    from_number = db.Column(db.String(20), nullable=False)
    to_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='initiated')
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # in seconds
    call_type = db.Column(db.String(20), default='inbound')  # inbound, outbound, conference
    recording_url = db.Column(db.String(500))
    
    # Relationships
    transcripts = db.relationship('Transcript', backref='call', lazy=True, cascade='all, delete-orphan')
    interactions = db.relationship('Interaction', backref='call', lazy=True, cascade='all, delete-orphan')
    appointments = db.relationship('Appointment', backref='call', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'call_sid': self.call_sid,
            'from_number': self.from_number,
            'to_number': self.to_number,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'call_type': self.call_type,
            'recording_url': self.recording_url,
            'transcript_count': len(self.transcripts),
            'interaction_count': len(self.interactions)
        }

class Transcript(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    call_id = db.Column(db.Integer, db.ForeignKey('call.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    speaker = db.Column(db.String(20))  # 'caller', 'agent', 'participant1', 'participant2'
    text = db.Column(db.Text, nullable=False)
    confidence = db.Column(db.Float)
    is_final = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'call_id': self.call_id,
            'timestamp': self.timestamp.isoformat(),
            'speaker': self.speaker,
            'text': self.text,
            'confidence': self.confidence,
            'is_final': self.is_final
        }

class Interaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    call_id = db.Column(db.Integer, db.ForeignKey('call.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    intent = db.Column(db.String(100))  # 'booking', 'info_request', 'complaint', etc.
    confidence = db.Column(db.Float)
    user_input = db.Column(db.Text)
    ai_response = db.Column(db.Text)
    action_taken = db.Column(db.String(100))  # 'appointment_booked', 'crm_updated', etc.
    meta_data = db.Column(db.Text)  # JSON string for additional data
    
    def get_metadata(self):
        return json.loads(self.meta_data) if self.meta_data else {}
    
    def set_metadata(self, data):
        self.meta_data = json.dumps(data)
    
    def to_dict(self):
        return {
            'id': self.id,
            'call_id': self.call_id,
            'timestamp': self.timestamp.isoformat(),
            'intent': self.intent,
            'confidence': self.confidence,
            'user_input': self.user_input,
            'ai_response': self.ai_response,
            'action_taken': self.action_taken,
            'metadata': self.get_metadata()
        }

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    call_id = db.Column(db.Integer, db.ForeignKey('call.id'), nullable=True)
    google_event_id = db.Column(db.String(255))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    attendee_email = db.Column(db.String(255))
    attendee_phone = db.Column(db.String(20))
    status = db.Column(db.String(20), default='scheduled')  # scheduled, confirmed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'call_id': self.call_id,
            'google_event_id': self.google_event_id,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'attendee_email': self.attendee_email,
            'attendee_phone': self.attendee_phone,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

class CRMWebhook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    call_id = db.Column(db.Integer, db.ForeignKey('call.id'), nullable=True)
    webhook_url = db.Column(db.String(500), nullable=False)
    payload = db.Column(db.Text)  # JSON string
    response_status = db.Column(db.Integer)
    response_body = db.Column(db.Text)
    triggered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_payload(self):
        return json.loads(self.payload) if self.payload else {}
    
    def set_payload(self, data):
        self.payload = json.dumps(data)
    
    def to_dict(self):
        return {
            'id': self.id,
            'call_id': self.call_id,
            'webhook_url': self.webhook_url,
            'payload': self.get_payload(),
            'response_status': self.response_status,
            'response_body': self.response_body,
            'triggered_at': self.triggered_at.isoformat()
        }
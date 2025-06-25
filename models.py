from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Call(db.Model):
    __tablename__ = 'calls'
    
    id = db.Column(db.Integer, primary_key=True)
    sid = db.Column(db.String(50), unique=True, nullable=False)
    from_number = db.Column(db.String(20), nullable=False)
    to_number = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # seconds
    status = db.Column(db.String(20), default='in-progress')  # in-progress, completed, failed
    recording_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    transcripts = db.relationship('Transcript', backref='call', lazy=True)
    appointments = db.relationship('Appointment', backref='call', lazy=True)
    webhook_logs = db.relationship('WebhookLog', backref='call', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sid': self.sid,
            'from_number': self.from_number,
            'to_number': self.to_number,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'status': self.status,
            'recording_url': self.recording_url,
            'created_at': self.created_at.isoformat()
        }

class Transcript(db.Model):
    __tablename__ = 'transcripts'
    
    id = db.Column(db.Integer, primary_key=True)
    call_id = db.Column(db.Integer, db.ForeignKey('calls.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    speaker = db.Column(db.String(20))  # 'caller', 'agent'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    confidence = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'call_id': self.call_id,
            'text': self.text,
            'speaker': self.speaker,
            'timestamp': self.timestamp.isoformat(),
            'confidence': self.confidence
        }

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    call_id = db.Column(db.Integer, db.ForeignKey('calls.id'), nullable=True)
    reference_id = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    service_type = db.Column(db.String(100))
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, confirmed, cancelled, completed
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'call_id': self.call_id,
            'reference_id': self.reference_id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'service_type': self.service_type,
            'appointment_date': self.appointment_date.isoformat() if self.appointment_date else None,
            'appointment_time': self.appointment_time.isoformat() if self.appointment_time else None,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class WebhookLog(db.Model):
    __tablename__ = 'webhook_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    call_id = db.Column(db.Integer, db.ForeignKey('calls.id'), nullable=True)
    event_type = db.Column(db.String(50), nullable=False)
    payload = db.Column(db.Text)  # JSON string
    response_status = db.Column(db.Integer)
    response_body = db.Column(db.Text)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_payload(self, payload_dict):
        self.payload = json.dumps(payload_dict)
    
    def get_payload(self):
        return json.loads(self.payload) if self.payload else {}
    
    def to_dict(self):
        return {
            'id': self.id,
            'call_id': self.call_id,
            'event_type': self.event_type,
            'payload': self.get_payload(),
            'response_status': self.response_status,
            'response_body': self.response_body,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat()
        }
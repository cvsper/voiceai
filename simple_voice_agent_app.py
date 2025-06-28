#!/usr/bin/env python3

from flask import Flask, request, send_from_directory, render_template_string, render_template, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
from datetime import datetime, timedelta
import os
import logging
import requests
import secrets
import json
from cryptography.fernet import Fernet
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Flask with multiple static folders and template folders
app = Flask(__name__, template_folder='admin_templates')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Initialize OAuth
oauth = OAuth(app)

# Configure Google OAuth
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Add multiple static folders for different content
@app.route('/static/<path:filename>')
def serve_dashboard_static(filename):
    """Serve dashboard static files"""
    return send_from_directory('demo3/static', filename)

@app.route('/admin_static/<path:filename>')
def serve_admin_static(filename):
    """Serve admin dashboard static files"""
    return send_from_directory('admin_static', filename)

@app.route('/assets/<path:filename>')
def serve_demo3_assets(filename):
    """Serve demo3 React app assets"""
    return send_from_directory('demo3/static/assets', filename)

@app.route('/vite.svg')
def serve_vite_svg():
    """Serve vite.svg icon"""
    # Return a simple SVG if file doesn't exist
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
  <circle cx="8" cy="8" r="6" fill="#646cff"/>
</svg>''', 200, {'Content-Type': 'image/svg+xml'}

@app.route('/css/<path:filename>')
def serve_landing_css(filename):
    """Serve landing page CSS files"""
    return send_from_directory('landing/HTML/css', filename)

@app.route('/js/<path:filename>')
def serve_landing_js(filename):
    """Serve landing page JS files"""
    return send_from_directory('landing/HTML/js', filename)

@app.route('/img/<path:filename>')
def serve_landing_img(filename):
    """Serve landing page image files"""
    return send_from_directory('landing/HTML/img', filename)

@app.route('/fonts/<path:filename>')
def serve_landing_fonts(filename):
    """Serve landing page font files"""
    return send_from_directory('landing/HTML/fonts', filename)

@app.route('/video/<path:filename>')
def serve_landing_video(filename):
    """Serve landing page video files"""
    return send_from_directory('landing/HTML/video', filename)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///voiceai_calendar.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable for Google OAuth users
    name = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)  # User's personal phone (optional)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Google OAuth
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    
    # Calendar integrations
    google_calendar_token = db.Column(db.Text, nullable=True)
    microsoft_calendar_token = db.Column(db.Text, nullable=True)
    apple_calendar_enabled = db.Column(db.Boolean, default=False)
    
    # Relationships
    twilio_numbers = db.relationship('TwilioNumber', backref='user', lazy=True)
    sms_logs = db.relationship('SMSLog', backref='user', lazy=True)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        """Return user ID as string (required by Flask-Login)"""
        return str(self.id)
    
    def is_authenticated(self):
        """Return True if user is authenticated"""
        return True
    
    def is_anonymous(self):
        """Return False as this is not an anonymous user"""
        return False

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    calendar_provider = db.Column(db.String(50), default='voiceai')  # 'google', 'microsoft', 'apple', 'voiceai'
    external_event_id = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='scheduled')  # 'scheduled', 'confirmed', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Phone call details
    call_sid = db.Column(db.String(100), nullable=True)
    scheduled_via_voice = db.Column(db.Boolean, default=False)
    phone_number = db.Column(db.String(20), nullable=True)  # Associated phone number
    event_type = db.Column(db.String(20), default='call')  # 'call', 'meeting', 'reminder', 'follow-up'
    
    user = db.relationship('User', backref=db.backref('appointments', lazy=True))

class CalendarSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    preferred_calendar = db.Column(db.String(50), nullable=False)  # 'google', 'microsoft', 'apple'
    default_appointment_duration = db.Column(db.Integer, default=30)  # minutes
    business_hours_start = db.Column(db.Time, default=datetime.strptime('09:00', '%H:%M').time())
    business_hours_end = db.Column(db.Time, default=datetime.strptime('17:00', '%H:%M').time())
    timezone = db.Column(db.String(50), default='America/New_York')
    
    user = db.relationship('User', backref=db.backref('calendar_settings', uselist=False))

class BusinessInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Basic Business Information
    business_name = db.Column(db.String(200), nullable=True)
    business_type = db.Column(db.String(100), nullable=True)
    business_description = db.Column(db.Text, nullable=True)
    
    # Contact Information
    business_phone = db.Column(db.String(20), nullable=True)
    business_email = db.Column(db.String(120), nullable=True)
    location_address = db.Column(db.Text, nullable=True)
    website_url = db.Column(db.String(500), nullable=True)
    business_hours = db.Column(db.Text, nullable=True)
    
    # Services and Pricing
    services_offered = db.Column(db.Text, nullable=True)
    pricing_info = db.Column(db.Text, nullable=True)
    payment_methods = db.Column(db.String(500), nullable=True)
    special_offers = db.Column(db.Text, nullable=True)
    
    # Appointment Information
    appointment_types = db.Column(db.Text, nullable=True)
    booking_policy = db.Column(db.Text, nullable=True)
    
    # FAQ and Communication
    common_questions = db.Column(db.Text, nullable=True)
    emergency_contact = db.Column(db.String(200), nullable=True)
    alternative_contact = db.Column(db.String(200), nullable=True)
    ai_instructions = db.Column(db.Text, nullable=True)
    
    # Legacy fields (for backward compatibility)
    contact_info = db.Column(db.Text, nullable=True)
    additional_info = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('business_info', uselist=False))

class CallLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    call_sid = db.Column(db.String(100), unique=True, nullable=False)
    from_number = db.Column(db.String(20), nullable=False)
    to_number = db.Column(db.String(20), nullable=False)
    call_status = db.Column(db.String(20), nullable=True)  # 'in-progress', 'completed', 'failed'
    call_duration = db.Column(db.Integer, nullable=True)  # seconds
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    transcript = db.Column(db.Text, nullable=True)
    audio_url = db.Column(db.String(500), nullable=True)
    recording_url = db.Column(db.String(500), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    appointment_scheduled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships to user and Twilio number
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    twilio_number_id = db.Column(db.Integer, db.ForeignKey('twilio_number.id'), nullable=True)
    user = db.relationship('User', backref='call_logs')

class ContactSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    phone2 = db.Column(db.String(20), nullable=True)
    company = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=False)
    services = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='new')  # 'new', 'contacted', 'closed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    contacted_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)

class TwilioNumber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    friendly_name = db.Column(db.String(200), nullable=True)
    sid = db.Column(db.String(100), unique=True, nullable=False)  # Twilio Phone Number SID
    capabilities = db.Column(db.JSON, nullable=True)  # voice, sms, mms capabilities
    status = db.Column(db.String(20), default='active')  # 'active', 'inactive', 'released'
    monthly_cost = db.Column(db.Float, nullable=True)
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)
    released_at = db.Column(db.DateTime, nullable=True)
    webhook_url = db.Column(db.String(500), nullable=True)
    
    # Relationships
    call_logs = db.relationship('CallLog', backref='twilio_number', lazy=True)
    sms_logs = db.relationship('SMSLog', backref='twilio_number', lazy=True)

class SMSLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    twilio_number_id = db.Column(db.Integer, db.ForeignKey('twilio_number.id'), nullable=False)
    message_sid = db.Column(db.String(100), unique=True, nullable=False)
    from_number = db.Column(db.String(20), nullable=False)
    to_number = db.Column(db.String(20), nullable=False)
    body = db.Column(db.Text, nullable=True)
    direction = db.Column(db.String(20), nullable=False)  # 'inbound', 'outbound'
    status = db.Column(db.String(20), nullable=True)  # 'received', 'sent', 'failed', etc.
    media_urls = db.Column(db.JSON, nullable=True)  # Array of media URLs for MMS
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class TwilioAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_sid = db.Column(db.String(100), nullable=False)
    auth_token_encrypted = db.Column(db.Text, nullable=False)  # Encrypted auth token
    is_primary = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('twilio_accounts', lazy=True))

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    company = db.Column(db.String(200))
    job_title = db.Column(db.String(200))
    address = db.Column(db.Text)
    notes = db.Column(db.Text)
    tags = db.Column(db.String(500))  # Comma-separated tags
    contact_group = db.Column(db.String(100))
    is_favorite = db.Column(db.Boolean, default=False)
    allow_sms = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('contacts', lazy=True))

# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Utility functions for encryption/decryption
def get_encryption_key():
    """Get or create encryption key for Twilio credentials"""
    key = os.environ.get('ENCRYPTION_KEY')
    if not key:
        key = Fernet.generate_key().decode()
        logger.warning("No ENCRYPTION_KEY found in environment. Generated new key.")
    return key.encode() if isinstance(key, str) else key

def encrypt_token(token):
    """Encrypt sensitive token"""
    f = Fernet(get_encryption_key())
    return f.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token):
    """Decrypt sensitive token"""
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted_token.encode()).decode()

# Twilio utilities
def get_twilio_client(user=None, account_sid=None, auth_token=None):
    """Get Twilio client for user or use master account"""
    if user and user.twilio_accounts:
        account = user.twilio_accounts[0]  # Use first account
        sid = account.account_sid
        token = decrypt_token(account.auth_token_encrypted)
        return Client(sid, token)
    elif account_sid and auth_token:
        return Client(account_sid, auth_token)
    else:
        # Use master Twilio account
        sid = os.environ.get('TWILIO_ACCOUNT_SID')
        token = os.environ.get('TWILIO_AUTH_TOKEN')
        if not sid or not token:
            raise ValueError("No Twilio credentials available")
        return Client(sid, token)

# Root route to serve landing page
@app.route('/')
def landing_page():
    """Serve the landing page as the main site"""
    try:
        return send_from_directory('landing/HTML', 'index.html')
    except Exception as e:
        logger.error(f"❌ Error serving landing page: {e}")
        return f"Landing page error: {str(e)}", 500

@app.route('/contact')
def contact_page():
    """Serve the contact page"""
    try:
        return send_from_directory('landing/HTML', 'contact.html')
    except Exception as e:
        logger.error(f"❌ Error serving contact page: {e}")
        return f"Contact page error: {str(e)}", 500

@app.route('/api/contact', methods=['POST'])
def handle_contact_form():
    """Handle contact form submissions"""
    try:
        # Extract form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        phone2 = request.form.get('phone2', '').strip()
        company = request.form.get('company', '').strip()
        message = request.form.get('message', '').strip()
        services = request.form.get('services', '').strip()
        
        # Validate required fields
        if not name or not email or not phone or not message:
            return jsonify({
                'success': False,
                'error': 'Please fill in all required fields (name, email, phone, message)'
            }), 400
        
        # Create contact submission
        contact = ContactSubmission(
            name=name,
            email=email,
            phone=phone,
            phone2=phone2 if phone2 else None,
            company=company if company else None,
            message=message,
            services=services if services else None
        )
        
        # Save to database
        db.session.add(contact)
        db.session.commit()
        
        logger.info(f"📝 New contact submission from {name} ({email})")
        
        return jsonify({
            'success': True,
            'message': 'Thank you! Your message has been sent successfully.'
        })
        
    except Exception as e:
        logger.error(f"❌ Error handling contact form: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Sorry, there was an error processing your request. Please try again.'
        }), 500

# Authentication Routes
@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'GET':
        return render_template_string(REGISTER_TEMPLATE)
    
    try:
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        
        # Validate input
        if not username or not email or not password:
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': 'Email already registered'}), 400
        
        # Create new user
        user = User(
            username=username,
            email=email,
            name=name,
            is_verified=True  # Auto-verify for demo
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"✅ New user registered: {username} ({email})")
        
        return jsonify({
            'success': True, 
            'message': 'Registration successful! Please log in.',
            'redirect': '/auth/login'
        })
        
    except Exception as e:
        logger.error(f"❌ Registration error: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Registration failed'}), 500

@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'GET':
        return render_template_string(LOGIN_TEMPLATE)
    
    try:
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user or not user.check_password(password):
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'success': False, 'error': 'Account disabled'}), 401
        
        # Log user in
        login_user(user, remember=True)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"✅ User logged in: {user.username}")
        
        return jsonify({
            'success': True,
            'message': 'Login successful!',
            'redirect': '/dashboard'
        })
        
    except Exception as e:
        logger.error(f"❌ Login error: {str(e)}")
        return jsonify({'success': False, 'error': 'Login failed'}), 500

@app.route('/auth/logout')
@login_required
def logout():
    """User logout"""
    logger.info(f"✅ User logged out: {current_user.username}")
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('landing_page'))

@app.route('/auth/google')
def google_auth():
    """Google OAuth login"""
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def google_callback():
    """Google OAuth callback"""
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        
        if not user_info:
            flash('Failed to get user information from Google.', 'error')
            return redirect(url_for('login'))
        
        # Check if user exists
        user = User.query.filter_by(google_id=user_info['sub']).first()
        
        if not user:
            # Check if email already exists
            existing_user = User.query.filter_by(email=user_info['email']).first()
            if existing_user:
                # Link Google account to existing user
                existing_user.google_id = user_info['sub']
                existing_user.avatar_url = user_info.get('picture')
                user = existing_user
            else:
                # Create new user
                username = user_info['email'].split('@')[0]
                # Ensure unique username
                base_username = username
                counter = 1
                while User.query.filter_by(username=username).first():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = User(
                    username=username,
                    email=user_info['email'],
                    name=user_info.get('name'),
                    google_id=user_info['sub'],
                    avatar_url=user_info.get('picture'),
                    is_verified=True
                )
                db.session.add(user)
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=True)
        logger.info(f"✅ Google OAuth login: {user.username}")
        
        flash('Successfully logged in with Google!', 'success')
        return redirect(url_for('user_dashboard'))
        
    except Exception as e:
        logger.error(f"❌ Google OAuth error: {str(e)}")
        flash('Google login failed. Please try again.', 'error')
        return redirect(url_for('login'))

# User Dashboard and Twilio Management Routes
@app.route('/dashboard')
@app.route('/dashboard/')
@app.route('/dashboard/<path:path>')
@login_required
def user_dashboard(path=None):
    """User dashboard with Twilio number management using admin template"""
    try:
        # Get user's Twilio numbers
        user_numbers = TwilioNumber.query.filter_by(
            user_id=current_user.id, 
            status='active'
        ).all()
        
        # Get recent call logs
        recent_calls = CallLog.query.filter_by(user_id=current_user.id)\
            .order_by(CallLog.created_at.desc()).limit(5).all()
        
        # Get recent SMS logs
        recent_sms = SMSLog.query.filter_by(user_id=current_user.id)\
            .order_by(SMSLog.created_at.desc()).limit(5).all()
        
        # Calculate stats
        total_calls = CallLog.query.filter_by(user_id=current_user.id).count()
        total_sms = SMSLog.query.filter_by(user_id=current_user.id).count()
        total_numbers = len(user_numbers)
        total_cost = sum(num.monthly_cost or 0 for num in user_numbers)
        
        logger.info(f"✅ User {current_user.username} accessing new admin dashboard")
        
        return render_template('voiceai_dashboard.html',
            current_user=current_user,
            user_numbers=user_numbers,
            recent_calls=recent_calls,
            recent_sms=recent_sms,
            total_numbers=total_numbers,
            total_calls=total_calls,
            total_sms=total_sms,
            total_cost=total_cost
        )
        
    except Exception as e:
        logger.error(f"❌ Dashboard error: {str(e)}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        # Return error message instead of fallback
        return f"<h1>Dashboard Error</h1><p>Error: {str(e)}</p><pre>{traceback.format_exc()}</pre>", 500

@app.route('/api/twilio/numbers/available')
@login_required
def get_available_numbers():
    """Get available Twilio numbers for purchase"""
    try:
        area_code = request.args.get('area_code', '555')
        country_code = request.args.get('country_code', 'US')
        
        logger.info(f"🔍 Searching for numbers in area code: {area_code}")
        
        # Check Twilio credentials
        sid = os.environ.get('TWILIO_ACCOUNT_SID')
        token = os.environ.get('TWILIO_AUTH_TOKEN')
        if not sid or not token:
            logger.error("❌ Missing Twilio credentials")
            return jsonify({
                'success': False,
                'error': 'Twilio credentials not configured'
            }), 500
        
        client = get_twilio_client()
        logger.info(f"📞 Querying Twilio API for {country_code} numbers...")
        
        available_numbers = client.available_phone_numbers(country_code)\
            .local.list(area_code=area_code, limit=10)
        
        logger.info(f"📋 Found {len(available_numbers)} available numbers")
        
        numbers = []
        for number in available_numbers:
            numbers.append({
                'phone_number': number.phone_number,
                'friendly_name': number.friendly_name or f"Number in {area_code} area",
                'capabilities': {
                    'voice': number.capabilities.get('voice', False),
                    'sms': number.capabilities.get('SMS', False),
                    'mms': number.capabilities.get('MMS', False)
                },
                'cost': '$1.00/month'  # Default Twilio cost
            })
        
        if not numbers:
            logger.warning(f"⚠️ No numbers found for area code {area_code}")
            return jsonify({
                'success': False,
                'error': f'No available numbers found for area code {area_code}. Try a different area code like 212, 415, or 510.'
            })
        
        return jsonify({
            'success': True,
            'numbers': numbers,
            'count': len(numbers)
        })
        
    except TwilioException as e:
        logger.error(f"❌ Twilio API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Twilio API error: {str(e)}'
        }), 500
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/api/twilio/numbers/purchase', methods=['POST'])
@login_required
def purchase_number():
    """Purchase a Twilio number for the user"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        friendly_name = data.get('friendly_name', '')
        
        if not phone_number:
            return jsonify({'success': False, 'error': 'Phone number required'}), 400
        
        # Check if number is already owned
        existing = TwilioNumber.query.filter_by(phone_number=phone_number).first()
        if existing:
            return jsonify({'success': False, 'error': 'Number already owned'}), 400
        
        # Purchase number via Twilio API
        client = get_twilio_client()
        
        # Set webhook URLs
        domain = os.environ.get('DOMAIN_NAME', 'verifycap.com')
        voice_url = f"https://{domain}/webhooks/voice/{current_user.id}"
        sms_url = f"https://{domain}/webhooks/sms/{current_user.id}"
        
        purchased_number = client.incoming_phone_numbers.create(
            phone_number=phone_number,
            friendly_name=friendly_name or f"{current_user.username}'s Number",
            voice_url=voice_url,
            sms_url=sms_url,
            voice_method='POST',
            sms_method='POST'
        )
        
        # Save to database
        twilio_number = TwilioNumber(
            user_id=current_user.id,
            phone_number=phone_number,
            friendly_name=friendly_name,
            sid=purchased_number.sid,
            capabilities={
                'voice': True,
                'sms': True,
                'mms': True
            },
            monthly_cost=1.00,  # Default Twilio cost
            webhook_url=voice_url
        )
        
        db.session.add(twilio_number)
        db.session.commit()
        
        logger.info(f"✅ Number purchased: {phone_number} for user {current_user.username}")
        
        return jsonify({
            'success': True,
            'message': 'Number purchased successfully!',
            'number': {
                'id': twilio_number.id,
                'phone_number': twilio_number.phone_number,
                'friendly_name': twilio_number.friendly_name,
                'monthly_cost': twilio_number.monthly_cost
            }
        })
        
    except TwilioException as e:
        logger.error(f"❌ Twilio purchase error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to purchase number'
        }), 500
    except Exception as e:
        logger.error(f"❌ Purchase error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Purchase failed'
        }), 500

@app.route('/api/twilio/numbers/<int:number_id>/release', methods=['POST'])
@login_required
def release_number(number_id):
    """Release a Twilio number"""
    try:
        twilio_number = TwilioNumber.query.filter_by(
            id=number_id, 
            user_id=current_user.id
        ).first()
        
        if not twilio_number:
            return jsonify({'success': False, 'error': 'Number not found'}), 404
        
        # Release via Twilio API
        client = get_twilio_client()
        client.incoming_phone_numbers(twilio_number.sid).delete()
        
        # Update database
        twilio_number.status = 'released'
        twilio_number.released_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"✅ Number released: {twilio_number.phone_number}")
        
        return jsonify({
            'success': True,
            'message': 'Number released successfully!'
        })
        
    except TwilioException as e:
        logger.error(f"❌ Twilio release error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to release number'
        }), 500

@app.route('/api/dashboard/stats')
@login_required
def get_dashboard_stats():
    """Get dashboard statistics for the current user"""
    try:
        # Get user's stats
        twilio_numbers = TwilioNumber.query.filter_by(
            user_id=current_user.id, 
            status='active'
        ).all()
        
        total_calls = CallLog.query.filter_by(user_id=current_user.id).count()
        total_sms = SMSLog.query.filter_by(user_id=current_user.id).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_numbers': len(twilio_numbers),
                'total_calls': total_calls,
                'total_sms': total_sms,
                'total_cost': sum(num.monthly_cost or 0 for num in twilio_numbers)
            },
            'numbers': [{
                'id': num.id,
                'phone_number': num.phone_number,
                'friendly_name': num.friendly_name,
                'monthly_cost': num.monthly_cost,
                'purchased_at': num.purchased_at.isoformat() if num.purchased_at else None,
                'status': num.status
            } for num in twilio_numbers]
        })
        
    except Exception as e:
        logger.error(f"❌ Dashboard stats error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load stats'
        }), 500

# Call Logs API Routes
@app.route('/api/calls')
@login_required
def get_call_logs():
    """Get call logs for the current user"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        status_filter = request.args.get('status')
        phone_filter = request.args.get('phone')
        date_filter = request.args.get('date')
        search_filter = request.args.get('search')
        
        query = CallLog.query.filter_by(user_id=current_user.id)
        
        # Apply filters
        if status_filter:
            query = query.filter(CallLog.call_status == status_filter)
        if phone_filter:
            query = query.filter((CallLog.from_number == phone_filter) | (CallLog.to_number == phone_filter))
        if date_filter:
            from datetime import datetime as dt
            date_obj = dt.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(CallLog.created_at >= date_obj, CallLog.created_at < date_obj + timedelta(days=1))
        if search_filter:
            query = query.filter(CallLog.from_number.contains(search_filter))
        
        # Pagination
        total = query.count()
        calls = query.order_by(CallLog.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
        
        return jsonify({
            'success': True,
            'calls': [{
                'id': call.id,
                'call_sid': call.call_sid,
                'from_number': call.from_number,
                'to_number': call.to_number,
                'call_status': call.call_status,
                'duration': call.duration,
                'direction': 'inbound',  # Default for now
                'created_at': call.created_at.isoformat() if call.created_at else None
            } for call in calls],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': (total + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Call logs error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load call logs'
        }), 500

# SMS API Routes
@app.route('/api/sms')
@login_required
def get_sms_messages():
    """Get SMS messages for the current user"""
    try:
        direction_filter = request.args.get('direction')
        phone_filter = request.args.get('phone')
        search_filter = request.args.get('search')
        
        query = SMSLog.query.filter_by(user_id=current_user.id)
        
        # Apply filters
        if direction_filter:
            query = query.filter(SMSLog.direction == direction_filter)
        if phone_filter:
            query = query.filter((SMSLog.from_number == phone_filter) | (SMSLog.to_number == phone_filter))
        if search_filter:
            query = query.filter(SMSLog.body.contains(search_filter))
        
        messages = query.order_by(SMSLog.created_at.desc()).limit(100).all()
        
        return jsonify({
            'success': True,
            'messages': [{
                'id': msg.id,
                'message_sid': msg.message_sid,
                'from_number': msg.from_number,
                'to_number': msg.to_number,
                'body': msg.body,
                'direction': msg.direction or 'inbound',
                'message_status': msg.message_status,
                'media_urls': msg.media_urls or [],
                'created_at': msg.created_at.isoformat() if msg.created_at else None
            } for msg in messages]
        })
        
    except Exception as e:
        logger.error(f"❌ SMS messages error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load SMS messages'
        }), 500

@app.route('/api/sms/send', methods=['POST'])
@login_required
def send_sms():
    """Send an SMS message"""
    try:
        data = request.get_json()
        from_number = data.get('from_number')
        to_number = data.get('to_number')
        body = data.get('body')
        
        if not from_number or not to_number or not body:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Verify user owns the from_number
        twilio_number = TwilioNumber.query.filter_by(
            user_id=current_user.id,
            phone_number=from_number,
            status='active'
        ).first()
        
        if not twilio_number:
            return jsonify({'success': False, 'error': 'Invalid from number'}), 400
        
        # Send via Twilio
        client = get_twilio_client()
        message = client.messages.create(
            body=body,
            from_=from_number,
            to=to_number
        )
        
        # Log the message
        sms_log = SMSLog(
            user_id=current_user.id,
            twilio_number_id=twilio_number.id,
            message_sid=message.sid,
            from_number=from_number,
            to_number=to_number,
            body=body,
            direction='outbound',
            message_status=message.status
        )
        db.session.add(sms_log)
        db.session.commit()
        
        logger.info(f"✅ SMS sent: {message.sid} from {from_number} to {to_number}")
        
        return jsonify({
            'success': True,
            'message': 'SMS sent successfully',
            'message_sid': message.sid
        })
        
    except TwilioException as e:
        logger.error(f"❌ Twilio SMS error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to send SMS'
        }), 500
    except Exception as e:
        logger.error(f"❌ Send SMS error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to send SMS'
        }), 500

# Calendar Routes
@app.route('/calendar')
@login_required
def calendar_page():
    """Calendar page with event management"""
    try:
        return render_template('calendar.html', current_user=current_user)
    except Exception as e:
        logger.error(f"❌ Calendar page error: {str(e)}")
        return redirect(url_for('user_dashboard'))

@app.route('/api/calendar/events')
@login_required
def get_calendar_events():
    """Get calendar events for the current user"""
    try:
        appointments = Appointment.query.filter_by(user_id=current_user.id).all()
        
        events = []
        for apt in appointments:
            events.append({
                'id': apt.id,
                'title': apt.title,
                'description': apt.description,
                'start_time': apt.start_time.isoformat(),
                'end_time': apt.end_time.isoformat(),
                'phone_number': apt.phone_number,
                'event_type': apt.event_type,
                'status': apt.status
            })
        
        return jsonify({
            'success': True,
            'events': events
        })
        
    except Exception as e:
        logger.error(f"❌ Calendar events error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load events'
        }), 500

@app.route('/api/calendar/events', methods=['POST'])
@login_required
def create_calendar_event():
    """Create a new calendar event"""
    try:
        data = request.get_json()
        
        # Parse date and time
        from datetime import datetime as dt, timedelta
        
        date_str = data.get('date')
        time_str = data.get('time')
        duration = int(data.get('duration', 30))
        
        start_datetime = dt.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        end_datetime = start_datetime + timedelta(minutes=duration)
        
        # Create new appointment
        appointment = Appointment(
            user_id=current_user.id,
            title=data.get('title'),
            description=data.get('description', ''),
            start_time=start_datetime,
            end_time=end_datetime,
            phone_number=data.get('phone_number', ''),
            event_type=data.get('event_type', 'call'),
            calendar_provider='voiceai',
            status='scheduled'
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        logger.info(f"✅ Created calendar event: {appointment.title} for user {current_user.username}")
        
        return jsonify({
            'success': True,
            'message': 'Event created successfully',
            'event_id': appointment.id
        })
        
    except Exception as e:
        logger.error(f"❌ Create calendar event error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to create event'
        }), 500

@app.route('/api/calendar/events/<int:event_id>', methods=['PUT'])
@login_required
def update_calendar_event(event_id):
    """Update a calendar event"""
    try:
        appointment = Appointment.query.filter_by(
            id=event_id,
            user_id=current_user.id
        ).first()
        
        if not appointment:
            return jsonify({
                'success': False,
                'error': 'Event not found'
            }), 404
        
        data = request.get_json()
        
        # Update fields if provided
        if 'start_time' in data:
            from datetime import datetime as dt
            appointment.start_time = dt.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        
        if 'end_time' in data:
            from datetime import datetime as dt
            appointment.end_time = dt.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        
        if 'title' in data:
            appointment.title = data['title']
        
        if 'description' in data:
            appointment.description = data['description']
        
        if 'status' in data:
            appointment.status = data['status']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Event updated successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Update calendar event error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to update event'
        }), 500

@app.route('/api/calendar/events/<int:event_id>', methods=['DELETE'])
@login_required
def delete_calendar_event(event_id):
    """Delete a calendar event"""
    try:
        appointment = Appointment.query.filter_by(
            id=event_id,
            user_id=current_user.id
        ).first()
        
        if not appointment:
            return jsonify({
                'success': False,
                'error': 'Event not found'
            }), 404
        
        db.session.delete(appointment)
        db.session.commit()
        
        logger.info(f"✅ Deleted calendar event: {appointment.title} for user {current_user.username}")
        
        return jsonify({
            'success': True,
            'message': 'Event deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Delete calendar event error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to delete event'
        }), 500

@app.route('/api/calendar/stats')
@login_required
def get_calendar_stats():
    """Get calendar statistics"""
    try:
        from datetime import datetime as dt, date, timedelta
        
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        # Today's events
        today_events = Appointment.query.filter(
            Appointment.user_id == current_user.id,
            db.func.date(Appointment.start_time) == today
        ).count()
        
        # This week's events
        week_events = Appointment.query.filter(
            Appointment.user_id == current_user.id,
            db.func.date(Appointment.start_time) >= week_start,
            db.func.date(Appointment.start_time) <= week_end
        ).count()
        
        # Call appointments
        call_appointments = Appointment.query.filter(
            Appointment.user_id == current_user.id,
            Appointment.event_type == 'call'
        ).count()
        
        # Pending appointments
        pending_appointments = Appointment.query.filter(
            Appointment.user_id == current_user.id,
            Appointment.status == 'scheduled'
        ).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'today_events': today_events,
                'week_events': week_events,
                'call_appointments': call_appointments,
                'pending_appointments': pending_appointments
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Calendar stats error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load calendar stats'
        }), 500

@app.route('/api/calendar/recent')
@login_required
def get_recent_appointments():
    """Get recent appointments"""
    try:
        appointments = Appointment.query.filter_by(user_id=current_user.id)\
            .order_by(Appointment.start_time.desc()).limit(10).all()
        
        recent = []
        for apt in appointments:
            recent.append({
                'id': apt.id,
                'title': apt.title,
                'start_time': apt.start_time.isoformat(),
                'phone_number': apt.phone_number,
                'status': apt.status,
                'event_type': apt.event_type
            })
        
        return jsonify({
            'success': True,
            'appointments': recent
        })
        
    except Exception as e:
        logger.error(f"❌ Recent appointments error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load recent appointments'
        }), 500

# Appointments Routes
@app.route('/appointments')
@login_required
def appointments_page():
    """Appointments management page"""
    try:
        return render_template('appointments.html', current_user=current_user)
    except Exception as e:
        logger.error(f"❌ Appointments page error: {str(e)}")
        return redirect(url_for('user_dashboard'))

# Availability Routes
@app.route('/availability')
@login_required
def availability_page():
    """Availability management page"""
    try:
        return render_template('availability.html', current_user=current_user)
    except Exception as e:
        logger.error(f"❌ Availability page error: {str(e)}")
        return redirect(url_for('user_dashboard'))

# Settings Routes
@app.route('/settings')
@login_required
def settings_page():
    """Settings management page"""
    try:
        return render_template('settings.html', current_user=current_user)
    except Exception as e:
        logger.error(f"❌ Settings page error: {str(e)}")
        return redirect(url_for('user_dashboard'))

# Profile Routes
@app.route('/profile')
@login_required
def profile_page():
    """User profile management page"""
    try:
        return render_template('profile.html', current_user=current_user)
    except Exception as e:
        logger.error(f"❌ Profile page error: {str(e)}")
        return redirect(url_for('user_dashboard'))

# Phone Numbers Page
@app.route('/phone-numbers')
@login_required
def phone_numbers_page():
    """Phone numbers management page"""
    try:
        return render_template('phone_numbers.html', current_user=current_user)
    except Exception as e:
        logger.error(f"❌ Phone numbers page error: {str(e)}")
        return redirect(url_for('user_dashboard'))

# Call Logs Page
@app.route('/calls')
@login_required
def calls_page():
    """Call logs page"""
    try:
        return render_template('calls.html', current_user=current_user)
    except Exception as e:
        logger.error(f"❌ Call logs page error: {str(e)}")
        return redirect(url_for('user_dashboard'))

# SMS Messages Page
@app.route('/sms')
@login_required
def sms_page():
    """SMS messages page"""
    try:
        return render_template('sms.html', current_user=current_user)
    except Exception as e:
        logger.error(f"❌ SMS page error: {str(e)}")
        return redirect(url_for('user_dashboard'))

# Contacts Page
@app.route('/contacts')
@login_required
def contacts_page():
    """Contacts management page"""
    try:
        return render_template('contacts.html', current_user=current_user)
    except Exception as e:
        logger.error(f"❌ Contacts page error: {str(e)}")
        return redirect(url_for('user_dashboard'))

# Business Information API Routes
@app.route('/api/user/business-info', methods=['GET'])
@login_required
def get_business_info():
    """Get user's business information"""
    try:
        business_info = BusinessInfo.query.filter_by(user_id=current_user.id).first()
        
        if business_info:
            return jsonify({
                'success': True,
                'business_info': {
                    'business_name': business_info.business_name,
                    'business_type': business_info.business_type,
                    'business_description': business_info.business_description,
                    'business_phone': business_info.business_phone,
                    'business_email': business_info.business_email,
                    'location_address': business_info.location_address,
                    'website_url': business_info.website_url,
                    'business_hours': business_info.business_hours,
                    'services_offered': business_info.services_offered,
                    'pricing_info': business_info.pricing_info,
                    'payment_methods': business_info.payment_methods,
                    'special_offers': business_info.special_offers,
                    'appointment_types': business_info.appointment_types,
                    'booking_policy': business_info.booking_policy,
                    'common_questions': business_info.common_questions,
                    'emergency_contact': business_info.emergency_contact,
                    'alternative_contact': business_info.alternative_contact,
                    'ai_instructions': business_info.ai_instructions
                }
            })
        else:
            return jsonify({
                'success': True,
                'business_info': None
            })
            
    except Exception as e:
        logger.error(f"❌ Get business info error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load business information'
        }), 500

@app.route('/api/user/business-info', methods=['PUT'])
@login_required
def update_business_info():
    """Update user's business information"""
    try:
        data = request.get_json()
        
        # Get or create business info record
        business_info = BusinessInfo.query.filter_by(user_id=current_user.id).first()
        if not business_info:
            business_info = BusinessInfo(user_id=current_user.id)
            db.session.add(business_info)
        
        # Update fields
        business_info.business_name = data.get('business_name', '')
        business_info.business_type = data.get('business_type', '')
        business_info.business_description = data.get('business_description', '')
        business_info.business_phone = data.get('business_phone', '')
        business_info.business_email = data.get('business_email', '')
        business_info.location_address = data.get('business_address', '')
        business_info.website_url = data.get('business_website', '')
        business_info.business_hours = data.get('business_hours', '')
        business_info.services_offered = data.get('services_offered', '')
        business_info.pricing_info = data.get('pricing_info', '')
        business_info.payment_methods = data.get('payment_methods', '')
        business_info.special_offers = data.get('special_offers', '')
        business_info.appointment_types = data.get('appointment_types', '')
        business_info.booking_policy = data.get('booking_policy', '')
        business_info.common_questions = data.get('common_questions', '')
        business_info.emergency_contact = data.get('emergency_contact', '')
        business_info.alternative_contact = data.get('alternative_contact', '')
        business_info.ai_instructions = data.get('ai_instructions', '')
        business_info.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"✅ Updated business info for user {current_user.username}")
        
        return jsonify({
            'success': True,
            'message': 'Business information updated successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Update business info error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to update business information'
        }), 500

@app.route('/api/ai/business-info/<int:user_id>', methods=['GET'])
def get_business_info_for_ai(user_id):
    """Get business information for AI assistant during calls"""
    try:
        # Verify the user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        business_info = BusinessInfo.query.filter_by(user_id=user_id).first()
        
        if business_info:
            # Format the business information in a way that's easy for AI to use
            ai_business_context = {
                'business_name': business_info.business_name,
                'business_type': business_info.business_type,
                'description': business_info.business_description,
                'contact': {
                    'phone': business_info.business_phone,
                    'email': business_info.business_email,
                    'address': business_info.location_address,
                    'website': business_info.website_url,
                    'emergency_contact': business_info.emergency_contact,
                    'alternative_contact': business_info.alternative_contact
                },
                'hours': business_info.business_hours,
                'services': {
                    'offered': business_info.services_offered,
                    'pricing': business_info.pricing_info,
                    'payment_methods': business_info.payment_methods,
                    'special_offers': business_info.special_offers
                },
                'appointments': {
                    'types': business_info.appointment_types,
                    'booking_policy': business_info.booking_policy
                },
                'faq': business_info.common_questions,
                'ai_instructions': business_info.ai_instructions
            }
            
            return jsonify({
                'success': True,
                'business_context': ai_business_context,
                'user_name': user.name or user.username
            })
        else:
            return jsonify({
                'success': True,
                'business_context': {
                    'business_name': 'Business',
                    'message': 'Business information not configured yet'
                },
                'user_name': user.name or user.username
            })
            
    except Exception as e:
        logger.error(f"❌ Get business info for AI error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load business information'
        }), 500

# Contacts API Routes
@app.route('/api/contacts', methods=['GET'])
@login_required
def get_contacts():
    """Get user's contacts"""
    try:
        contacts = Contact.query.filter_by(user_id=current_user.id).order_by(Contact.first_name).all()
        
        contacts_data = []
        for contact in contacts:
            contacts_data.append({
                'id': contact.id,
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'email': contact.email,
                'phone': contact.phone,
                'company': contact.company,
                'job_title': contact.job_title,
                'address': contact.address,
                'notes': contact.notes,
                'tags': contact.tags,
                'contact_group': contact.contact_group,
                'is_favorite': contact.is_favorite,
                'allow_sms': contact.allow_sms,
                'created_at': contact.created_at.isoformat() if contact.created_at else None,
                'updated_at': contact.updated_at.isoformat() if contact.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'contacts': contacts_data
        })
    except Exception as e:
        logger.error(f"❌ Error getting contacts: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load contacts'
        }), 500

@app.route('/api/contacts', methods=['POST'])
@login_required
def create_contact():
    """Create a new contact"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('first_name'):
            return jsonify({
                'success': False,
                'error': 'First name is required'
            }), 400
        
        contact = Contact(
            user_id=current_user.id,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            phone=data.get('phone'),
            company=data.get('company'),
            job_title=data.get('job_title'),
            address=data.get('address'),
            notes=data.get('notes'),
            tags=data.get('tags'),
            contact_group=data.get('contact_group'),
            is_favorite=data.get('is_favorite', False),
            allow_sms=data.get('allow_sms', True)
        )
        
        db.session.add(contact)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contact created successfully',
            'contact_id': contact.id
        })
    except Exception as e:
        logger.error(f"❌ Error creating contact: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to create contact'
        }), 500

@app.route('/api/contacts/<int:contact_id>', methods=['PUT'])
@login_required
def update_contact(contact_id):
    """Update an existing contact"""
    try:
        contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first()
        if not contact:
            return jsonify({
                'success': False,
                'error': 'Contact not found'
            }), 404
        
        data = request.get_json()
        
        # Update contact fields
        contact.first_name = data.get('first_name', contact.first_name)
        contact.last_name = data.get('last_name', contact.last_name)
        contact.email = data.get('email', contact.email)
        contact.phone = data.get('phone', contact.phone)
        contact.company = data.get('company', contact.company)
        contact.job_title = data.get('job_title', contact.job_title)
        contact.address = data.get('address', contact.address)
        contact.notes = data.get('notes', contact.notes)
        contact.tags = data.get('tags', contact.tags)
        contact.contact_group = data.get('contact_group', contact.contact_group)
        contact.is_favorite = data.get('is_favorite', contact.is_favorite)
        contact.allow_sms = data.get('allow_sms', contact.allow_sms)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contact updated successfully'
        })
    except Exception as e:
        logger.error(f"❌ Error updating contact: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to update contact'
        }), 500

@app.route('/api/contacts/<int:contact_id>', methods=['DELETE'])
@login_required
def delete_contact(contact_id):
    """Delete a contact"""
    try:
        contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first()
        if not contact:
            return jsonify({
                'success': False,
                'error': 'Contact not found'
            }), 404
        
        db.session.delete(contact)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contact deleted successfully'
        })
    except Exception as e:
        logger.error(f"❌ Error deleting contact: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to delete contact'
        }), 500

@app.route('/api/contacts/<int:contact_id>/favorite', methods=['PUT'])
@login_required
def toggle_contact_favorite(contact_id):
    """Toggle contact favorite status"""
    try:
        contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first()
        if not contact:
            return jsonify({
                'success': False,
                'error': 'Contact not found'
            }), 404
        
        data = request.get_json()
        contact.is_favorite = data.get('is_favorite', not contact.is_favorite)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contact favorite status updated'
        })
    except Exception as e:
        logger.error(f"❌ Error updating contact favorite: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to update favorite status'
        }), 500

@app.route('/api/contacts/activity', methods=['GET'])
@login_required
def get_contact_activity():
    """Get recent contact activity"""
    try:
        # Get recent contacts (last 5 added)
        recent_contacts = Contact.query.filter_by(user_id=current_user.id)\
            .order_by(Contact.created_at.desc()).limit(5).all()
        
        activities = []
        for contact in recent_contacts:
            activities.append({
                'title': f"Added {contact.first_name} {contact.last_name or ''}",
                'description': f"New contact added to {contact.contact_group or 'your contacts'}",
                'icon': 'bi-person-plus',
                'created_at': contact.created_at.isoformat() if contact.created_at else None
            })
        
        return jsonify({
            'success': True,
            'activities': activities
        })
    except Exception as e:
        logger.error(f"❌ Error getting contact activity: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load activity'
        }), 500

@app.route('/webhooks/voice/<int:user_id>', methods=['POST'])
def handle_user_voice_webhook(user_id):
    """Handle incoming voice calls for specific user"""
    try:
        call_sid = request.form.get('CallSid')
        from_number = request.form.get('From')
        to_number = request.form.get('To')
        call_status = request.form.get('CallStatus')
        
        logger.info(f"📞 User {user_id} voice webhook: {call_sid} from {from_number} to {to_number}")
        
        # Find the user and their Twilio number
        user = User.query.get(user_id)
        if not user:
            logger.error(f"❌ User {user_id} not found")
            return "User not found", 404
        
        twilio_number = TwilioNumber.query.filter_by(
            user_id=user_id,
            phone_number=to_number,
            status='active'
        ).first()
        
        # Log the call
        call_log = CallLog(
            call_sid=call_sid,
            from_number=from_number,
            to_number=to_number,
            call_status=call_status,
            user_id=user_id,
            twilio_number_id=twilio_number.id if twilio_number else None
        )
        db.session.add(call_log)
        db.session.commit()
        
        # Return TwiML response
        domain = os.environ.get('DOMAIN_NAME', 'verifycap.com')
        twiml_response = f'''<Response>
    <Connect>
        <Stream url="wss://{domain}/ws/voice-agent-v1/{user_id}" />
    </Connect>
</Response>'''
        
        return twiml_response, 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error(f"❌ User voice webhook error: {str(e)}")
        error_response = '''<Response>
    <Say>I'm sorry, there was an error. Please try again.</Say>
    <Hangup />
</Response>'''
        return error_response, 200, {'Content-Type': 'text/xml'}

@app.route('/webhooks/sms/<int:user_id>', methods=['POST'])
def handle_user_sms_webhook(user_id):
    """Handle incoming SMS for specific user"""
    try:
        message_sid = request.form.get('MessageSid')
        from_number = request.form.get('From')
        to_number = request.form.get('To')
        body = request.form.get('Body', '')
        num_media = int(request.form.get('NumMedia', 0))
        
        logger.info(f"📱 User {user_id} SMS webhook: {message_sid} from {from_number}")
        
        # Find the user and their Twilio number
        user = User.query.get(user_id)
        if not user:
            logger.error(f"❌ User {user_id} not found")
            return "User not found", 404
        
        twilio_number = TwilioNumber.query.filter_by(
            user_id=user_id,
            phone_number=to_number,
            status='active'
        ).first()
        
        # Handle media URLs
        media_urls = []
        for i in range(num_media):
            media_url = request.form.get(f'MediaUrl{i}')
            if media_url:
                media_urls.append(media_url)
        
        # Log the SMS
        sms_log = SMSLog(
            user_id=user_id,
            twilio_number_id=twilio_number.id if twilio_number else None,
            message_sid=message_sid,
            from_number=from_number,
            to_number=to_number,
            body=body,
            direction='inbound',
            status='received',
            media_urls=media_urls if media_urls else None
        )
        db.session.add(sms_log)
        db.session.commit()
        
        # Auto-reply logic can be added here
        response_body = f"Thank you for your message! We'll get back to you soon."
        
        twiml_response = f'''<Response>
    <Message>{response_body}</Message>
</Response>'''
        
        return twiml_response, 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error(f"❌ User SMS webhook error: {str(e)}")
        return '<Response></Response>', 200, {'Content-Type': 'text/xml'}

@app.route('/webhooks/voice', methods=['POST'])
def handle_voice_webhook():
    """Handle incoming Twilio voice webhooks - Deepgram Voice Agent V1"""
    try:
        logger.info(f"🎯 Voice webhook called with data: {dict(request.form)}")
        
        call_sid = request.form.get('CallSid')
        from_number = request.form.get('From')
        to_number = request.form.get('To')
        call_status = request.form.get('CallStatus')
        
        logger.info(f"📞 Voice webhook: {call_sid} from {from_number} to {to_number} status {call_status}")
        
        # Return TwiML response with WebSocket stream to Deepgram Voice Agent bridge
        domain = os.environ.get('DOMAIN_NAME', 'verifycap.com')
        
        twiml_response = f'''<Response>
    <Connect>
        <Stream url="wss://{domain}/ws/voice-agent-v1" />
    </Connect>
</Response>'''
        
        logger.info(f"📤 Returning TwiML with WebSocket URL: wss://{domain}/ws/voice-agent-v1")
        return twiml_response, 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error(f"❌ Error in voice webhook: {str(e)}")
        error_response = '''<Response>
    <Say>I'm sorry, there was an error. Please try again.</Say>
    <Hangup />
</Response>'''
        return error_response, 200, {'Content-Type': 'text/xml'}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'Deepgram Voice Agent V1',
        'voice_model': 'aura-2-amalthea-en'
    }

@app.route('/api/status', methods=['GET'])
def api_status():
    """API status endpoint"""
    return {
        'status': 'Voice AI Assistant with Deepgram Voice Agent V1',
        'version': '1.0.0',
        'voice_model': 'aura-2-amalthea-en',
        'endpoints': {
            'voice_webhook': '/webhooks/voice',
            'health': '/api/health'
        }
    }

@app.route('/test-webhook', methods=['GET', 'POST'])
def test_webhook():
    """Test webhook endpoint"""
    if request.method == 'POST':
        test_response = '''<Response>
    <Say>Test webhook working! This is the simplified Deepgram Voice Agent app.</Say>
    <Hangup />
</Response>'''
        return test_response, 200, {'Content-Type': 'text/xml'}
    else:
        return "Test webhook is working - use POST for voice calls", 200


def get_dashboard_data():
    """Get real dashboard data from database and system"""
    try:
        from datetime import datetime, timedelta
        
        # Get current date for filtering
        today = datetime.now().date()
        
        # Get user and appointment counts
        total_users = User.query.count()
        total_appointments = Appointment.query.count()
        today_appointments = Appointment.query.filter(
            db.func.date(Appointment.created_at) == today
        ).count()
        
        # Get calendar connection status
        google_connected = User.query.filter(User.google_calendar_token.isnot(None)).count()
        microsoft_connected = User.query.filter(User.microsoft_calendar_token.isnot(None)).count()
        apple_connected = User.query.filter(User.apple_calendar_enabled == True).count()
        
        # Get recent appointments
        recent_appointments = Appointment.query.order_by(
            Appointment.created_at.desc()
        ).limit(5).all()
        
        # Calculate some stats
        confirmed_appointments = Appointment.query.filter_by(status='confirmed').count()
        pending_appointments = Appointment.query.filter_by(status='scheduled').count()
        
        # Get call logs data
        total_calls = CallLog.query.count()
        today_calls = CallLog.query.filter(
            db.func.date(CallLog.start_time) == today
        ).count()
        completed_calls = CallLog.query.filter_by(call_status='completed').count()
        
        # Get recent call logs
        recent_calls = CallLog.query.order_by(
            CallLog.start_time.desc()
        ).limit(10).all()
        
        # Calculate average call duration
        avg_duration_result = db.session.query(db.func.avg(CallLog.call_duration)).filter(
            CallLog.call_duration.isnot(None)
        ).scalar()
        avg_call_duration = int(avg_duration_result) if avg_duration_result else 0
        
        return {
            'total_users': total_users,
            'total_appointments': total_appointments,
            'today_appointments': today_appointments,
            'google_connected': google_connected,
            'microsoft_connected': microsoft_connected,
            'apple_connected': apple_connected,
            'recent_appointments': recent_appointments,
            'confirmed_appointments': confirmed_appointments,
            'pending_appointments': pending_appointments,
            'calendar_sync_status': 'Connected' if (google_connected + microsoft_connected + apple_connected) > 0 else 'Not Connected',
            'total_calls': total_calls,
            'today_calls': today_calls,
            'completed_calls': completed_calls,
            'recent_calls': recent_calls,
            'avg_call_duration': avg_call_duration
        }
    except Exception as e:
        logger.error(f"❌ Error getting dashboard data: {e}")
        return {
            'total_users': 0,
            'total_appointments': 0,
            'today_appointments': 0,
            'google_connected': 0,
            'microsoft_connected': 0,
            'apple_connected': 0,
            'recent_appointments': [],
            'confirmed_appointments': 0,
            'pending_appointments': 0,
            'calendar_sync_status': 'Error',
            'total_calls': 0,
            'today_calls': 0,
            'completed_calls': 0,
            'recent_calls': [],
            'avg_call_duration': 0
        }

def render_call_logs_table(recent_calls):
    """Render call logs table HTML"""
    if not recent_calls:
        return '<tr><td colspan="6" style="padding: 1rem; text-align: center; color: #9ca3af;">No calls yet</td></tr>'
    
    html = ""
    for call in recent_calls:
        status_color = {
            'completed': '#10b981',
            'in-progress': '#3b82f6',
            'failed': '#ef4444'
        }.get(call.call_status, '#6b7280')
        
        duration = f"{call.call_duration//60}:{call.call_duration%60:02d}" if call.call_duration else "N/A"
        formatted_time = call.start_time.strftime('%b %d, %I:%M %p') if call.start_time else 'N/A'
        
        # Transcript dropdown
        transcript_html = ""
        if call.transcript:
            transcript_preview = call.transcript[:50] + "..." if len(call.transcript) > 50 else call.transcript
            transcript_html = f'''
            <div style="position: relative;">
                <button onclick="toggleTranscript('{call.call_sid}')" style="
                    background: linear-gradient(135deg, #3b82f6, #1d4ed8);
                    color: white;
                    border: none;
                    padding: 0.5rem 1rem;
                    border-radius: 0.5rem;
                    cursor: pointer;
                    font-size: 0.875rem;
                    font-weight: 500;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    transition: all 0.2s ease;
                    box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
                " onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 8px rgba(59, 130, 246, 0.3)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(59, 130, 246, 0.2)'">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14,2 14,8 20,8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                        <polyline points="10,9 9,9 8,9"></polyline>
                    </svg>
                    View Transcript
                </button>
                <div id="transcript-{call.call_sid}" style="
                    display: none;
                    position: absolute;
                    top: 100%;
                    left: 0;
                    background: #1f2937;
                    border: 1px solid #374151;
                    border-radius: 0.75rem;
                    padding: 1.5rem;
                    max-width: 400px;
                    max-height: 300px;
                    overflow-y: auto;
                    z-index: 20;
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
                    margin-top: 0.5rem;
                    backdrop-filter: blur(8px);
                    animation: slideIn 0.2s ease-out;
                ">
                    <div style="
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 1rem;
                        padding-bottom: 0.75rem;
                        border-bottom: 1px solid #374151;
                    ">
                        <h4 style="color: #f3f4f6; font-weight: 600; margin: 0;">Call Transcript</h4>
                        <button onclick="toggleTranscript('{call.call_sid}')" style="
                            background: none;
                            border: none;
                            color: #9ca3af;
                            cursor: pointer;
                            padding: 0.25rem;
                            border-radius: 0.25rem;
                            transition: color 0.2s;
                        " onmouseover="this.style.color='#f3f4f6'" onmouseout="this.style.color='#9ca3af'">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                        </button>
                    </div>
                    <div style="
                        font-size: 0.875rem;
                        line-height: 1.6;
                        color: #d1d5db;
                        white-space: pre-wrap;
                        word-break: break-word;
                    ">{call.transcript}</div>
                    <div style="
                        margin-top: 1rem;
                        padding-top: 0.75rem;
                        border-top: 1px solid #374151;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    ">
                        <span style="color: #6b7280; font-size: 0.75rem;">
                            Duration: {f"{call.call_duration//60}:{call.call_duration%60:02d}" if call.call_duration else "N/A"}
                        </span>
                        <button onclick="toggleTranscript('{call.call_sid}')" style="
                            background: #374151;
                            color: #d1d5db;
                            border: none;
                            padding: 0.5rem 1rem;
                            border-radius: 0.375rem;
                            cursor: pointer;
                            font-size: 0.75rem;
                            font-weight: 500;
                            transition: all 0.2s;
                        " onmouseover="this.style.background='#4b5563'" onmouseout="this.style.background='#374151'">
                            Close
                        </button>
                    </div>
                </div>
            </div>
            '''
        else:
            transcript_html = '<span style="color: #6b7280; font-style: italic;">No transcript available</span>'
        
        # Audio playback
        audio_html = ""
        if call.recording_url:
            audio_html = f'''
            <audio controls style="width: 150px; height: 30px;">
                <source src="{call.recording_url}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
            '''
        else:
            audio_html = '<span style="color: #6b7280;">No recording</span>'
        
        html += f'''
        <tr style="border-bottom: 1px solid #374151;">
            <td style="padding: 0.75rem;">{call.from_number}</td>
            <td style="padding: 0.75rem;">{formatted_time}</td>
            <td style="padding: 0.75rem;">{duration}</td>
            <td style="padding: 0.75rem;"><span style="color: {status_color};">{call.call_status.title() if call.call_status else 'Unknown'}</span></td>
            <td style="padding: 0.75rem;">{transcript_html}</td>
            <td style="padding: 0.75rem;">{audio_html}</td>
        </tr>
        '''
    
    return html

def render_dashboard_with_data(data):
    """Render dashboard HTML with real data"""
    # Format recent call logs
    call_logs_html = render_call_logs_table(data['recent_calls'])
    
    # Format recent appointments
    appointments_html = ""
    for apt in data['recent_appointments']:
        status_color = {
            'confirmed': '#10b981',
            'scheduled': '#eab308', 
            'cancelled': '#ef4444'
        }.get(apt.status, '#6b7280')
        
        appointments_html += f"""
        <tr style="border-bottom: 1px solid #374151;">
            <td style="padding: 0.75rem;">{apt.title}</td>
            <td style="padding: 0.75rem;">{apt.start_time.strftime('%b %d, %I:%M %p') if apt.start_time else 'N/A'}</td>
            <td style="padding: 0.75rem;">{apt.calendar_provider.title()}</td>
            <td style="padding: 0.75rem;"><span style="color: {status_color};">{apt.status.title()}</span></td>
        </tr>
        """
    
    if not appointments_html:
        appointments_html = '<tr><td colspan="4" style="padding: 1rem; text-align: center; color: #9ca3af;">No appointments yet</td></tr>'
    
    # Calendar sync status
    sync_status = data['calendar_sync_status']
    sync_color = '#10b981' if sync_status == 'Connected' else '#ef4444'
    sync_icon = '✅' if sync_status == 'Connected' else '❌'
    
    # Generate dynamic HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VoiceAI Dashboard - Real Data</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #111827; color: white; }}
        .container {{ display: flex; min-height: 100vh; }}
        .sidebar {{ width: 16rem; background: #1f2937; padding: 1.5rem; }}
        .main {{ flex: 1; padding: 1.5rem; }}
        .nav-item {{ display: block; padding: 0.75rem 1rem; margin: 0.25rem 0; border-radius: 0.5rem; color: #d1d5db; text-decoration: none; transition: all 0.2s; }}
        .nav-item:hover, .nav-item.active {{ background: #374151; color: white; }}
        .card {{ background: #1f2937; border-radius: 0.5rem; padding: 1.5rem; margin-bottom: 1.5rem; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }}
        .metric-card {{ background: #1f2937; border-radius: 0.5rem; padding: 1.5rem; }}
        .metric-value {{ font-size: 2rem; font-weight: bold; color: #3b82f6; }}
        .metric-label {{ color: #9ca3af; margin-top: 0.5rem; }}
        h1 {{ font-size: 1.875rem; font-weight: bold; margin-bottom: 1.5rem; }}
        h2 {{ font-size: 1.25rem; font-weight: semibold; margin-bottom: 1rem; }}
        .btn {{ display: inline-block; padding: 0.5rem 1rem; background: #3b82f6; color: white; border-radius: 0.375rem; text-decoration: none; transition: all 0.2s; }}
        .btn:hover {{ background: #2563eb; }}
        .status-ok {{ color: #10b981; }}
        .status-error {{ color: #ef4444; }}
        .calendar-connect {{ border: 2px dashed #374151; border-radius: 0.5rem; padding: 2rem; text-align: center; margin: 1rem 0; }}
        .live-indicator {{ display: inline-block; width: 8px; height: 8px; background: #10b981; border-radius: 50%; margin-right: 0.5rem; animation: pulse 2s infinite; }}
        @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} 100% {{ opacity: 1; }} }}
        @keyframes slideIn {{ 
            0% {{ opacity: 0; transform: translateY(-10px) scale(0.95); }}
            100% {{ opacity: 1; transform: translateY(0) scale(1); }}
        }}
        .refresh-time {{ color: #6b7280; font-size: 0.875rem; text-align: right; margin-bottom: 1rem; }}
    </style>
</head>
<body>
    <div class="container">
        <nav class="sidebar">
            <div style="border-bottom: 1px solid #374151; padding-bottom: 1rem; margin-bottom: 1rem;">
                <h2 style="color: white;">Voice<span style="color: #3b82f6;">AI</span> Dashboard</h2>
                <div class="live-indicator"></div><span style="font-size: 0.875rem; color: #9ca3af;">Live Data</span>
            </div>
            <a href="#dashboard" class="nav-item active" onclick="showSection('dashboard')">📊 Dashboard</a>
            <a href="#calendar" class="nav-item" onclick="showSection('calendar')">📅 Calendar</a>
            <a href="#calls" class="nav-item" onclick="showSection('calls')">📞 Call Logs</a>
            <a href="#users" class="nav-item" onclick="showSection('users')">👥 Analytics</a>
            <a href="#settings" class="nav-item" onclick="showSection('settings')">⚙️ Settings</a>
            <div style="margin-top: auto; padding-top: 2rem;">
                <a href="tel:+18444356005" class="btn" style="width: 100%; text-align: center;">📞 Test Call</a>
            </div>
        </nav>

        <main class="main">
            <div id="dashboard-section">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                    <h1>Dashboard</h1>
                    <div class="refresh-time">Last updated: {datetime.now().strftime('%I:%M %p')}</div>
                </div>
                
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value">{data['total_users']}</div>
                        <div class="metric-label">Total Users</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{data['today_appointments']}</div>
                        <div class="metric-label">Appointments Today</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{data['total_appointments']}</div>
                        <div class="metric-label">Total Appointments</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{data['google_connected'] + data['microsoft_connected'] + data['apple_connected']}</div>
                        <div class="metric-label">Connected Calendars</div>
                    </div>
                </div>

                <div class="card">
                    <h2>System Status</h2>
                    <div style="display: grid; gap: 1rem;">
                        <div style="display: flex; justify-content: space-between;">
                            <span>Voice AI (Amelia)</span>
                            <span class="status-ok">✅ Operational</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>WebSocket Bridge</span>
                            <span class="status-ok">✅ Operational</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>Calendar Sync</span>
                            <span style="color: {sync_color};">{sync_icon} {sync_status}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>Database</span>
                            <span class="status-ok">✅ Connected</span>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <h2>Recent Appointments</h2>
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="border-bottom: 1px solid #374151;">
                                    <th style="text-align: left; padding: 0.75rem; color: #9ca3af;">Title</th>
                                    <th style="text-align: left; padding: 0.75rem; color: #9ca3af;">Time</th>
                                    <th style="text-align: left; padding: 0.75rem; color: #9ca3af;">Calendar</th>
                                    <th style="text-align: left; padding: 0.75rem; color: #9ca3af;">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {appointments_html}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div id="calendar-section" style="display: none;">
                <h1>Calendar Integration</h1>
                <div class="refresh-time">Calendar connections: {data['google_connected']} Google, {data['microsoft_connected']} Microsoft, {data['apple_connected']} Apple</div>

                <div class="metric-grid" style="margin-bottom: 2rem;">
                    <div class="metric-card">
                        <div class="metric-value">{data['confirmed_appointments']}</div>
                        <div class="metric-label">Confirmed Appointments</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{data['pending_appointments']}</div>
                        <div class="metric-label">Pending Appointments</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{data['google_connected']}</div>
                        <div class="metric-label">Google Connected</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{data['microsoft_connected']}</div>
                        <div class="metric-label">Microsoft Connected</div>
                    </div>
                </div>

                <div class="metric-grid">
                    <div class="calendar-connect">
                        <div style="margin-bottom: 1rem;">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                                <rect x="3" y="4" width="18" height="18" rx="2" ry="2" stroke="#4285f4" stroke-width="2" fill="none"/>
                                <line x1="16" y1="2" x2="16" y2="6" stroke="#4285f4" stroke-width="2"/>
                                <line x1="8" y1="2" x2="8" y2="6" stroke="#4285f4" stroke-width="2"/>
                                <line x1="3" y1="10" x2="21" y2="10" stroke="#4285f4" stroke-width="2"/>
                            </svg>
                        </div>
                        <h3 style="margin-bottom: 0.5rem;">Google Calendar</h3>
                        <p style="color: #9ca3af; margin-bottom: 1rem;">Gmail & Workspace ({data['google_connected']} connected)</p>
                        <a href="/api/calendar/connect/google" class="btn">Connect Google</a>
                    </div>
                    
                    <div class="calendar-connect">
                        <div style="margin-bottom: 1rem;">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                                <rect x="2" y="3" width="20" height="14" rx="2" ry="2" stroke="#0078d4" stroke-width="2" fill="none"/>
                                <polyline points="22,6 12,13 2,6" stroke="#0078d4" stroke-width="2" fill="none"/>
                                <rect x="8" y="10" width="8" height="6" rx="1" ry="1" fill="#0078d4"/>
                                <line x1="10" y1="12" x2="14" y2="12" stroke="white" stroke-width="1"/>
                                <line x1="10" y1="14" x2="14" y2="14" stroke="white" stroke-width="1"/>
                            </svg>
                        </div>
                        <h3 style="margin-bottom: 0.5rem;">Microsoft Calendar</h3>
                        <p style="color: #9ca3af; margin-bottom: 1rem;">Outlook & Office 365 ({data['microsoft_connected']} connected)</p>
                        <a href="/api/calendar/connect/microsoft" class="btn">Connect Microsoft</a>
                    </div>
                    
                    <div class="calendar-connect">
                        <div style="margin-bottom: 1rem;">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                                <path d="M12 2L13.09 8.26L19 9L13.09 9.74L12 16L10.91 9.74L5 9L10.91 8.26L12 2Z" fill="#007AFF"/>
                                <rect x="3" y="4" width="18" height="16" rx="2" ry="2" stroke="#007AFF" stroke-width="2" fill="none"/>
                                <line x1="3" y1="10" x2="21" y2="10" stroke="#007AFF" stroke-width="2"/>
                                <line x1="8" y1="2" x2="8" y2="6" stroke="#007AFF" stroke-width="2"/>
                                <line x1="16" y1="2" x2="16" y2="6" stroke="#007AFF" stroke-width="2"/>
                            </svg>
                        </div>
                        <h3 style="margin-bottom: 0.5rem;">Apple iCloud</h3>
                        <p style="color: #9ca3af; margin-bottom: 1rem;">iCloud Calendar ({data['apple_connected']} connected)</p>
                        <a href="/api/calendar/connect/apple" class="btn">Connect Apple</a>
                    </div>
                </div>
            </div>

            <div id="calls-section" style="display: none;">
                <h1>Call Logs & Transcripts</h1>
                
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value">{data['total_calls']}</div>
                        <div class="metric-label">Total Calls</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{data['today_calls']}</div>
                        <div class="metric-label">Calls Today</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{data['completed_calls']}</div>
                        <div class="metric-label">Completed Calls</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{f"{data['avg_call_duration']//60}:{data['avg_call_duration']%60:02d}" if data['avg_call_duration'] > 0 else "0:00"}</div>
                        <div class="metric-label">Avg Duration</div>
                    </div>
                </div>

                <div class="card">
                    <h2>Recent Calls</h2>
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="border-bottom: 1px solid #374151;">
                                    <th style="text-align: left; padding: 0.75rem; color: #9ca3af;">Phone Number</th>
                                    <th style="text-align: left; padding: 0.75rem; color: #9ca3af;">Date/Time</th>
                                    <th style="text-align: left; padding: 0.75rem; color: #9ca3af;">Duration</th>
                                    <th style="text-align: left; padding: 0.75rem; color: #9ca3af;">Status</th>
                                    <th style="text-align: left; padding: 0.75rem; color: #9ca3af;">Transcript</th>
                                    <th style="text-align: left; padding: 0.75rem; color: #9ca3af;">Audio</th>
                                </tr>
                            </thead>
                            <tbody id="call-logs-table">
                                {call_logs_html}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div id="users-section" style="display: none;">
                <h1>Analytics & Reports</h1>
                
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value">{data['total_users']}</div>
                        <div class="metric-label">Total Users</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{data['total_appointments']}</div>
                        <div class="metric-label">Total Appointments</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{round((data['confirmed_appointments'] / max(data['total_appointments'], 1)) * 100)}%</div>
                        <div class="metric-label">Confirmation Rate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{round(data['total_appointments'] / max(data['total_users'], 1), 1)}</div>
                        <div class="metric-label">Avg Appointments/User</div>
                    </div>
                </div>

                <div class="card">
                    <h2>User Activity</h2>
                    <p style="color: #9ca3af;">Detailed user analytics and call patterns coming soon...</p>
                </div>
            </div>

            <div id="settings-section" style="display: none;">
                <h1>Settings</h1>
                
                <div class="card">
                    <h2>Voice AI Configuration</h2>
                    <div style="display: grid; gap: 1rem;">
                        <div style="display: flex; justify-content: space-between;">
                            <span>Current Voice Model</span>
                            <span style="color: #3b82f6;">Amelia (ElevenLabs)</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>AI Model</span>
                            <span style="color: #3b82f6;">GPT-4o-mini</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>Speech Recognition</span>
                            <span style="color: #3b82f6;">Deepgram STT</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>Phone Number</span>
                            <span style="color: #3b82f6;">+1 (844) 435-6005</span>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <h2>Business Information</h2>
                    <p style="color: #9ca3af; margin-bottom: 1.5rem;">Upload your business details for the AI to reference during calls</p>
                    
                    <form id="business-info-form" style="display: grid; gap: 1.5rem;">
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem;">
                            <div>
                                <label style="display: block; margin-bottom: 0.5rem; color: #d1d5db; font-weight: 600;">Business Name</label>
                                <input type="text" id="business_name" placeholder="e.g., ABC Consulting Services" style="width: 100%; padding: 0.75rem; background: #374151; color: white; border: 1px solid #4b5563; border-radius: 0.375rem;">
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 0.5rem; color: #d1d5db; font-weight: 600;">Website URL</label>
                                <input type="url" id="website_url" placeholder="https://yourwebsite.com" style="width: 100%; padding: 0.75rem; background: #374151; color: white; border: 1px solid #4b5563; border-radius: 0.375rem;">
                            </div>
                        </div>
                        
                        <div>
                            <label style="display: block; margin-bottom: 0.5rem; color: #d1d5db; font-weight: 600;">Business Description</label>
                            <textarea id="business_description" rows="3" placeholder="Brief description of your business and what you do..." style="width: 100%; padding: 0.75rem; background: #374151; color: white; border: 1px solid #4b5563; border-radius: 0.375rem; resize: vertical;"></textarea>
                        </div>
                        
                        <div>
                            <label style="display: block; margin-bottom: 0.5rem; color: #d1d5db; font-weight: 600;">Services Offered</label>
                            <textarea id="services_offered" rows="4" placeholder="List your services, products, or offerings...&#10;e.g.:&#10;- Business consulting&#10;- Strategy planning&#10;- Market analysis" style="width: 100%; padding: 0.75rem; background: #374151; color: white; border: 1px solid #4b5563; border-radius: 0.375rem; resize: vertical;"></textarea>
                        </div>
                        
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem;">
                            <div>
                                <label style="display: block; margin-bottom: 0.5rem; color: #d1d5db; font-weight: 600;">Business Hours</label>
                                <textarea id="business_hours" rows="4" placeholder="e.g.:&#10;Monday-Friday: 9:00 AM - 5:00 PM&#10;Saturday: 10:00 AM - 2:00 PM&#10;Sunday: Closed" style="width: 100%; padding: 0.75rem; background: #374151; color: white; border: 1px solid #4b5563; border-radius: 0.375rem; resize: vertical;"></textarea>
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 0.5rem; color: #d1d5db; font-weight: 600;">Pricing Information</label>
                                <textarea id="pricing_info" rows="4" placeholder="e.g.:&#10;Consultation: $150/hour&#10;Strategy Package: $2,500&#10;Monthly Retainer: $5,000" style="width: 100%; padding: 0.75rem; background: #374151; color: white; border: 1px solid #4b5563; border-radius: 0.375rem; resize: vertical;"></textarea>
                            </div>
                        </div>
                        
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem;">
                            <div>
                                <label style="display: block; margin-bottom: 0.5rem; color: #d1d5db; font-weight: 600;">Contact Information</label>
                                <textarea id="contact_info" rows="3" placeholder="e.g.:&#10;Email: info@business.com&#10;Phone: (555) 123-4567" style="width: 100%; padding: 0.75rem; background: #374151; color: white; border: 1px solid #4b5563; border-radius: 0.375rem; resize: vertical;"></textarea>
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 0.5rem; color: #d1d5db; font-weight: 600;">Location/Address</label>
                                <textarea id="location_address" rows="3" placeholder="e.g.:&#10;123 Business St.&#10;City, State 12345" style="width: 100%; padding: 0.75rem; background: #374151; color: white; border: 1px solid #4b5563; border-radius: 0.375rem; resize: vertical;"></textarea>
                            </div>
                        </div>
                        
                        <div>
                            <label style="display: block; margin-bottom: 0.5rem; color: #d1d5db; font-weight: 600;">Additional Information</label>
                            <textarea id="additional_info" rows="4" placeholder="Any other information you want the AI to know about your business..." style="width: 100%; padding: 0.75rem; background: #374151; color: white; border: 1px solid #4b5563; border-radius: 0.375rem; resize: vertical;"></textarea>
                        </div>
                        
                        <div style="display: flex; gap: 1rem; align-items: center;">
                            <button type="submit" class="btn" style="padding: 0.75rem 2rem;">Save Business Info</button>
                            <div id="save-status" style="color: #9ca3af; font-size: 0.875rem;"></div>
                        </div>
                    </form>
                </div>

                <div class="card">
                    <h2>Database Status</h2>
                    <div style="display: grid; gap: 1rem;">
                        <div style="display: flex; justify-content: space-between;">
                            <span>Users Table</span>
                            <span class="status-ok">{data['total_users']} records</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>Appointments Table</span>
                            <span class="status-ok">{data['total_appointments']} records</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>Calendar Settings</span>
                            <span class="status-ok">Active</span>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        function showSection(sectionName) {{
            // Hide all sections
            const sections = ['dashboard', 'calendar', 'calls', 'users', 'settings'];
            sections.forEach(section => {{
                document.getElementById(section + '-section').style.display = 'none';
            }});
            
            // Remove active class from all nav items
            document.querySelectorAll('.nav-item').forEach(item => {{
                item.classList.remove('active');
            }});
            
            // Show selected section
            document.getElementById(sectionName + '-section').style.display = 'block';
            
            // Add active class to clicked nav item
            event.target.classList.add('active');
        }}
        
        function toggleTranscript(callSid) {{
            const transcriptDiv = document.getElementById('transcript-' + callSid);
            if (transcriptDiv.style.display === 'none' || transcriptDiv.style.display === '') {{
                // Hide all other open transcripts
                document.querySelectorAll('[id^="transcript-"]').forEach(div => {{
                    div.style.display = 'none';
                }});
                // Show this transcript
                transcriptDiv.style.display = 'block';
            }} else {{
                transcriptDiv.style.display = 'none';
            }}
        }}
        
        // Load business info when settings section is shown
        function loadBusinessInfo() {{
            fetch('/api/business-info')
                .then(response => response.json())
                .then(data => {{
                    document.getElementById('business_name').value = data.business_name || '';
                    document.getElementById('business_description').value = data.business_description || '';
                    document.getElementById('services_offered').value = data.services_offered || '';
                    document.getElementById('pricing_info').value = data.pricing_info || '';
                    document.getElementById('business_hours').value = data.business_hours || '';
                    document.getElementById('contact_info').value = data.contact_info || '';
                    document.getElementById('location_address').value = data.location_address || '';
                    document.getElementById('website_url').value = data.website_url || '';
                    document.getElementById('additional_info').value = data.additional_info || '';
                }})
                .catch(error => {{
                    console.error('Error loading business info:', error);
                }});
        }}
        
        // Handle business info form submission
        document.getElementById('business-info-form').addEventListener('submit', function(e) {{
            e.preventDefault();
            
            const statusDiv = document.getElementById('save-status');
            statusDiv.textContent = 'Saving...';
            statusDiv.style.color = '#3b82f6';
            
            const formData = {{
                business_name: document.getElementById('business_name').value,
                business_description: document.getElementById('business_description').value,
                services_offered: document.getElementById('services_offered').value,
                pricing_info: document.getElementById('pricing_info').value,
                business_hours: document.getElementById('business_hours').value,
                contact_info: document.getElementById('contact_info').value,
                location_address: document.getElementById('location_address').value,
                website_url: document.getElementById('website_url').value,
                additional_info: document.getElementById('additional_info').value
            }};
            
            fetch('/api/business-info', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify(formData)
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    statusDiv.textContent = '✅ Saved successfully!';
                    statusDiv.style.color = '#10b981';
                    setTimeout(() => {{
                        statusDiv.textContent = '';
                    }}, 3000);
                }} else {{
                    statusDiv.textContent = '❌ Error saving';
                    statusDiv.style.color = '#ef4444';
                }}
            }})
            .catch(error => {{
                console.error('Error:', error);
                statusDiv.textContent = '❌ Error saving';
                statusDiv.style.color = '#ef4444';
            }});
        }});
        
        // Load business info on page load
        loadBusinessInfo();
        
        // Auto refresh every 30 seconds
        setTimeout(() => {{
            window.location.reload();
        }}, 30000);
    </script>
</body>
</html>
    """
    
    return html_content

@app.route('/dashboard-react')
def dashboard_react():
    """Serve the React dashboard for testing"""
    try:
        logger.info("📊 React dashboard accessed")
        return send_from_directory('demo3/static', 'index.html')
    except Exception as e:
        logger.error(f"❌ Error serving React dashboard: {e}")
        return f"React dashboard error: {str(e)}", 500

@app.route('/assets/<path:filename>')
def dashboard_assets(filename):
    """Serve dashboard assets"""
    try:
        logger.info(f"🎨 Asset requested: {filename}")
        return send_from_directory('demo3/static/assets', filename)
    except Exception as e:
        logger.error(f"❌ Error serving asset {filename}: {e}")
        return "Asset not found", 404

@app.route('/test-dashboard')
def test_dashboard():
    """Test dashboard connectivity"""
    try:
        return send_from_directory('.', 'test_dashboard.html')
    except Exception as e:
        logger.error(f"❌ Error serving test dashboard: {e}")
        return f"Test dashboard error: {str(e)}", 500

# Calendar API Endpoints
@app.route('/api/calendar/connect/<provider>')
def connect_calendar(provider):
    """Start OAuth flow for calendar provider"""
    if provider == 'google':
        return redirect_to_google_oauth()
    elif provider == 'microsoft':
        return redirect_to_microsoft_oauth()
    elif provider == 'apple':
        return jsonify({'message': 'Apple Calendar integration requires manual setup. Please contact support.'}), 200
    else:
        return jsonify({'error': 'Unsupported calendar provider'}), 400

def redirect_to_google_oauth():
    """Redirect to Google OAuth"""
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
    if not google_client_id:
        return jsonify({'error': 'Google Calendar integration not configured'}), 500
    
    google_redirect_uri = request.url_root + 'api/calendar/google/callback'
    oauth_url = f"https://accounts.google.com/o/oauth2/v2/auth?" \
                f"client_id={google_client_id}&" \
                f"redirect_uri={google_redirect_uri}&" \
                f"scope=https://www.googleapis.com/auth/calendar&" \
                f"response_type=code&" \
                f"access_type=offline"
    
    return redirect(oauth_url)

def redirect_to_microsoft_oauth():
    """Redirect to Microsoft OAuth"""
    microsoft_client_id = os.environ.get('MICROSOFT_CLIENT_ID')
    if not microsoft_client_id:
        return jsonify({'error': 'Microsoft Calendar integration not configured'}), 500
    
    microsoft_redirect_uri = request.url_root + 'api/calendar/microsoft/callback'
    oauth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?" \
                f"client_id={microsoft_client_id}&" \
                f"redirect_uri={microsoft_redirect_uri}&" \
                f"scope=https://graph.microsoft.com/calendars.readwrite&" \
                f"response_type=code&" \
                f"response_mode=query"
    
    return redirect(oauth_url)

@app.route('/api/calendar/google/callback')
def google_oauth_callback():
    """Handle Google OAuth callback"""
    code = request.args.get('code')
    if not code:
        return redirect('/dashboard?error=google_auth_failed')
    
    # Exchange code for tokens
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
    google_client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    google_redirect_uri = request.url_root + 'api/calendar/google/callback'
    
    token_data = {
        'code': code,
        'client_id': google_client_id,
        'client_secret': google_client_secret,
        'redirect_uri': google_redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    try:
        response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
        if response.status_code == 200:
            tokens = response.json()
            session['google_calendar_tokens'] = tokens
            logger.info("✅ Google Calendar connected successfully")
            return redirect('/dashboard?success=google_connected')
        else:
            logger.error(f"❌ Google OAuth failed: {response.text}")
            return redirect('/dashboard?error=google_auth_failed')
    except Exception as e:
        logger.error(f"❌ Google OAuth error: {e}")
        return redirect('/dashboard?error=google_auth_failed')

@app.route('/api/calendar/microsoft/callback')
def microsoft_oauth_callback():
    """Handle Microsoft OAuth callback"""
    code = request.args.get('code')
    if not code:
        return redirect('/dashboard?error=microsoft_auth_failed')
    
    # Exchange code for tokens
    microsoft_client_id = os.environ.get('MICROSOFT_CLIENT_ID')
    microsoft_client_secret = os.environ.get('MICROSOFT_CLIENT_SECRET')
    microsoft_redirect_uri = request.url_root + 'api/calendar/microsoft/callback'
    
    token_data = {
        'code': code,
        'client_id': microsoft_client_id,
        'client_secret': microsoft_client_secret,
        'redirect_uri': microsoft_redirect_uri,
        'grant_type': 'authorization_code',
        'scope': 'https://graph.microsoft.com/calendars.readwrite'
    }
    
    try:
        response = requests.post('https://login.microsoftonline.com/common/oauth2/v2.0/token', data=token_data)
        if response.status_code == 200:
            tokens = response.json()
            session['microsoft_calendar_tokens'] = tokens
            logger.info("✅ Microsoft Calendar connected successfully")
            return redirect('/dashboard?success=microsoft_connected')
        else:
            logger.error(f"❌ Microsoft OAuth failed: {response.text}")
            return redirect('/dashboard?error=microsoft_auth_failed')
    except Exception as e:
        logger.error(f"❌ Microsoft OAuth error: {e}")
        return redirect('/dashboard?error=microsoft_auth_failed')

@app.route('/api/appointments', methods=['GET'])
def get_appointments():
    """API endpoint to get appointments for voice assistant"""
    phone_number = request.args.get('phone')
    if not phone_number:
        return jsonify({'error': 'Phone number required'}), 400
    
    user = User.query.filter_by(phone_number=phone_number).first()
    if not user:
        return jsonify({'appointments': []})
    
    appointments = Appointment.query.filter_by(user_id=user.id).all()
    return jsonify({
        'appointments': [{
            'id': apt.id,
            'title': apt.title,
            'start_time': apt.start_time.isoformat(),
            'end_time': apt.end_time.isoformat(),
            'status': apt.status
        } for apt in appointments]
    })

@app.route('/api/appointments', methods=['POST'])
def create_appointment():
    """API endpoint to create appointment from voice assistant"""
    data = request.json
    phone_number = data.get('phone_number')
    
    if not phone_number:
        return jsonify({'error': 'Phone number required'}), 400
    
    try:
        # Get or create user
        user = User.query.filter_by(phone_number=phone_number).first()
        if not user:
            user = User(phone_number=phone_number)
            db.session.add(user)
            db.session.commit()
        
        # Create appointment
        appointment = Appointment(
            user_id=user.id,
            title=data.get('title', 'Voice Scheduled Appointment'),
            description=data.get('description', ''),
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']),
            calendar_provider=data.get('calendar_provider', 'internal'),
            call_sid=data.get('call_sid'),
            scheduled_via_voice=True
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        logger.info(f"✅ Created appointment {appointment.id} for {phone_number}")
        
        return jsonify({
            'success': True,
            'appointment_id': appointment.id,
            'message': 'Appointment scheduled successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Error creating appointment: {e}")
        return jsonify({'error': 'Failed to create appointment'}), 500


@app.route('/api/call-logs', methods=['POST'])
def save_call_log():
    """Save call log from voice assistant"""
    try:
        data = request.json
        call_sid = data.get('call_sid')
        
        if not call_sid:
            return jsonify({'error': 'Call SID required'}), 400
        
        # Check if call log already exists
        call_log = CallLog.query.filter_by(call_sid=call_sid).first()
        
        if not call_log:
            call_log = CallLog(
                call_sid=call_sid,
                from_number=data.get('from_number', ''),
                to_number=data.get('to_number', ''),
                call_status=data.get('call_status', 'in-progress')
            )
            db.session.add(call_log)
        
        # Update fields
        if data.get('call_status'):
            call_log.call_status = data['call_status']
        if data.get('call_duration'):
            call_log.call_duration = data['call_duration']
        if data.get('transcript'):
            call_log.transcript = data['transcript']
        if data.get('recording_url'):
            call_log.recording_url = data['recording_url']
        if data.get('summary'):
            call_log.summary = data['summary']
        if data.get('appointment_scheduled'):
            call_log.appointment_scheduled = data['appointment_scheduled']
        if data.get('end_time'):
            call_log.end_time = datetime.fromisoformat(data['end_time'])
        
        # Try to link to user if phone number exists
        if call_log.from_number:
            user = User.query.filter_by(phone_number=call_log.from_number).first()
            if user:
                call_log.user_id = user.id
        
        db.session.commit()
        
        logger.info(f"✅ Call log saved for {call_sid}")
        return jsonify({'success': True, 'message': 'Call log saved successfully'})
        
    except Exception as e:
        logger.error(f"❌ Error saving call log: {e}")
        return jsonify({'error': 'Failed to save call log'}), 500


@app.route('/api/demo-data', methods=['POST'])
def create_demo_data():
    """Create demo call logs for testing"""
    try:
        from datetime import timedelta
        import random
        
        # Check if demo data already exists
        if CallLog.query.count() > 0:
            return jsonify({'message': 'Demo data already exists'}), 200
        
        # Sample call data
        demo_calls = [
            {
                'call_sid': 'CA1234567890abcdef1234567890abcdef',
                'from_number': '+15551234567',
                'to_number': '+18444356005',
                'call_status': 'completed',
                'call_duration': 245,
                'transcript': 'Hi, I\'d like to schedule an appointment for next week. I\'m interested in your consulting services. Can you tell me more about your pricing? That sounds good, let\'s book for Tuesday at 2 PM.',
                'start_time': datetime.utcnow() - timedelta(hours=2),
                'end_time': datetime.utcnow() - timedelta(hours=2) + timedelta(seconds=245),
                'summary': 'Customer inquiry about consulting services, appointment scheduled for Tuesday 2 PM',
                'appointment_scheduled': True
            },
            {
                'call_sid': 'CA2234567890abcdef1234567890abcdef',
                'from_number': '+15559876543',
                'to_number': '+18444356005',
                'call_status': 'completed',
                'call_duration': 125,
                'transcript': 'Hello, what are your business hours? I see, thank you. And what services do you offer? Okay, I\'ll call back later to discuss more.',
                'start_time': datetime.utcnow() - timedelta(hours=5),
                'end_time': datetime.utcnow() - timedelta(hours=5) + timedelta(seconds=125),
                'summary': 'General inquiry about business hours and services',
                'appointment_scheduled': False
            },
            {
                'call_sid': 'CA3234567890abcdef1234567890abcdef',
                'from_number': '+15555678901',
                'to_number': '+18444356005',
                'call_status': 'completed',
                'call_duration': 67,
                'transcript': 'Hi, I\'m calling to confirm my appointment tomorrow. Yes, that\'s right. See you then!',
                'start_time': datetime.utcnow() - timedelta(hours=1),
                'end_time': datetime.utcnow() - timedelta(hours=1) + timedelta(seconds=67),
                'summary': 'Appointment confirmation call',
                'appointment_scheduled': False
            }
        ]
        
        for call_data in demo_calls:
            call_log = CallLog(**call_data)
            db.session.add(call_log)
        
        db.session.commit()
        
        logger.info("✅ Demo call logs created")
        return jsonify({'success': True, 'message': 'Demo data created successfully'})
        
    except Exception as e:
        logger.error(f"❌ Error creating demo data: {e}")
        return jsonify({'error': 'Failed to create demo data'}), 500

# HTML Templates
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - VoiceAI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .login-container { background: white; padding: 2rem; border-radius: 1rem; box-shadow: 0 20px 40px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
        .logo { text-align: center; margin-bottom: 2rem; }
        .logo h1 { color: #272F7C; font-size: 2rem; font-weight: bold; }
        .form-group { margin-bottom: 1.5rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; color: #374151; font-weight: 500; }
        .form-control { width: 100%; padding: 0.75rem; border: 1px solid #d1d5db; border-radius: 0.5rem; font-size: 1rem; transition: border-color 0.2s; }
        .form-control:focus { outline: none; border-color: #272F7C; box-shadow: 0 0 0 3px rgba(39, 47, 124, 0.1); }
        .btn { width: 100%; padding: 0.75rem; background: #272F7C; color: white; border: none; border-radius: 0.5rem; font-size: 1rem; font-weight: 500; cursor: pointer; transition: background 0.2s; }
        .btn:hover { background: #1e2654; }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .google-btn { background: #4285f4; margin-top: 1rem; }
        .google-btn:hover { background: #357ae8; }
        .divider { text-align: center; margin: 1.5rem 0; color: #9ca3af; }
        .register-link { text-align: center; margin-top: 1.5rem; }
        .register-link a { color: #272F7C; text-decoration: none; font-weight: 500; }
        .alert { padding: 0.75rem; border-radius: 0.5rem; margin-bottom: 1rem; }
        .alert-error { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
        .alert-success { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1>Voice<span style="color: #3b82f6;">AI</span></h1>
            <p style="color: #6b7280; margin-top: 0.5rem;">Sign in to your account</p>
        </div>
        
        <div id="messages"></div>
        
        <form id="loginForm">
            <div class="form-group">
                <label for="username">Username or Email</label>
                <input type="text" id="username" name="username" class="form-control" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" class="form-control" required>
            </div>
            
            <button type="submit" class="btn">Sign In</button>
        </form>
        
        <div class="divider">or</div>
        
        <a href="/auth/google" class="btn google-btn" style="text-decoration: none; display: block; text-align: center;">
            Continue with Google
        </a>
        
        <div class="register-link">
            Don't have an account? <a href="/auth/register">Sign up</a>
        </div>
    </div>
    
    <script>
        document.getElementById('loginForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');
            const messagesDiv = document.getElementById('messages');
            
            submitBtn.disabled = true;
            submitBtn.textContent = 'Signing in...';
            
            fetch('/auth/login', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    messagesDiv.innerHTML = '<div class="alert alert-success">' + data.message + '</div>';
                    setTimeout(() => {
                        window.location.href = data.redirect;
                    }, 1000);
                } else {
                    messagesDiv.innerHTML = '<div class="alert alert-error">' + data.error + '</div>';
                }
            })
            .catch(error => {
                messagesDiv.innerHTML = '<div class="alert alert-error">Login failed. Please try again.</div>';
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Sign In';
            });
        });
    </script>
</body>
</html>
'''

REGISTER_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register - VoiceAI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .register-container { background: white; padding: 2rem; border-radius: 1rem; box-shadow: 0 20px 40px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
        .logo { text-align: center; margin-bottom: 2rem; }
        .logo h1 { color: #272F7C; font-size: 2rem; font-weight: bold; }
        .form-group { margin-bottom: 1.5rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; color: #374151; font-weight: 500; }
        .form-control { width: 100%; padding: 0.75rem; border: 1px solid #d1d5db; border-radius: 0.5rem; font-size: 1rem; transition: border-color 0.2s; }
        .form-control:focus { outline: none; border-color: #272F7C; box-shadow: 0 0 0 3px rgba(39, 47, 124, 0.1); }
        .btn { width: 100%; padding: 0.75rem; background: #272F7C; color: white; border: none; border-radius: 0.5rem; font-size: 1rem; font-weight: 500; cursor: pointer; transition: background 0.2s; }
        .btn:hover { background: #1e2654; }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .login-link { text-align: center; margin-top: 1.5rem; }
        .login-link a { color: #272F7C; text-decoration: none; font-weight: 500; }
        .alert { padding: 0.75rem; border-radius: 0.5rem; margin-bottom: 1rem; }
        .alert-error { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
        .alert-success { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }
    </style>
</head>
<body>
    <div class="register-container">
        <div class="logo">
            <h1>Voice<span style="color: #3b82f6;">AI</span></h1>
            <p style="color: #6b7280; margin-top: 0.5rem;">Create your account</p>
        </div>
        
        <div id="messages"></div>
        
        <form id="registerForm">
            <div class="form-group">
                <label for="name">Full Name</label>
                <input type="text" id="name" name="name" class="form-control">
            </div>
            
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" class="form-control" required>
            </div>
            
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" name="email" class="form-control" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password (min 6 characters)</label>
                <input type="password" id="password" name="password" class="form-control" required minlength="6">
            </div>
            
            <button type="submit" class="btn">Create Account</button>
        </form>
        
        <div class="login-link">
            Already have an account? <a href="/auth/login">Sign in</a>
        </div>
    </div>
    
    <script>
        document.getElementById('registerForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');
            const messagesDiv = document.getElementById('messages');
            
            submitBtn.disabled = true;
            submitBtn.textContent = 'Creating account...';
            
            fetch('/auth/register', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    messagesDiv.innerHTML = '<div class="alert alert-success">' + data.message + '</div>';
                    setTimeout(() => {
                        window.location.href = data.redirect;
                    }, 2000);
                } else {
                    messagesDiv.innerHTML = '<div class="alert alert-error">' + data.error + '</div>';
                }
            })
            .catch(error => {
                messagesDiv.innerHTML = '<div class="alert alert-error">Registration failed. Please try again.</div>';
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Create Account';
            });
        });
    </script>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - VoiceAI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; }
        .header { background: white; border-bottom: 1px solid #e5e7eb; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }
        .logo { color: #272F7C; font-size: 1.5rem; font-weight: bold; }
        .user-menu { display: flex; align-items: center; gap: 1rem; }
        .user-info { display: flex; align-items: center; gap: 0.5rem; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        
        /* Tab Navigation */
        .tab-nav { background: white; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 2rem; }
        .tab-list { display: flex; border-bottom: 1px solid #e5e7eb; }
        .tab-button { padding: 1rem 1.5rem; background: none; border: none; cursor: pointer; font-weight: 500; color: #6b7280; border-bottom: 2px solid transparent; transition: all 0.2s; }
        .tab-button.active { color: #272F7C; border-bottom-color: #272F7C; background: #f8fafc; }
        .tab-button:hover { color: #272F7C; background: #f8fafc; }
        .tab-content { display: none; padding: 2rem; }
        .tab-content.active { display: block; }
        
        /* Stats and other existing styles */
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .stat-card { background: white; padding: 1.5rem; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .stat-value { font-size: 2rem; font-weight: bold; color: #272F7C; }
        .stat-label { color: #6b7280; margin-top: 0.5rem; }
        .section { background: white; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 2rem; }
        .section-header { padding: 1.5rem; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center; }
        .section-title { font-size: 1.25rem; font-weight: 600; }
        .section-content { padding: 1.5rem; }
        .btn { padding: 0.5rem 1rem; background: #272F7C; color: white; border: none; border-radius: 0.375rem; cursor: pointer; text-decoration: none; display: inline-block; font-weight: 500; }
        .btn:hover { background: #1e2654; }
        .btn-outline { background: transparent; color: #272F7C; border: 1px solid #272F7C; }
        .btn-outline:hover { background: #272F7C; color: white; }
        .btn-danger { background: #dc2626; }
        .btn-danger:hover { background: #b91c1c; }
        .table { width: 100%; border-collapse: collapse; }
        .table th, .table td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #e5e7eb; }
        .table th { background: #f9fafb; font-weight: 600; }
        .number-card { border: 1px solid #e5e7eb; border-radius: 0.5rem; padding: 1rem; margin-bottom: 1rem; }
        .number-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
        .number-phone { font-size: 1.125rem; font-weight: 600; color: #272F7C; }
        .number-details { color: #6b7280; font-size: 0.875rem; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; }
        .modal-content { background: white; margin: 5% auto; padding: 2rem; border-radius: 0.5rem; max-width: 500px; }
        .close { float: right; font-size: 1.5rem; cursor: pointer; }
        .form-group { margin-bottom: 1rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
        .form-control { width: 100%; padding: 0.5rem; border: 1px solid #d1d5db; border-radius: 0.375rem; }
        .alert { padding: 0.75rem; border-radius: 0.375rem; margin-bottom: 1rem; }
        .alert-success { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }
        .alert-error { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">Voice<span style="color: #3b82f6;">AI</span> Dashboard</div>
        <div class="user-menu">
            <div class="user-info">
                {% if user.avatar_url %}
                <img src="{{ user.avatar_url }}" alt="Avatar" style="width: 32px; height: 32px; border-radius: 50%;">
                {% endif %}
                <span>{{ user.name or user.username }}</span>
            </div>
            <a href="/auth/logout" class="btn btn-outline">Logout</a>
        </div>
    </div>
    
    <div class="container">
        <!-- Tab Navigation -->
        <div class="tab-nav">
            <div class="tab-list">
                <button class="tab-button active" onclick="switchTab('dashboard')">Dashboard</button>
                <button class="tab-button" onclick="switchTab('settings')">Settings</button>
            </div>
            
            <!-- Dashboard Tab Content -->
            <div id="dashboard-tab" class="tab-content active">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{{ stats.active_numbers }}</div>
                        <div class="stat-label">Active Numbers</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{{ stats.total_calls }}</div>
                        <div class="stat-label">Total Calls</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{{ stats.total_sms }}</div>
                        <div class="stat-label">Total SMS</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${{ "%.2f"|format(stats.total_cost) }}</div>
                        <div class="stat-label">Monthly Cost</div>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                    <div class="section">
                        <div class="section-header">
                            <div class="section-title">Recent Calls</div>
                        </div>
                        <div class="section-content">
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>From</th>
                                        <th>Time</th>
                                        <th>Duration</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% if recent_calls %}
                                        {% for call in recent_calls %}
                                        <tr>
                                            <td>{{ call.from_number }}</td>
                                            <td>{{ call.start_time.strftime('%b %d, %I:%M %p') if call.start_time else 'N/A' }}</td>
                                            <td>{% if call.call_duration %}{{ (call.call_duration//60)|int }}:{{ '%02d'|format(call.call_duration%60) }}{% else %}N/A{% endif %}</td>
                                            <td><span style="color: {% if call.call_status == 'completed' %}#10b981{% elif call.call_status == 'in-progress' %}#3b82f6{% else %}#ef4444{% endif %};">{{ call.call_status.title() if call.call_status else 'Unknown' }}</span></td>
                                        </tr>
                                        {% endfor %}
                                    {% else %}
                                        <tr><td colspan="4" style="text-align: center; color: #9ca3af;">No calls yet</td></tr>
                                    {% endif %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div class="section">
                        <div class="section-header">
                            <div class="section-title">Recent SMS</div>
                        </div>
                        <div class="section-content">
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>From</th>
                                        <th>Time</th>
                                        <th>Message</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% if recent_sms %}
                                        {% for sms in recent_sms %}
                                        <tr>
                                            <td>{{ sms.from_number }}</td>
                                            <td>{{ sms.created_at.strftime('%b %d, %I:%M %p') }}</td>
                                            <td>{{ sms.body[:50] + '...' if sms.body and sms.body|length > 50 else sms.body or 'No content' }}</td>
                                        </tr>
                                        {% endfor %}
                                    {% else %}
                                        <tr><td colspan="3" style="text-align: center; color: #9ca3af;">No SMS yet</td></tr>
                                    {% endif %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Settings Tab Content -->
            <div id="settings-tab" class="tab-content">
                <div class="section">
                    <div class="section-header">
                        <div class="section-title">Manage Phone Numbers</div>
                        <button onclick="openPurchaseModal()" class="btn">Buy New Number</button>
                    </div>
                    <div class="section-content">
                        {% if twilio_numbers %}
                            {% for number in twilio_numbers %}
                            <div class="number-card">
                                <div class="number-header">
                                    <div class="number-phone">{{ number.phone_number }}</div>
                                    <button onclick="releaseNumber({{ number.id }})" class="btn btn-danger">Release</button>
                                </div>
                                <div class="number-details">
                                    {{ number.friendly_name or 'No name set' }} • 
                                    ${{ "%.2f"|format(number.monthly_cost or 0) }}/month • 
                                    Purchased {{ number.purchased_at.strftime('%b %d, %Y') }}
                                </div>
                            </div>
                            {% endfor %}
                        {% else %}
                            <p style="text-align: center; color: #6b7280; padding: 2rem;">
                                No numbers yet. <button onclick="openPurchaseModal()" class="btn">Buy your first number</button>
                            </p>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Purchase Number Modal -->
    <div id="purchaseModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closePurchaseModal()">&times;</span>
            <h2>Buy New Number</h2>
            <div id="modalMessages"></div>
            
            <div class="form-group">
                <label for="areaCode">Area Code</label>
                <input type="text" id="areaCode" class="form-control" value="555" placeholder="e.g., 555">
            </div>
            
            <button onclick="searchNumbers()" class="btn">Search Available Numbers</button>
            
            <div id="availableNumbers" style="margin-top: 1rem;"></div>
        </div>
    </div>
    
    <script>
        function openPurchaseModal() {
            document.getElementById('purchaseModal').style.display = 'block';
        }
        
        function closePurchaseModal() {
            document.getElementById('purchaseModal').style.display = 'none';
            document.getElementById('availableNumbers').innerHTML = '';
        }
        
        function searchNumbers() {
            const areaCode = document.getElementById('areaCode').value;
            const messagesDiv = document.getElementById('modalMessages');
            
            fetch(`/api/twilio/numbers/available?area_code=${areaCode}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    let html = '<h3>Available Numbers:</h3>';
                    data.numbers.forEach(number => {
                        html += `
                        <div style="border: 1px solid #e5e7eb; padding: 1rem; margin: 0.5rem 0; border-radius: 0.375rem;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong>${number.phone_number}</strong><br>
                                    <small>${number.cost}</small>
                                </div>
                                <button onclick="purchaseNumber('${number.phone_number}')" class="btn">Buy</button>
                            </div>
                        </div>`;
                    });
                    document.getElementById('availableNumbers').innerHTML = html;
                } else {
                    messagesDiv.innerHTML = '<div class="alert alert-error">' + data.error + '</div>';
                }
            });
        }
        
        function purchaseNumber(phoneNumber) {
            const messagesDiv = document.getElementById('modalMessages');
            
            fetch('/api/twilio/numbers/purchase', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({phone_number: phoneNumber})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    messagesDiv.innerHTML = '<div class="alert alert-success">' + data.message + '</div>';
                    setTimeout(() => {
                        location.reload();
                    }, 2000);
                } else {
                    messagesDiv.innerHTML = '<div class="alert alert-error">' + data.error + '</div>';
                }
            });
        }
        
        function releaseNumber(numberId) {
            if (confirm('Are you sure you want to release this number? This action cannot be undone.')) {
                fetch(`/api/twilio/numbers/${numberId}/release`, {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('Failed to release number: ' + data.error);
                    }
                });
            }
        }
        
        // Tab switching functionality
        function switchTab(tabName) {
            // Remove active classes from all tabs and content
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked tab and its content
            document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
            document.getElementById(`${tabName}-tab`).classList.add('active');
            
            // Update URL hash
            window.location.hash = tabName === 'dashboard' ? '' : tabName;
        }
        
        // Handle URL hash on page load
        function handleUrlHash() {
            const hash = window.location.hash.replace('#', '');
            if (hash === 'settings') {
                switchTab('settings');
            } else {
                switchTab('dashboard');
            }
        }
        
        // Listen for hash changes
        window.addEventListener('hashchange', handleUrlHash);
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', handleUrlHash);
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('purchaseModal');
            if (event.target == modal) {
                closePurchaseModal();
            }
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    # Initialize database
    with app.app_context():
        db.create_all()
        logger.info("✅ Database initialized")
    
    port = int(os.environ.get('PORT', 5001))
    logger.info(f"🚀 Starting Simple Voice Agent App on port {port}")
    logger.info(f"🎤 Voice model: aura-2-amalthea-en")
    logger.info(f"🔗 WebSocket bridge should be running on port 8768")
    logger.info(f"📅 Calendar integration available at /dashboard")
    
    app.run(host='0.0.0.0', port=port, debug=False)
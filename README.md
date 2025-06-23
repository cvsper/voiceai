# Voice AI Assistant MVP

A comprehensive Flask-based voice AI assistant that handles incoming calls, transcrites conversations in real-time, detects user intent, and performs actions like booking appointments and triggering CRM workflows.

## Features

- **Call Handling**: Receive and process incoming calls via Twilio
- **Real-time Transcription**: Stream audio to Deepgram for live transcription
- **Intent Detection**: Use GPT-4 to understand customer intent and respond naturally
- **Appointment Booking**: Integrate with Google Calendar for scheduling
- **CRM Integration**: Trigger webhook events for external CRM systems
- **Call Monitoring**: Monitor human-to-human conversations
- **Comprehensive Logging**: Store all call data, transcripts, and interactions

## Tech Stack

- **Backend**: Flask, SQLAlchemy, SQLite
- **Voice**: Twilio for call handling
- **Transcription**: Deepgram for real-time speech-to-text
- **AI**: OpenAI GPT-4 for intent detection and responses
- **TTS**: ElevenLabs for text-to-speech
- **Calendar**: Google Calendar API
- **Deployment**: Railway/Render compatible

## Project Structure

```
voiceai/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── models.py             # Database models
├── requirements.txt      # Python dependencies
├── services/            # Service layer
│   ├── twilio_service.py
│   ├── deepgram_service.py
│   ├── openai_service.py
│   ├── elevenlabs_service.py
│   ├── calendar_service.py
│   └── crm_service.py
├── utils/               # Utility functions
│   ├── auth.py
│   └── errors.py
└── deployment files
```

## Quick Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required API keys:
- **Twilio**: Account SID, Auth Token, Phone Number
- **Deepgram**: API Key
- **OpenAI**: API Key (GPT-4 access required)
- **ElevenLabs**: API Key and Voice ID
- **Google Calendar**: Client ID, Client Secret (optional)

### 3. Database Setup

```bash
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all()"
```

### 4. Run Locally

```bash
python app.py
```

The application will run on `http://localhost:5000`

## API Endpoints

### Webhooks (for Twilio)
- `POST /webhooks/voice` - Handle incoming voice calls
- `POST /webhooks/transcribe` - Process transcription results
- `POST /webhooks/recording` - Handle call recordings

### API Endpoints (require authentication)
- `GET /api/calls` - List all calls with pagination
- `GET /api/calls/<id>` - Get detailed call information
- `POST /api/book-appointment` - Book a new appointment
- `GET /api/appointments` - List all appointments
- `POST /api/crm-trigger` - Trigger custom CRM webhook
- `GET /api/available-slots?date=YYYY-MM-DD` - Get available appointment slots

### Utility
- `GET /health` - Health check endpoint

## Authentication

The API uses HTTP Basic Authentication. Set your credentials in the environment:

```
AUTH_USERNAME=admin
AUTH_PASSWORD=your-secure-password
```

## Deployment

### Railway Deployment

1. Connect your repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically with `railway.toml` configuration

### Render Deployment

1. Connect repository to Render
2. Set environment variables
3. Use the `Procfile` for process configuration

### Environment Variables for Production

```bash
# Flask
FLASK_ENV=production
SECRET_KEY=your-production-secret-key
DATABASE_URL=your-database-url

# API Keys (as described above)
TWILIO_ACCOUNT_SID=...
DEEPGRAM_API_KEY=...
OPENAI_API_KEY=...
# ... etc

# Authentication
AUTH_USERNAME=admin
AUTH_PASSWORD=secure-password

# Base URL
BASE_URL=https://your-domain.com
```

## Twilio Configuration

### Webhook URLs
Configure these URLs in your Twilio console:

- **Voice URL**: `https://your-domain.com/webhooks/voice`
- **Status Callback**: `https://your-domain.com/webhooks/voice`
- **Recording Callback**: `https://your-domain.com/webhooks/recording`
- **Transcription Callback**: `https://your-domain.com/webhooks/transcribe`

### Required Twilio Features
- Voice calls
- Recording
- Transcription (optional, Deepgram provides better results)

## Google Calendar Setup (Optional)

1. Create a Google Cloud Project
2. Enable the Google Calendar API
3. Create credentials (OAuth 2.0 or Service Account)
4. Set the credentials in your environment variables

For service account authentication, download the JSON key and reference it in your code.

## CRM Integration

The system supports webhook-based CRM integration. Configure webhook URLs for different events:

- Call started
- Call ended
- Intent detected
- Appointment booked

Example webhook payload:
```json
{
  "event": "appointment_booked",
  "timestamp": "2024-01-15T10:30:00Z",
  "appointment": {
    "id": 123,
    "title": "Customer Consultation",
    "start_time": "2024-01-20T14:00:00Z",
    "attendee_email": "customer@example.com"
  },
  "call_data": {
    "call_sid": "CA1234567890",
    "from_number": "+1234567890"
  }
}
```

## Monitoring and Logs

- All calls, transcripts, and interactions are stored in the database
- Error logging is configured for debugging
- Health check endpoint for monitoring uptime
- Call summaries generated automatically with GPT-4

## Security Considerations

- Use HTTPS in production
- Secure your API keys and environment variables
- Implement rate limiting for production
- Review and audit webhook endpoints
- Use strong authentication credentials

## Troubleshooting

### Common Issues

1. **Twilio webhooks not working**
   - Ensure your server is accessible from the internet
   - Check webhook URLs in Twilio console
   - Verify HTTPS is properly configured

2. **Deepgram transcription issues**
   - Verify API key is correct
   - Check audio format compatibility
   - Monitor API quota and usage

3. **OpenAI API errors**
   - Ensure you have GPT-4 access
   - Check API key and billing status
   - Monitor rate limits

4. **Google Calendar not working**
   - Verify OAuth credentials
   - Check API permissions and scopes
   - Ensure proper redirect URIs

## Performance Tips

- Use connection pooling for database
- Implement caching for frequently accessed data
- Monitor API usage and implement rate limiting
- Use async processing for webhook calls
- Optimize database queries with proper indexing

## Support

For issues and questions:
1. Check the logs for error messages
2. Verify all API keys are correctly configured
3. Test individual services in isolation
4. Monitor webhook delivery in respective service dashboards

## License

This is a proprietary MVP for commercial use.
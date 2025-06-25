# Voice AI Assistant with Deepgram Voice Agent

A production-ready voice AI assistant using Deepgram Voice Agent API with Flask backend and React dashboard.

## Features

- **Phone System**: Twilio integration for incoming calls
- **Voice AI**: Deepgram Voice Agent with function calling
- **Appointments**: Book, manage, and track appointments
- **CRM Integration**: Webhook notifications to CRM systems
- **Dashboard**: Real-time monitoring and analytics
- **Database**: SQLite for MVP, PostgreSQL for production

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- Deepgram API key
- Twilio account with phone number
- ngrok (for local development)

### Environment Setup

1. Copy environment variables:
```bash
cp .env.example .env
```

2. Configure your `.env` file:
```env
DEEPGRAM_API_KEY=your_deepgram_api_key
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890
CRM_WEBHOOK_URL=https://your-crm.com/webhook
```

### Backend Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize database:
```bash
python -c "from app import app; from models import db; app.app_context().push(); db.create_all()"
```

3. Run the application:
```bash
python app.py
```

### Frontend Setup

1. Navigate to demo folder:
```bash
cd demo
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

### Twilio Configuration

1. Start ngrok to expose your local server:
```bash
ngrok http 5000
```

2. Configure your Twilio phone number webhook:
   - Voice webhook URL: `https://your-ngrok-url.ngrok.io/webhooks/voice`
   - HTTP method: POST

## API Endpoints

### Dashboard
- `GET /api/dashboard/metrics` - Get dashboard metrics
- `GET /api/dashboard/call-trends` - Get call trends
- `GET /api/dashboard/live-stats` - Get live statistics

### Calls
- `GET /api/calls` - List calls with pagination
- `GET /api/calls/{id}` - Get specific call details
- `GET /api/calls/search` - Search calls

### Appointments  
- `GET /api/appointments` - List appointments
- `GET /api/appointments/{id}` - Get appointment details
- `PUT /api/appointments/{id}` - Update appointment
- `GET /api/appointments/availability/{date}` - Check availability

### System
- `GET /api/health` - Health check
- `POST /api/test-call` - Make test call
- `POST /api/test-crm` - Test CRM webhook

## Voice Agent Configuration

The Voice Agent is configured with:
- **Model**: nova-2 (Deepgram's latest model)
- **Voice**: aura-asteria-en (professional female voice)
- **Functions**: Appointment booking, availability checking, CRM integration

### Function Calling

The Voice Agent can execute these functions:
- `book_appointment(name, phone, date, time, service)`
- `get_availability(date)`
- `cancel_appointment(reference_id)`
- `trigger_crm_webhook(event_type, data)`

## Deployment

### Railway

1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically on push

### Render

1. Create new Web Service
2. Connect GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn app:app`
5. Add environment variables

### Environment Variables for Production

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@host:port/db
DEEPGRAM_API_KEY=your_deepgram_api_key
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890
CRM_WEBHOOK_URL=https://your-crm.com/webhook
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Twilio PSTN   │    │   Flask Backend  │    │ React Dashboard │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │   Phone     │─────▶│ │   Webhook    │ │    │ │  Analytics  │ │
│ │   Calls     │ │    │ │   Handler    │ │    │ │  Dashboard  │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ └─────────────┘ │
│                 │    │        │         │    │        ▲        │
│ ┌─────────────┐ │    │        ▼         │    │        │        │
│ │   Media     │◀─────┤ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │   Stream    │ │    │ │   WebSocket  │ │    │ │     API     │ │
│ └─────────────┘ │    │ │   Bridge     │ │    │ │  Endpoints  │ │
└─────────────────┘    │ └──────────────┘ │    │ └─────────────┘ │
                       │        │         │    └─────────────────┘
┌─────────────────┐    │        ▼         │    
│ Deepgram Voice  │    │ ┌──────────────┐ │    ┌─────────────────┐
│     Agent       │◀───┤ │   Function   │ │    │   Database      │
│                 │    │ │   Calling    │ │───▶│                 │
│ ┌─────────────┐ │    │ └──────────────┘ │    │ ┌─────────────┐ │
│ │    STT      │ │    │        │         │    │ │    Calls    │ │
│ │    TTS      │ │    │        ▼         │    │ │Appointments │ │
│ │   LLM       │ │    │ ┌──────────────┐ │    │ │ Transcripts │ │
│ └─────────────┘ │    │ │     CRM      │ │    │ │   Webhooks  │ │
└─────────────────┘    │ │   Webhook    │ │    │ └─────────────┘ │
                       │ └──────────────┘ │    └─────────────────┘
                       └──────────────────┘    
```

## Testing

### Test the Voice AI

1. Use the dashboard's "Test Call" feature
2. Enter your phone number
3. Click "Test Call"
4. Answer the call and interact with the AI

### Test Function Calling

Try these phrases during a call:
- "I'd like to book an appointment"
- "What times are available tomorrow?"
- "Can you cancel my appointment?"

## Monitoring

The dashboard provides:
- Real-time call metrics
- Appointment statistics
- Conversion rates
- System health monitoring
- Call transcripts and recordings

## Troubleshooting

### Common Issues

1. **WebSocket connection fails**
   - Ensure ngrok is running for local testing
   - Check Twilio webhook configuration

2. **Voice Agent not responding**
   - Verify Deepgram API key
   - Check audio format conversion

3. **Function calls not working**
   - Review function calling logs
   - Verify database connections

### Logs

Check application logs for debugging:
```bash
python app.py  # Shows all application logs
```

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation
3. Test with provided endpoints
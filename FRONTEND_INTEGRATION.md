# Frontend Integration Guide

This guide explains how to integrate the React dashboard frontend with your Flask Voice AI backend.

## Overview

The Voice AI system now includes:
- **Backend**: Flask API with voice processing, transcription, and data management
- **Frontend**: React TypeScript dashboard with authentication and real-time data
- **Integration**: Frontend served directly by Flask with API authentication

## Quick Start

### 1. Build the Frontend

```bash
# Automated build (recommended)
python build_frontend.py

# Manual build
cd demo
npm install
npm run build
cd ..
```

### 2. Configure Environment

Ensure your `.env` file has the correct credentials:

```bash
# Copy example and fill in your keys
cp .env.example .env

# Edit .env with your API keys
AUTH_USERNAME=admin
AUTH_PASSWORD=your-secure-password
```

### 3. Start the Integrated Application

```bash
python app.py
```

The Flask app now serves both:
- **API endpoints**: `/api/*` for backend functionality
- **Frontend**: `/` for the React dashboard

### 4. Access the Dashboard

1. Open browser to: `http://localhost:5000`
2. Login with your credentials (default: admin/password)
3. View real-time call data, metrics, and system status

## Features Integrated

### ✅ Authentication
- Login form with HTTP Basic Auth
- Persistent sessions with localStorage
- Logout functionality
- Protected routes

### ✅ Real-time Dashboard
- Live call metrics (calls today, appointments, duration)
- Performance statistics (answer rate, booking rate, miss rate)
- System status monitoring (Voice AI, Call Recording, Calendar)
- Recent calls table with real data

### ✅ Call Logs
- Paginated call history
- Search by phone number or call ID
- Filter by call status
- Download recordings and view transcripts
- Real-time status updates

### ✅ API Integration
- All components use real Flask API data
- Error handling and loading states
- Automatic credential management
- CORS configured for development

## Technical Architecture

```
Frontend (React/TypeScript)
├── Authentication (LoginForm, AuthContext)
├── API Service (api.ts)
├── Hooks (useApi.ts)
├── Components (Dashboard, CallLogs, etc.)
└── Build Output (demo/dist/)

Flask Backend
├── API Routes (/api/*)
├── Dashboard Routes (/api/dashboard/*)
├── Frontend Serving (/, /*)
└── Authentication (HTTP Basic Auth)
```

## API Endpoints Used by Frontend

### Dashboard APIs
- `GET /api/dashboard/metrics` - Real-time metrics
- `GET /api/dashboard/recent-calls` - Recent call list
- `GET /api/dashboard/system-status` - Service status

### Call Management APIs
- `GET /api/calls` - Paginated call logs
- `GET /api/calls/<id>` - Call details with transcripts
- `GET /api/appointments` - Appointment list
- `POST /api/book-appointment` - Create appointments

### System APIs
- `GET /health` - Health check
- `POST /api/crm-trigger` - Trigger webhooks

## Development Workflow

### Frontend Development
```bash
# Start development server (frontend only)
cd demo
npm run dev
# Opens http://localhost:5173

# Backend must be running at http://localhost:5000
python app.py
```

### Production Build
```bash
# Build and integrate
python build_frontend.py

# Deploy as single Flask app
python app.py
```

## Customization

### Authentication
Update credentials in `/demo/src/services/api.ts`:
```typescript
private credentials = {
  username: 'admin',
  password: 'your-password'
};
```

### API Configuration
Modify base URL in `/demo/src/services/api.ts`:
```typescript
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '' 
  : 'http://localhost:5000';
```

### Styling
The frontend uses Tailwind CSS. Customize in:
- `/demo/tailwind.config.js` - Theme configuration
- `/demo/src/index.css` - Global styles
- Component files - Component-specific styles

## Troubleshooting

### Frontend Not Loading
1. Check if build was successful: `ls demo/dist/`
2. Verify Flask static folder configuration in `app.py`
3. Check browser console for errors

### API Authentication Errors
1. Verify credentials in `.env` file
2. Check Flask app authentication configuration
3. Clear browser localStorage: `localStorage.clear()`

### CORS Issues in Development
1. Ensure CORS origins include development URL
2. Check Flask CORS configuration in `app.py`
3. Use incognito mode to test

### Build Errors
1. Check Node.js version: `node --version` (requires 16+)
2. Clear npm cache: `npm cache clean --force`
3. Delete node_modules and reinstall: `rm -rf node_modules && npm install`

## Production Deployment

### Railway/Render Deployment
The integrated app deploys as a single Flask application:

1. Frontend builds automatically during deployment
2. Flask serves both API and frontend
3. Environment variables configure authentication
4. No separate frontend hosting needed

### Environment Variables for Production
```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-production-secret

# Authentication
AUTH_USERNAME=admin
AUTH_PASSWORD=secure-production-password

# API Keys (your existing configuration)
TWILIO_ACCOUNT_SID=...
DEEPGRAM_API_KEY=...
OPENAI_API_KEY=...
# ... etc
```

## Security Considerations

- ✅ HTTP Basic Authentication implemented
- ✅ Credentials stored securely in environment variables
- ✅ Frontend credentials not exposed in build
- ✅ CORS properly configured
- ⚠️  Consider implementing JWT tokens for production
- ⚠️  Add rate limiting for API endpoints
- ⚠️  Use HTTPS in production

## Support

If you encounter issues:
1. Check the browser console for errors
2. Verify Flask logs for API errors
3. Test API endpoints directly with curl
4. Check network tab for failed requests

The integration provides a complete voice AI dashboard with real-time data, authentication, and production-ready deployment.
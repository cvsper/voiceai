# Twilio Configuration for Voice AI Assistant

## Your Current Setup Status ✅

- **Backend**: Running on http://localhost:5001
- **Frontend**: Running on http://localhost:5173
- **ngrok URL**: `https://b033-2600-1006-a132-82c-cd1a-9762-4bf8-3b0d.ngrok-free.app`
- **Twilio Phone**: +18444356005

## Step 1: Configure Your Twilio Phone Number

1. **Go to Twilio Console**: https://console.twilio.com/

2. **Navigate to Phone Numbers**:
   - Click "Phone Numbers" in the left sidebar
   - Click "Manage" 
   - Click "Active numbers"

3. **Click on your phone number**: +18444356005

4. **Configure Voice Webhook**:
   - In the "Voice" section, set:
   - **Webhook URL**: `https://b033-2600-1006-a132-82c-cd1a-9762-4bf8-3b0d.ngrok-free.app/webhooks/voice`
   - **HTTP Method**: POST
   - **Fallback URL**: (leave blank for now)

5. **Configure Status Callback** (optional):
   - **Status Callback URL**: `https://b033-2600-1006-a132-82c-cd1a-9762-4bf8-3b0d.ngrok-free.app/webhooks/call-status`
   - **HTTP Method**: POST

6. **Save Configuration**: Click "Save"

## Step 2: Test Your Voice AI

### Method 1: Using the Dashboard
1. Open http://localhost:5173
2. Scroll down to "Test Voice AI" section
3. Enter your phone number (e.g., +1234567890)
4. Click "Test Call"
5. Answer your phone and interact with the AI

### Method 2: Call Directly
1. Call your Twilio number: **+18444356005**
2. The AI assistant will answer and greet you
3. Try saying: "I'd like to book an appointment"

## Step 3: Monitor in Real-time

**Dashboard**: http://localhost:5173
- Real-time call metrics
- Appointment bookings
- Call transcripts
- System health

**ngrok Web Interface**: http://localhost:4040
- View webhook requests
- Debug HTTP traffic
- Monitor response times

## Expected AI Behavior

The Voice AI assistant will:
1. **Greet callers** professionally
2. **Understand requests** like:
   - "I want to book an appointment"
   - "What times are available tomorrow?"
   - "Can you help me schedule a meeting?"
3. **Ask for details**:
   - Name
   - Phone number
   - Preferred date/time
   - Service type
4. **Confirm bookings** and provide reference numbers
5. **Send data to CRM** (if webhook configured)

## Troubleshooting

### If calls don't connect:
1. Check that ngrok is running: `curl http://localhost:4040/api/tunnels`
2. Verify Flask backend: `curl http://localhost:5001/api/health`
3. Check Twilio webhook configuration matches ngrok URL

### If AI doesn't respond:
1. Verify Deepgram API key in `.env`
2. Check Flask logs for errors
3. Monitor ngrok web interface for webhook calls

### For webhook debugging:
- **ngrok Web UI**: http://localhost:4040
- **Flask logs**: Check terminal where `python3 app.py` is running
- **Twilio debugger**: https://console.twilio.com/us1/monitor/logs/debugger

## Production Deployment

When ready for production:
1. Deploy to Railway/Render using provided configs
2. Update Twilio webhook to production URL
3. Switch from SQLite to PostgreSQL
4. Enable WebSocket server for real-time audio streaming

## Your Next Steps:
1. ✅ Configure Twilio webhook (Step 1)
2. ✅ Test with dashboard (Step 2) 
3. ✅ Monitor real-time activity (Step 3)
4. 🚀 Start taking real customer calls!

---

**Support**: If you encounter issues, check the troubleshooting section or review the main README.md
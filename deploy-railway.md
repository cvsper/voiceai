# Railway Deployment Guide for Voice AI Assistant

## 🚀 Quick Deploy to Railway

1. **Connect Repository to Railway:**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login to Railway
   railway login
   
   # Deploy from this directory
   railway link
   railway up
   ```

2. **Set Environment Variables in Railway Dashboard:**
   ```
   DEEPGRAM_API_KEY=your_deepgram_api_key
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   TWILIO_PHONE_NUMBER=your_twilio_number
   PORT=5001
   WEBSOCKET_PORT=8767
   ```

3. **Update Twilio Webhook URL:**
   ```
   https://your-app-name.railway.app/webhooks/voice
   ```

## 🔧 Railway Configuration

The `railway.json` file is configured to:
- Run both Flask app (port 5001) and WebSocket server (port 8767)
- Support Deepgram Voice Agent V1 with aura-2-amalthea-en
- Handle real-time audio streaming between Twilio ↔ Deepgram

## 📞 Voice Agent Features

✅ **Actual Deepgram Voice Agent V1**
✅ **aura-2-amalthea-en voice model**
✅ **Real-time WebSocket communication**
✅ **Function calling for appointments**
✅ **Professional dashboard**

## 🎯 Expected Flow

1. Call Twilio number
2. "Hello! Connecting you with our advanced AI assistant..."
3. WebSocket connection to Deepgram Voice Agent V1
4. Natural conversation with aura voice
5. Appointment booking functionality

## 🐛 Troubleshooting

- Check Railway logs for WebSocket connection status
- Verify both ports 5001 and 8767 are accessible
- Ensure environment variables are set correctly
- Monitor Deepgram API usage in dashboard
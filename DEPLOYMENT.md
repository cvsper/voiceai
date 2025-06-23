# Deployment Guide

This guide covers deploying the Voice AI Assistant to Railway and Render.

## Railway Deployment

Railway is the recommended platform for its simplicity and excellent Flask support.

### Step 1: Prepare Your Repository

Ensure these files are in your repository root:
- `railway.toml` ✓
- `requirements.txt` ✓ 
- `Procfile` ✓
- `runtime.txt` ✓

### Step 2: Deploy to Railway

1. **Connect Repository**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login and link project
   railway login
   railway link
   ```

2. **Set Environment Variables**
   ```bash
   railway variables set FLASK_ENV=production
   railway variables set SECRET_KEY=your-production-secret-key
   railway variables set TWILIO_ACCOUNT_SID=your-twilio-sid
   railway variables set TWILIO_AUTH_TOKEN=your-twilio-token
   railway variables set DEEPGRAM_API_KEY=your-deepgram-key
   railway variables set OPENAI_API_KEY=your-openai-key
   railway variables set ELEVENLABS_API_KEY=your-elevenlabs-key
   railway variables set AUTH_USERNAME=admin
   railway variables set AUTH_PASSWORD=secure-password
   ```

3. **Deploy**
   ```bash
   railway up
   ```

4. **Get Your URL**
   ```bash
   railway domain
   ```

### Step 3: Configure Twilio Webhooks

In your Twilio Console, set these webhook URLs:

- **Voice URL**: `https://your-railway-domain.railway.app/webhooks/voice`
- **Status Callback URL**: `https://your-railway-domain.railway.app/webhooks/voice`

## Render Deployment

### Step 1: Create Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository

### Step 2: Configure Service

**Settings:**
- **Environment**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Instance Type**: Starter (for MVP)

### Step 3: Environment Variables

Add these in the Render dashboard:

| Key | Value |
|-----|-------|
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | `your-production-secret-key` |
| `TWILIO_ACCOUNT_SID` | `your-twilio-sid` |
| `TWILIO_AUTH_TOKEN` | `your-twilio-token` |
| `TWILIO_PHONE_NUMBER` | `your-twilio-number` |
| `DEEPGRAM_API_KEY` | `your-deepgram-key` |
| `OPENAI_API_KEY` | `your-openai-key` |
| `ELEVENLABS_API_KEY` | `your-elevenlabs-key` |
| `AUTH_USERNAME` | `admin` |
| `AUTH_PASSWORD` | `secure-password` |

### Step 4: Deploy

Click "Create Web Service" - Render will automatically deploy.

## Post-Deployment Setup

### 1. Test Health Endpoint

```bash
curl https://your-domain.com/health
```

Expected response:
```json
{"status": "healthy", "timestamp": "2024-01-15T10:30:00.000000"}
```

### 2. Configure Twilio Phone Number

In Twilio Console:
1. Go to Phone Numbers → Manage → Active numbers
2. Click your phone number
3. Set Voice webhook to: `https://your-domain.com/webhooks/voice`
4. Set HTTP method to `POST`

### 3. Test Call Flow

1. Call your Twilio number
2. Verify the AI greeting plays
3. Speak something and check if transcription works
4. Check the `/api/calls` endpoint for call logs

### 4. Set Up Google Calendar (Optional)

If using Google Calendar integration:

1. Create OAuth 2.0 credentials in Google Cloud Console
2. Add your domain to authorized redirect URIs
3. Set the environment variables:
   ```bash
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   GOOGLE_REDIRECT_URI=https://your-domain.com/auth/callback
   ```

## Database Setup

The app uses SQLite by default, which works for MVP. For production scaling:

### Railway PostgreSQL

1. Add PostgreSQL service in Railway
2. Get the connection string
3. Set `DATABASE_URL` environment variable

### Render PostgreSQL

1. Create PostgreSQL database in Render
2. Get the connection string from database settings
3. Set `DATABASE_URL` environment variable

## Monitoring and Maintenance

### Health Checks

Both Railway and Render will automatically monitor `/health` endpoint.

### Logs

**Railway:**
```bash
railway logs
```

**Render:**
Check logs in the Render dashboard under your service.

### Database Migrations

When you update models:

1. Connect to your deployed app's environment
2. Run database migration commands
3. For SQLite, the database will auto-update on restart

## Security Checklist

- [ ] Use HTTPS (enabled by default on Railway/Render)
- [ ] Set strong `SECRET_KEY`
- [ ] Use secure authentication passwords
- [ ] Don't commit API keys to repository
- [ ] Enable webhook signature validation (Twilio)
- [ ] Set up proper CORS if needed
- [ ] Monitor API usage and set up rate limiting

## Scaling Considerations

### Performance
- Monitor response times
- Watch memory usage
- Set up database connection pooling
- Implement caching for frequent queries

### Reliability
- Set up uptime monitoring
- Configure auto-restart on failure
- Implement retry logic for external API calls
- Set up backup and recovery procedures

## Troubleshooting

### Common Issues

**1. Webhooks not receiving calls**
- Check Twilio webhook configuration
- Verify domain is accessible
- Check firewall settings

**2. API errors**
- Verify all API keys are set correctly
- Check API quotas and billing
- Monitor rate limits

**3. Database issues**
- Check database connection string
- Verify database permissions
- Monitor disk space

**4. Performance issues**
- Check memory usage
- Monitor API response times
- Review database query performance

### Debug Commands

**Check environment variables:**
```bash
# Railway
railway variables

# Render
# Check in dashboard under Environment tab
```

**View logs:**
```bash
# Railway
railway logs --tail

# Render
# View in dashboard
```

**Test API endpoints:**
```bash
# Test authentication
curl -X GET https://your-domain.com/api/calls \
  -u admin:password

# Test webhook trigger
curl -X POST https://your-domain.com/api/crm-trigger \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://httpbin.org/post", "payload": {"test": true}}'
```

## Support

If you encounter issues:

1. Check the logs first
2. Verify all environment variables are set
3. Test individual API integrations
4. Review Twilio webhook logs
5. Monitor external API status pages
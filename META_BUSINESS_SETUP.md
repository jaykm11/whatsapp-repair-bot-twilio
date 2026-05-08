# WhatsApp Business API Setup - Complete Guide

Step-by-step instructions to set up a WhatsApp Business account with Meta and get a **permanent (long-lived) access token** for production use.

---

## 🎯 Overview

**What you'll get:**
- ✅ Official WhatsApp Business phone number
- ✅ Verified Business Account
- ✅ Long-lived API token (60 days, auto-renewable)
- ✅ Production-ready webhook setup
- ✅ No more temporary tokens!

**Time required:** 30-60 minutes  
**Cost:** Free for development, pay-per-conversation for production

---

## 📋 Prerequisites

Before starting, you need:
- [ ] Facebook Business Manager account
- [ ] Verified business (legal business name, website, address)
- [ ] Phone number for WhatsApp (not currently on WhatsApp)
- [ ] Credit card (for Meta Business verification - no charge unless you exceed free tier)

---

## Step 1: Create Meta Business Account

### 1.1 Create/Access Business Manager

1. Go to: https://business.facebook.com
2. Click **"Create Account"** (or log in if you have one)
3. Enter your business details:
   - Business name (e.g., "Houston Home Repair Services")
   - Your name
   - Business email address
4. Click **"Next"** and complete verification

### 1.2 Verify Your Business

**Why?** Meta requires verification for production WhatsApp API access.

1. In Business Manager → **Business Settings**
2. Click **"Security Center"** → **"Start Verification"**
3. Upload business documents:
   - Business license or registration
   - Utility bill with business address
   - Tax ID document
4. Wait 1-3 business days for approval

**Note:** You can start development while verification is pending, but production requires verified business.

---

## Step 2: Create WhatsApp Business App

### 2.1 Create App

1. Go to: https://developers.facebook.com/apps
2. Click **"Create App"**
3. Select **"Business"** as app type
4. Fill in app details:
   - **App Name:** "Home Repair Bot" (or your choice)
   - **App Contact Email:** your business email
   - **Business Account:** Select your Business Manager account
5. Click **"Create App"**

### 2.2 Add WhatsApp Product

1. In your app dashboard, find **"WhatsApp"**
2. Click **"Set up"**
3. You'll see the WhatsApp setup page

---

## Step 3: Get Phone Number & API Credentials

### 3.1 Test Phone Number (Temporary - for development)

Meta provides a test number to get started:

1. In WhatsApp setup → **"API Setup"**
2. You'll see:
   - **Phone number ID** (e.g., `1016577688214830`)
   - **WhatsApp Business Account ID**
   - **Temporary access token** (24 hours)

**Copy these for your `.env` file** (temporary - we'll get permanent token later)

### 3.2 Add Your Own Phone Number (Production)

**Important:** This phone number will become your official WhatsApp Business number.

1. In WhatsApp setup → **"API Setup"** → **"Phone Numbers"**
2. Click **"Add Phone Number"**
3. Select **"Register a phone number you own with WhatsApp"**
4. Enter phone number (format: +1-XXX-XXX-XXXX)
5. Verify with SMS code
6. Choose display name (what customers see, e.g., "Houston Home Repair")
7. Select business category (e.g., "Home Improvement")
8. Add business description

**Cost:** First 1,000 conversations/month are FREE. After that:
- Service conversations (24hr window): $0.005 - $0.01 per conversation
- Marketing messages: $0.02 - $0.04 per conversation

---

## Step 4: Get Permanent Access Token

### 4.1 Create System User (Recommended for Production)

**Why?** System user tokens are not tied to a personal Facebook account and won't expire when people leave your company.

1. Go to **Business Settings** → **"Users"** → **"System Users"**
2. Click **"Add"**
3. Create system user:
   - Name: "WhatsApp Bot Service"
   - Role: **Admin**
4. Click **"Create System User"**

### 4.2 Generate Access Token

1. Click on your system user name
2. Click **"Generate New Token"**
3. Select your WhatsApp app
4. Set permissions:
   - ✅ `whatsapp_business_management`
   - ✅ `whatsapp_business_messaging`
   - ✅ `business_management`
5. Set token expiration: **"60 days"** or **"Never expire"**
6. Click **"Generate Token"**
7. **COPY AND SAVE THIS TOKEN IMMEDIATELY** - you won't see it again!

**This is your permanent token!** Use it in `.env`:
```bash
WHATSAPP_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxx
```

### 4.3 Token Renewal (for 60-day tokens)

Set up automatic renewal:

**Option A: Manual renewal** (every 60 days)
1. Repeat step 4.2 before expiration
2. Update `.env` with new token
3. Restart bot

**Option B: Automatic renewal** (recommended)
Use Meta's token refresh API:
```bash
curl -X GET "https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=YOUR_CURRENT_TOKEN"
```

Add this to a cron job that runs every 50 days.

---

## Step 5: Configure Webhook

### 5.1 Get Permanent Webhook URL

**For Production - Deploy to Cloud:**

**Option A: Google Cloud Run** (Recommended)
1. Deploy your bot: `gcloud run deploy whatsapp-bot --source .`
2. Get permanent URL: `https://whatsapp-bot-xyz.run.app`

**Option B: AWS Lambda + API Gateway**
1. Deploy via Serverless Framework or SAM
2. Get API Gateway URL

**Option C: Traditional Server** (DigitalOcean, Railway, Heroku)
1. Deploy to server
2. Get HTTPS URL (SSL required)

### 5.2 Set Up Webhook in Meta

1. Go to WhatsApp → **"Configuration"**
2. Click **"Edit"** next to Webhook
3. Enter webhook details:
   - **Callback URL:** `https://your-production-url.com/webhook`
   - **Verify Token:** `houston_repair_webhook_secret_2026` (or create your own)
     - This is in your `.env`: `VERIFY_TOKEN=houston_repair_webhook_secret_2026`
4. Click **"Verify and Save"**

### 5.3 Subscribe to Webhook Fields

1. After verification succeeds, scroll down to **"Webhook fields"**
2. Subscribe to:
   - ✅ **messages** - Incoming messages
   - ✅ **message_status** (optional) - Delivery/read receipts
3. Click **"Subscribe"**

---

## Step 6: Configure Business Profile

### 6.1 Set Up Profile

1. Go to WhatsApp → **"Getting Started"** → **"Business Profile"**
2. Fill in:
   - **Business Name:** "Houston Home Repair"
   - **Category:** Home Improvement / Plumbing / HVAC
   - **Description:** "AI-powered repair diagnosis. Send a photo, get instant help!"
   - **Address:** Your business address
   - **Business hours:** 24/7 or your hours
   - **Website:** Your website URL
   - **Email:** Support email
3. Upload **Profile Picture** (your logo, 640x640px)
4. Click **"Save"**

### 6.2 Set Up Greeting Message (Optional)

1. Go to WhatsApp → **"Message Templates"** (optional for automated responses)
2. Or handle greeting in your bot code:

```python
# In app/services/agent.py
if text_body in ["hello", "hi", "start"]:
    welcome_message = """👋 Welcome to Houston Home Repair AI!

I can help diagnose household plumbing and HVAC issues.

📸 Send me a photo of your problem
💬 Add a description (optional)

I'll provide:
• Simple explanation
• Technical diagnosis  
• 3 recommended professionals

Send a photo to get started! 🔧"""
```

---

## Step 7: Production Environment Variables

### 7.1 Update .env File

```bash
# WhatsApp Cloud API - PRODUCTION
WHATSAPP_TOKEN=EAAxxxxxxxxxxxxxxxxx  # Long-lived token from Step 4
PHONE_NUMBER_ID=1016577688214830     # Your production phone number ID
VERIFY_TOKEN=houston_repair_webhook_secret_2026

# Google Gemini AI
GEMINI_API_KEY=AIzaSyCMbi-Dt6_6KwvU7Z229rYNDt0TkH61X8s

# Server Configuration
PORT=8000
LOG_LEVEL=INFO

# WhatsApp API Version
WHATSAPP_API_VERSION=v21.0

# Production Mode
ENVIRONMENT=production
```

### 7.2 Security Best Practices

**DO:**
- ✅ Store tokens in environment variables (never in code)
- ✅ Use different tokens for dev/staging/prod
- ✅ Rotate tokens every 60 days (if not "never expire")
- ✅ Use HTTPS for webhook URL (required by Meta)
- ✅ Validate webhook signatures (prevent spoofing)

**DON'T:**
- ❌ Commit `.env` to git
- ❌ Share tokens in Slack/email
- ❌ Use production tokens in development
- ❌ Hardcode tokens in source code

---

## Step 8: Test Production Setup

### 8.1 Health Check

```bash
curl https://your-production-url.com/health
# Should return: {"status":"healthy","service":"whatsapp-repair-bot","version":"1.0.0"}
```

### 8.2 Webhook Verification

Check Meta webhooks panel for:
- ✅ Green checkmark next to webhook URL
- ✅ "Last received" timestamp updating

### 8.3 Send Test Message

1. Save your WhatsApp Business number in your phone
2. Send: "Hi"
3. Should receive welcome message
4. Send a photo of a broken item
5. Should receive AI diagnosis + professional recommendations

---

## Step 9: Monitor & Manage

### 9.1 Message Analytics

1. Go to WhatsApp → **"Analytics"**
2. Monitor:
   - Messages sent/received
   - Delivery rates
   - Conversation counts
   - Error rates

### 9.2 Quality Rating

Meta assigns quality ratings based on user feedback:
- **Green:** High quality (good!)
- **Yellow:** Medium quality (improve)
- **Red:** Low quality (at risk of being restricted)

**Tips to maintain high quality:**
- Respond quickly to messages
- Don't send spam
- Get opt-in before messaging users
- Provide value in every response

### 9.3 Cost Monitoring

1. Go to **Business Settings** → **"WhatsApp Accounts"** → **"Billing"**
2. Set up billing alerts:
   - Alert when conversation count > 900/month (before paid tier)
   - Monthly budget cap

**Pricing tiers (as of 2026):**
- Free: 1,000 service conversations/month
- Paid: $0.005 - $0.01 per service conversation (varies by country)

---

## Step 10: Scale & Advanced Features

### 10.1 Multiple Phone Numbers

1. Add more numbers in WhatsApp → **"Phone Numbers"**
2. Use same webhook URL
3. Route by `PHONE_NUMBER_ID` in webhook payload:

```python
# In app/main.py
phone_number_id = event.entry[0].changes[0].value.metadata.phone_number_id

if phone_number_id == "1111111111":
    # Route to plumbing bot
elif phone_number_id == "2222222222":
    # Route to HVAC bot
```

### 10.2 Message Templates (for proactive messaging)

**Required for:** Sending messages outside 24-hour customer service window

1. Go to WhatsApp → **"Message Templates"**
2. Click **"Create Template"**
3. Template example:
   ```
   Name: appointment_reminder
   Category: Utility
   Language: English
   
   Body:
   Hi {{1}}, this is a reminder about your {{2}} appointment 
   tomorrow at {{3}}. Reply CONFIRM to confirm or RESCHEDULE 
   to change the time.
   ```
4. Submit for Meta approval (usually 24-48 hours)
5. Use in code:

```python
await whatsapp_service.send_template_message(
    to=phone_number,
    template_name="appointment_reminder",
    parameters=["John", "plumbing", "2pm"]
)
```

### 10.3 Interactive Messages (Buttons/Lists)

Send messages with buttons:

```python
await whatsapp_service.send_interactive_message(
    to=phone_number,
    body="Choose repair urgency:",
    buttons=[
        {"id": "urgent", "title": "🚨 Emergency"},
        {"id": "soon", "title": "⏰ This Week"},
        {"id": "flexible", "title": "📅 Flexible"}
    ]
)
```

---

## Troubleshooting

### Issue: "Access token is invalid"

**Solutions:**
1. Token expired → Generate new token (Step 4.2)
2. Wrong token format → Verify it starts with `EAA`
3. App permissions → Re-grant `whatsapp_business_messaging` permission

### Issue: "Phone number not found"

**Solutions:**
1. Verify `PHONE_NUMBER_ID` in `.env` matches Meta console
2. Check phone number status (active, not restricted)
3. Ensure phone number is added to your WhatsApp Business Account

### Issue: Webhook not receiving messages

**Solutions:**
1. Check webhook URL is HTTPS (not HTTP)
2. Verify webhook is subscribed to `messages` field
3. Check server logs for incoming POST requests
4. Test webhook verification:
   ```bash
   curl "https://your-url.com/webhook?hub.mode=subscribe&hub.challenge=test&hub.verify_token=houston_repair_webhook_secret_2026"
   ```

### Issue: "Message failed to send"

**Solutions:**
1. Verify recipient phone number is in E.164 format (+1XXXXXXXXXX)
2. Check recipient has WhatsApp installed
3. Ensure you're within 24-hour customer service window (or use template)
4. Check message format (valid JSON, no special characters)

### Issue: High costs / unexpected charges

**Solutions:**
1. Check Analytics → Conversation breakdown
2. Look for loops (bot replying to its own messages)
3. Set up billing alerts in Business Settings
4. Implement rate limiting:
   ```python
   # Limit: 1 message per user per 10 seconds
   from functools import lru_cache
   import time
   
   last_message_time = {}
   
   def rate_limit(phone_number: str) -> bool:
       now = time.time()
       if phone_number in last_message_time:
           if now - last_message_time[phone_number] < 10:
               return False  # Too soon
       last_message_time[phone_number] = now
       return True
   ```

---

## Quick Reference Card

**Meta Developer Console:** https://developers.facebook.com/apps  
**Business Manager:** https://business.facebook.com  
**WhatsApp API Docs:** https://developers.facebook.com/docs/whatsapp/cloud-api

**Key IDs for .env:**
```bash
# Get these from Meta console:
WHATSAPP_TOKEN=EAAxxxx...           # System User → Generate Token
PHONE_NUMBER_ID=1016577688214830    # WhatsApp → API Setup
VERIFY_TOKEN=your_secret_token      # You choose this (for webhook)
```

**Production Checklist:**
- [ ] Business verified with Meta
- [ ] Production phone number added
- [ ] Long-lived access token generated
- [ ] Webhook URL deployed (HTTPS)
- [ ] Webhook verified and subscribed
- [ ] Business profile completed
- [ ] Test message sent successfully
- [ ] Billing alerts configured
- [ ] Monitoring/logging enabled

---

## Additional Resources

**Official Documentation:**
- WhatsApp Cloud API: https://developers.facebook.com/docs/whatsapp/cloud-api
- Business Manager: https://www.facebook.com/business/help
- System Users: https://developers.facebook.com/docs/development/build-and-test/app-development/system-users

**Meta Support:**
- Developer Community: https://developers.facebook.com/community
- WhatsApp Business Support: https://business.whatsapp.com/support

**Pricing:**
- Conversation Pricing: https://developers.facebook.com/docs/whatsapp/pricing
- Free Tier Details: https://developers.facebook.com/docs/whatsapp/cloud-api/get-started

---

**Last Updated:** 2026-04-12  
**Maintainer:** Ravi Maranganti

**Next Steps:**
1. Complete Meta Business verification (if pending)
2. Generate long-lived access token
3. Deploy bot to production (Cloud Run)
4. Update webhook URL in Meta console
5. Test end-to-end flow
6. Monitor analytics and costs

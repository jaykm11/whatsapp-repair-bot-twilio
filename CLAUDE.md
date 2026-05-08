# WhatsApp Home Repair AI Agent - Claude Instructions

Project-specific guidance for working with the WhatsApp repair bot codebase.

## Project Overview

This is a WhatsApp chatbot that uses Google Gemini AI to diagnose household repair issues (plumbing, HVAC, furniture) from photos and recommends local professionals.

**Tech Stack:**
- **Backend:** FastAPI (Python 3.12), async/await
- **AI/ML:** Google Gemini (`gemini-3.1-pro-preview`)
- **Messaging:** Twilio WhatsApp API
- **Deployment:** Local + Pinggy tunnel (dev), Google Cloud Run (production)

## Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app with webhook endpoint |
| `app/services/gemini.py` | Gemini AI image analysis service |
| `app/services/whatsapp.py` | Twilio API client (send/download) |
| `app/services/agent.py` | Message routing and orchestration |
| `app/services/professional_matcher.py` | Smart professional recommendations |
| `app/config.py` | Pydantic settings (loads .env) |
| `app/models.py` | Pydantic models for Twilio webhooks |
| `professionals.json` | Local professional directory (50 contacts) |
| `.env` | **NEVER COMMIT** - API keys and tokens |

## Critical Patterns

### 1. Gemini Model Name

**ALWAYS use:** `gemini-3.1-pro-preview`

```python
# ✅ Correct
self.model = genai.GenerativeModel("gemini-3.1-pro-preview")

# ❌ Wrong - these don't exist
self.model = genai.GenerativeModel("gemini-1.5-pro")
```

### 2. Running the App

```bash
PYTHONPATH=. python app/main.py
# Or use convenience script:
./start.sh
```

### 3. Environment Variables (.env)

**Required variables:**
```bash
# Twilio WhatsApp
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886   # Twilio sandbox or approved number

# Google Gemini AI
GEMINI_API_KEY=AIzaSyC...

# Server
PORT=8000
LOG_LEVEL=INFO
```

**Where to find Twilio credentials:**
1. [Twilio Console](https://console.twilio.com/) → Account Info (top of Dashboard)
2. `TWILIO_ACCOUNT_SID` — starts with `AC`
3. `TWILIO_AUTH_TOKEN` — click eye icon to reveal
4. `TWILIO_WHATSAPP_NUMBER` — Twilio Sandbox: `whatsapp:+14155238886`

**NEVER commit `.env`** — it's in `.gitignore`.

### 4. Webhook Setup (Development)

**Step 1:** Start Pinggy tunnel (separate terminal):
```bash
ssh -p 443 -R0:localhost:8000 a.pinggy.io
# Copy the HTTPS URL (e.g., https://xyz-123.run.pinggy-free.link)
```

**Step 2:** Configure Twilio webhook:
1. Go to [Twilio Console](https://console.twilio.com/)
2. Messaging → Try it out → Send a WhatsApp message (Sandbox), OR
3. Messaging → Services → your sender → Integrations
4. Set **"A message comes in"** webhook URL: `https://YOUR-PINGGY-URL/webhook`
5. Method: **HTTP POST**

**Note:** Pinggy free tunnels expire after 60 minutes and generate new URLs each time.

### 5. Twilio vs Meta — Key Differences

| Feature | Meta Cloud API (old) | Twilio (new) |
|---------|---------------------|--------------|
| Webhook format | JSON POST | Form-encoded POST |
| Media delivery | Media ID → lookup URL | Direct URL in payload |
| Auth | Bearer token | HTTP Basic (SID:Token) |
| Webhook verification | GET challenge/response | X-Twilio-Signature header (optional) |
| Mark as read | Supported | Not available |
| Sender format | E.164 number | `whatsapp:+1234567890` |

### 6. WhatsApp Message Flow

```
User sends image via WhatsApp
 ↓
Twilio sends form-encoded POST to /webhook
 ↓
main.py extracts Form fields (MessageSid, From, MediaUrl0, …)
 ↓
agent.py routes to handle_image_message()
 ↓
whatsapp.py downloads image from MediaUrl0 (Basic auth)
 ↓
gemini.py analyzes image (Gemini 3.1)
 ↓
professional_matcher.py recommends 3 pros
 ↓
whatsapp.py sends formatted response via Twilio Messages API
```

### 7. Testing

**Health check:**
```bash
curl http://localhost:8000/health
```

**Simulate a Twilio text webhook:**
```bash
curl -X POST http://localhost:8000/webhook \
  -d "MessageSid=SM123&From=whatsapp:+15551234567&To=whatsapp:+14155238886&Body=hello&NumMedia=0"
```

**Simulate a Twilio image webhook:**
```bash
curl -X POST http://localhost:8000/webhook \
  -d "MessageSid=SM123&From=whatsapp:+15551234567&To=whatsapp:+14155238886&Body=leaking pipe&NumMedia=1&MediaUrl0=https://example.com/image.jpg&MediaContentType0=image/jpeg"
```

### 8. Common Issues & Fixes

**Issue:** "ModuleNotFoundError: No module named 'app'"
```bash
cd whatsapp-repair-bot-twilio
PYTHONPATH=. python app/main.py
```

**Issue:** "422 Unprocessable Entity" on /webhook
```bash
# Ensure python-multipart is installed — FastAPI needs it for Form() parsing
pip install python-multipart
```

**Issue:** Messages not reaching bot
```bash
# 1. Is Pinggy tunnel running? (60 min expiration)
# 2. Is webhook URL updated in Twilio console?
# 3. Check app logs for "Webhook received"
# 4. Verify Twilio credentials in .env
```

**Issue:** Twilio 401 Unauthorized when sending
```bash
# Check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env
# Tokens can be regenerated in the Twilio console
```

## Code Style & Conventions

### Async/Await
All service methods are `async` — Twilio expects a fast 200 response.

### Error Handling
Always catch errors in agent.py and send user-friendly messages.

### Logging
```python
logger.info("Processing message from %s, type: %s", sender, message.type)
logger.error("Error downloading media: %s", e)
```

## Deployment (Production)

**Goal:** Replace Pinggy with permanent URL on Google Cloud Run.

**Steps:**
1. Deploy to Cloud Run: `gcloud run deploy whatsapp-bot`
2. Get permanent URL: `https://whatsapp-bot-xyz.run.app`
3. Update Twilio webhook URL **once** (no more Pinggy!)
4. Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER`, `GEMINI_API_KEY` as Cloud Run secrets/env vars

## Quick Reference

**Start everything:**
```bash
# Terminal 1: Start bot
cd whatsapp-repair-bot-twilio
./start.sh

# Terminal 2: Start tunnel
ssh -p 443 -R0:localhost:8000 a.pinggy.io
# Copy HTTPS URL → Update Twilio webhook
```

**Stop everything:**
```bash
pkill -f "python app/main.py"
```

## Resources

- **Twilio WhatsApp Docs:** https://www.twilio.com/docs/whatsapp
- **Twilio Console:** https://console.twilio.com/
- **Gemini API Docs:** https://ai.google.dev/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com

---

**Last Updated:** 2026-05-08
**Maintainer:** Ravi Maranganti

# WhatsApp Home Repair AI Agent

An AI-powered WhatsApp bot for diagnosing household plumbing and HVAC issues. Friends can text photos of problems and receive instant AI diagnosis with both homeowner-friendly explanations and technical briefs for repair professionals.

## Features

- 📸 **Image Analysis**: Upload photos of household issues via WhatsApp
- 🤖 **AI Diagnosis**: Powered by Google Gemini 1.5 Pro for multimodal analysis
- 👥 **Dual Output**: 
  - Simple explanations for homeowners
  - Technical briefs for repair professionals
- ⚡ **Real-time**: Instant webhook-based message processing
- 🔐 **Secure**: Environment-based configuration with proper token verification

## Tech Stack

- **Framework**: FastAPI (Python 3.10+)
- **AI Engine**: Google Gemini 1.5 Pro
- **Messaging**: Meta WhatsApp Cloud API (Direct integration)
- **Server**: Uvicorn (ASGI)
- **Tunneling**: Pinggy (for local development)

## Project Structure

```
whatsapp-repair-bot/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Pydantic settings
│   ├── models.py            # WhatsApp payload models
│   └── services/
│       ├── __init__.py
│       ├── whatsapp.py      # WhatsApp API client
│       ├── gemini.py        # Gemini AI service
│       └── agent.py         # Core orchestration logic
├── .env                     # Environment variables (create from .env.example)
├── .env.example             # Environment template
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup Instructions

### 1. Prerequisites

- Python 3.10 or higher
- Meta WhatsApp Business Account
- Google Gemini API key
- Pinggy account (for tunneling)

### 2. Clone and Setup

```bash
# Navigate to the project directory
cd whatsapp-repair-bot

# Create virtual environment (if not already activated)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```bash
# WhatsApp Cloud API (from Meta Developer Console)
WHATSAPP_TOKEN=your_meta_access_token
PHONE_NUMBER_ID=your_phone_number_id
VERIFY_TOKEN=your_custom_verify_token  # Create a random string

# Gemini AI (from Google AI Studio)
GEMINI_API_KEY=your_gemini_api_key

# Server Config
PORT=8000
LOG_LEVEL=INFO
```

### 4. Get API Credentials

#### WhatsApp Cloud API:
1. Go to [Meta Developer Console](https://developers.facebook.com/apps)
2. Create a new app (Business type)
3. Add WhatsApp product
4. Get your:
   - `WHATSAPP_TOKEN`: Temporary or permanent access token
   - `PHONE_NUMBER_ID`: Test or production phone number ID
   - `VERIFY_TOKEN`: Create your own random string (e.g., `my_secret_verify_token_123`)

#### Gemini API:
1. Go to [Google AI Studio](https://ai.google.dev/)
2. Create an API key
3. Copy the `GEMINI_API_KEY`

### 5. Run the Application

```bash
# From the whatsapp-repair-bot directory
uvicorn app.main:app --reload --port 8000
```

The server will start on `http://localhost:8000`

### 6. Set Up Pinggy Tunnel

In a separate terminal:

```bash
# Start Pinggy tunnel pointing to localhost:8000
ssh -p 443 -R0:localhost:8000 a.pinggy.io
```

You'll get a public URL like: `https://xyz.a.pinggy.io`

### 7. Configure Meta WhatsApp Webhook

1. Go to your Meta App → WhatsApp → Configuration
2. Set **Webhook URL**: `https://xyz.a.pinggy.io/webhook`
3. Set **Verify Token**: Same value as `VERIFY_TOKEN` in your `.env`
4. Subscribe to webhook fields: `messages`
5. Click **Verify and Save**

## Usage

Once configured, users can:

1. **Send "help"** - Get welcome message and instructions
2. **Send a photo** - Upload image of plumbing/HVAC issue
3. **Receive diagnosis** - Get AI-generated homeowner brief and pro technical details

### Example Conversation

```
User: [sends photo of leaking pipe]
Bot: 🔍 Analyzing your image... This may take a moment.

Bot: 🏠 Household Issue Diagnosis

You have a leaking pipe joint under the sink. This appears to be a 
compression fitting that's loosened over time. Turn off the water supply 
under the sink and call us - this needs tightening or replacement.

---

📋 For Our Repair Team:

- Issue: Loose compression fitting on cold water supply line
- Severity: Medium
- Parts Needed: Compression nut (1/2"), ferrule ring, plumber's tape
- Tools Required: Adjustable wrench, basin wrench
- Estimated Time: 15-30 minutes
- Safety Notes: Shut off water supply before repair
- Next Steps: Check for corrosion on threads, may need full fitting replacement

---

Need immediate assistance? Call us at: (Houston) 555-REPAIR
```

## Development

### Testing Locally

```bash
# Run the server
uvicorn app.main:app --reload --port 8000

# Test health endpoint
curl http://localhost:8000/health

# Test webhook verification (simulate Meta's verification)
curl "http://localhost:8000/webhook?hub.mode=subscribe&hub.challenge=test123&hub.verify_token=your_verify_token"
```

### Project Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run server with auto-reload
uvicorn app.main:app --reload

# Run with custom port
uvicorn app.main:app --port 8080

# View logs
# Logs are output to console by default
```

## Troubleshooting

### Webhook Verification Fails
- Ensure `VERIFY_TOKEN` in `.env` matches what you set in Meta console
- Check Pinggy tunnel is running and URL is correct
- Verify server is running on port 8000

### Messages Not Received
- Check webhook subscription includes `messages` field
- Verify `WHATSAPP_TOKEN` and `PHONE_NUMBER_ID` are correct
- Check server logs for errors

### Gemini API Errors
- Verify `GEMINI_API_KEY` is valid
- Check API quota limits
- Ensure image format is supported (JPEG/PNG)

### Import Errors
- Activate virtual environment: `source .venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

## Security Notes

- Never commit `.env` file to git
- Use environment variables for all secrets
- Implement webhook signature validation for production
- Consider rate limiting for production deployment
- Store sensitive data in secure vaults for production

## Future Enhancements

- [ ] Webhook signature validation (HMAC-SHA256)
- [ ] Video message analysis
- [ ] Multi-language support
- [ ] Rate limiting per user
- [ ] Database for storing diagnoses
- [ ] Admin dashboard
- [ ] Appointment scheduling integration

## License

This project is for internal use only.

## Support

For issues or questions:
- Check the troubleshooting section
- Review server logs
- Contact the development team

---

**Built with ❤️ in Houston**

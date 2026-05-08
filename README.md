# 🔧 WhatsApp Home Repair AI Agent

AI-powered household repair diagnosis via WhatsApp. Send a photo, get instant diagnosis + professional recommendations.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![Gemini](https://img.shields.io/badge/Gemini-1.5%20Pro-orange)
![WhatsApp](https://img.shields.io/badge/WhatsApp-Cloud%20API-25D366)

---

## 🚀 What It Does

1. **User sends photo** of broken pipe/AC/electrical issue via WhatsApp
2. **Gemini AI analyzes** the image and diagnoses the problem
3. **Bot responds** with:
   - Simple explanation for homeowner
   - Technical diagnosis for repair team
   - **3 recommended professionals** with pricing, availability, pros/cons

**Smart Matching:**
- **High urgency** → Shows 24/7 emergency services first
- **Medium urgency** → Balanced cost/speed options
- **Low urgency** → Most cost-effective professionals

---

## 🏗️ Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | WhatsApp | No app needed, 2B users |
| **Backend** | FastAPI (Python 3.12) | Async webhook handling |
| **AI/ML** | Google Gemini 1.5 Pro | Multimodal image analysis |
| **API Integration** | Meta WhatsApp Cloud API | Direct (no Twilio) |
| **Data Layer** | JSON | Professional registry (50 contacts) |
| **Deployment** | Uvicorn → Cloud Run/Lambda | Serverless, auto-scaling |

---

## 📸 Example Usage

**User:** [sends photo of leaking pipe]

**Bot:**
```
🏠 Household Issue Diagnosis

You have a leaking compression fitting under your sink. 
This needs immediate attention - turn off the water supply 
under the sink and call a plumber.

---

📋 For Our Repair Team:

- Issue: Loose compression fitting on cold water supply
- Severity: Medium
- Parts Needed: Compression nut (1/2"), ferrule ring
- Tools Required: Adjustable wrench, basin wrench
- Estimated Time: 15-30 minutes

---

🔧 MODERATE URGENCY - Showing balanced cost/speed options

🔧 Recommended Professionals:

1. Quality Plumbing Solutions ⭐ 4.7★
   📞 +1-713-555-0103
   💵 $95-120/hr
   ⏰ Availability: Next Day
   📜 Credentials: Master Plumber, Licensed, Insured
   🏘️ Serves: Houston, Cypress
   
   ✅ Pros: Good balance of cost/quality, Next day service
   ❌ Cons: No same-day service
   💡 Why recommended: Best balance of speed and quality

2. Joe's Emergency Plumbing ⭐ 4.8★
   📞 +1-713-555-0100
   💵 $125-150/hr
   ⏰ Availability: Same Day (2-4 hours)
   ...
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- Meta WhatsApp Business Account
- Google Gemini API key

### 1. Clone & Install

```bash
git clone https://github.com/ravimaranganti/whatsapp-repair-bot.git
cd whatsapp-repair-bot
git checkout whatsapp-repair-bot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials:
# - WHATSAPP_TOKEN (from Meta Developer Console)
# - PHONE_NUMBER_ID (from Meta)
# - VERIFY_TOKEN (create your own secret)
# - GEMINI_API_KEY (from Google AI Studio)
```

### 3. Run Server

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Expose Webhook (Development)

```bash
# In separate terminal
ssh -p 443 -R0:localhost:8000 a.pinggy.io
# Copy the HTTPS URL
```

### 5. Configure Meta Webhook

1. Go to [Meta Developer Console](https://developers.facebook.com/apps)
2. Your App → WhatsApp → Configuration → Webhook
3. **Callback URL**: `https://your-pinggy-url/webhook`
4. **Verify Token**: Value from your `.env`
5. Subscribe to **messages** field

---

## 📁 Project Structure

```
whatsapp-repair-bot/
├── app/
│   ├── main.py                    # FastAPI app + webhook endpoints
│   ├── config.py                  # Pydantic settings
│   ├── models.py                  # WhatsApp payload models
│   └── services/
│       ├── whatsapp.py            # WhatsApp API client
│       ├── gemini.py              # Gemini AI integration
│       ├── agent.py               # Message orchestration
│       └── professional_matcher.py # Smart professional matching
├── professionals.json             # Professional registry (fake data for testing)
├── .env                          # Your credentials (gitignored)
├── .env.example                  # Template
├── requirements.txt              # Dependencies
├── TESTING_GUIDE.md             # Detailed testing instructions
└── README.md                     # This file
```

---

## 🔧 Professional Matching Logic

### Severity-Based Recommendations

| Severity | Priority | Example |
|----------|----------|---------|
| **High** | Fastest response → Rating → Cost | Burst pipe: Shows 24/7 emergency services |
| **Medium** | Balance speed/cost → Rating | Slow leak: Shows next-day + same-day options |
| **Low** | Lowest cost → Rating | Routine maintenance: Shows budget options |

### Cost-Benefit Factors

Each professional includes:
- **Hourly Rate**: Base cost comparison
- **Availability**: Same day / Next day / 3-5 days
- **Emergency Fees**: After-hours surcharges
- **Certifications**: Master license, insurance, bonding
- **Pros/Cons**: Quick comparison
- **Why Recommended**: Personalized reasoning

---

## 🎯 Features

- ✅ **Multimodal AI**: Gemini 1.5 Pro analyzes images
- ✅ **Smart Matching**: Professionals ranked by urgency
- ✅ **Dual Audience**: Homeowner brief + pro technical details
- ✅ **Cost Transparency**: Shows rates, fees, pros/cons
- ✅ **Zero Client Install**: Works via WhatsApp
- ✅ **Async Architecture**: Non-blocking webhook handling
- ✅ **Type Safe**: Pydantic models throughout
- ⏳ **Coming Soon**: Database, location-based search, appointment scheduling

---

## 💰 Cost Breakdown

| Service | Free Tier | Paid (1000 users/mo) |
|---------|-----------|----------------------|
| WhatsApp API | 1000 messages | $0 (free tier) |
| Gemini API | 50 requests/day | ~$25 |
| Cloud Run | 2M requests | ~$20 |
| Domain + SSL | Cloudflare free | $0 |
| **Total** | **$0/month** | **~$50/month** |

---

## 🔐 Security

- ✅ Environment variables (never commit `.env`)
- ✅ `.gitignore` configured
- ✅ WhatsApp webhook verification
- ⏳ HMAC signature validation (future)
- ⏳ Rate limiting per user (future)

---

## 📊 Testing

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for complete instructions.

**Quick Test:**
1. Add your phone to Meta's allowed list
2. Send "help" → Get welcome message
3. Send photo → Get diagnosis + recommendations

---

## 🚀 Deployment

### Option 1: Google Cloud Run (Recommended)

```bash
# Build Docker image
docker build -t whatsapp-repair-bot .

# Deploy to Cloud Run
gcloud run deploy whatsapp-repair-bot \
  --image whatsapp-repair-bot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Option 2: AWS Lambda

Use Mangum adapter for FastAPI → Lambda compatibility.

### Option 3: Traditional Server

```bash
# Production with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## 🛣️ Roadmap

- [ ] PostgreSQL with PostGIS for geospatial queries
- [ ] Redis caching for repeated images
- [ ] User conversation history
- [ ] Appointment scheduling integration
- [ ] Multi-language support
- [ ] Video message analysis
- [ ] Admin dashboard
- [ ] Analytics & monitoring (Sentry)

---

## 🤝 Contributing

1. Fork the repo
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📝 License

MIT License - see LICENSE file

---

## 🙏 Acknowledgments

- **Meta** - WhatsApp Cloud API
- **Google** - Gemini 1.5 Pro
- **FastAPI** - Modern Python web framework
- **Pinggy** - Development tunneling

---

## 📧 Contact

Questions? Open an issue or reach out!

**Built for Houston homeowners** 🏠🔧

---

## 🔍 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Health check |
| `/health` | GET | Service status |
| `/webhook` | GET | WhatsApp verification |
| `/webhook` | POST | Incoming messages |

---

## 🧪 Example Professional JSON

```json
{
  "name": "Joe's Emergency Plumbing",
  "phone": "+1-713-555-0100",
  "hourly_rate": "$125-150/hr",
  "availability": "Same Day (2-4 hours)",
  "certifications": ["Master Plumber", "Licensed", "Insured"],
  "pros": ["Very experienced", "Fast response"],
  "cons": ["Premium pricing"]
}
```

See `professionals.json` for full fake dataset (replace with real contacts).

---

**⭐ Star this repo if you find it useful!**

# WhatsApp Repair Bot - Testing Guide

## ✅ Step 1: Server is Running

Your FastAPI server is now running on `http://localhost:8000`

Test it:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy","service":"whatsapp-repair-bot","version":"1.0.0"}
```

---

## 📡 Step 2: Set Up Pinggy Tunnel

**Open a NEW terminal** and run:

```bash
ssh -p 443 -R0:localhost:8000 a.pinggy.io
```

You'll see output like:
```
Pinggy is listening on...
https://randomstring-12345.a.pinggy.io
```

**Copy that URL!** You'll need it for Meta configuration.

---

## 🔗 Step 3: Configure Meta WhatsApp Webhook

1. Go to [Meta Developer Console](https://developers.facebook.com/apps)
2. Select your WhatsApp app
3. Click **WhatsApp** → **Configuration**
4. Under **Webhook**, click **Edit**

5. Enter:
   - **Callback URL**: `https://YOUR-PINGGY-URL/webhook`
     - Example: `https://randomstring-12345.a.pinggy.io/webhook`
   - **Verify Token**: `houston_repair_webhook_secret_2026`
     - ⚠️ Must match exactly what's in your `.env` file

6. Click **Verify and Save**

7. If verification succeeds, subscribe to webhook fields:
   - Check: **messages**
   - Click **Subscribe**

---

## 📱 Step 4: Test with WhatsApp

### Option A: Test Phone Number (Meta Provides)

Meta gives you a test phone number to send messages to.

1. In Meta Console → WhatsApp → **API Setup**
2. Find "Send and receive messages" section
3. You'll see a test phone number (format: `+1 555...`)

### Option B: Add Your Phone Number

1. In Meta Console → WhatsApp → **API Setup**
2. Click **"To"** dropdown
3. Click **"Manage phone number list"**
4. Add your phone number
5. Verify via code sent to your phone

---

## 🧪 Step 5: Send Test Messages

### Test 1: Send "help"

Send a text message: **help**

Expected response:
```
👋 Welcome to Houston Home Repair AI!

I can help diagnose household plumbing and HVAC issues.

**How to use:**
📸 Send me a photo of your household issue
💬 Optionally include a description of the problem
...
```

### Test 2: Send an Image

Take a photo of:
- A pipe (any pipe)
- Sink/faucet
- HVAC vent
- Water heater
- Or search Google Images for "leaking pipe" and send that

Send the image via WhatsApp

Expected response:
```
🔍 Analyzing your image... This may take a moment.
```

Then:
```
🏠 **Household Issue Diagnosis**

[Homeowner explanation in plain English]

---

📋 **For Our Repair Team:**

- Issue: [Technical description]
- Severity: Low/Medium/High
- Parts Needed: [List]
- Tools Required: [List]
...
```

---

## 🐛 Troubleshooting

### Webhook Verification Fails

**Check your server logs:**
```bash
# The server is running in background, check logs at:
tail -f /tmp/uvicorn-output.log
```

**Common issues:**
- ❌ Verify token mismatch → Must be exactly `houston_repair_webhook_secret_2026`
- ❌ Pinggy tunnel not running → Restart Pinggy
- ❌ Wrong URL → Make sure it ends with `/webhook`

### Messages Not Being Received

1. **Check webhook subscription:**
   - Meta Console → WhatsApp → Configuration
   - Ensure "messages" field is subscribed

2. **Check server is running:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Check Pinggy tunnel:**
   - Look at Pinggy terminal
   - You should see requests when you send messages

4. **Check server logs:**
   - Look for incoming webhook POST requests
   - Check for any error messages

### Gemini API Errors

If you get errors about Gemini:

1. **Verify API key:**
   ```bash
   # Check your .env file
   cat .env | grep GEMINI
   ```

2. **Test Gemini separately:**
   ```python
   import google.generativeai as genai
   genai.configure(api_key="AIzaSyCMbi-Dt6_6KwvU7Z229rYNDt0TkH61X8s")
   model = genai.GenerativeModel("gemini-1.5-pro")
   response = model.generate_content("Hello!")
   print(response.text)
   ```

3. **Check API quota:**
   - Go to [Google AI Studio](https://ai.google.dev/)
   - Check if you've hit rate limits

---

## 📊 Monitoring

### Watch Server Logs (Real-time)

The server is running in background. To see what's happening:

```bash
# Check if server is running
ps aux | grep uvicorn

# Server outputs are being logged
# You can check the background task output
```

### Example Log Output

When everything works:
```
INFO: Webhook received: {'object': 'whatsapp_business_account', ...}
INFO: Processing message from 15551234567, type: image
INFO: Downloading image: 123456789
INFO: Sending image to Gemini for analysis
INFO: Gemini analysis completed successfully
INFO: Message sent successfully
```

---

## 🎯 Test Checklist

- [ ] Server started successfully (`/health` returns 200)
- [ ] Pinggy tunnel running (got HTTPS URL)
- [ ] Meta webhook verified (green checkmark)
- [ ] Webhook subscribed to "messages"
- [ ] Sent "help" → Got welcome message
- [ ] Sent image → Got AI diagnosis
- [ ] Both homeowner and pro briefs included
- [ ] No errors in server logs

---

## 🚀 Next Steps After Testing

Once everything works:

1. **Add more phone numbers** to test with friends
2. **Try different household issues:**
   - Leaking pipes
   - HVAC vents
   - Water heaters
   - Electrical outlets (but bot is trained for plumbing/HVAC)

3. **Test edge cases:**
   - Send random photos (not household issues)
   - Send videos
   - Send very large images

4. **Monitor performance:**
   - How long does Gemini take?
   - Are responses accurate?

---

## 📞 Support

**Server running?**
```bash
curl http://localhost:8000/health
```

**Stop the server:**
```bash
# Find the process
ps aux | grep uvicorn

# Kill it
kill <process_id>
```

**Restart everything:**
```bash
# From whatsapp-repair-bot directory
python -m uvicorn app.main:app --reload --port 8000
```

---

**Happy Testing! 🔧**

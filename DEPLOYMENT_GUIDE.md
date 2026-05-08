# Deployment Guide - Google Cloud Run

Complete guide to deploy the WhatsApp bot to Google Cloud Run for production use.

---

## 🎯 Why Cloud Run?

**Benefits:**
- ✅ **Permanent HTTPS URL** - No more Pinggy tunnel expiration
- ✅ **Auto-scaling** - 0 to 1000+ instances automatically
- ✅ **Free Tier** - 2 million requests/month free
- ✅ **Fast deploys** - 2-3 minutes from code to production
- ✅ **Built-in CI/CD** - Deploy from GitHub directly
- ✅ **Environment variables** - Secure secret management

**Cost:**
- Free tier: 2M requests, 360,000 GB-seconds, 180,000 vCPU-seconds per month
- After free tier: ~$0.00002400 per request (very cheap)
- **Estimated cost for this bot:** $0-5/month for moderate usage

---

## 📋 Prerequisites

- [ ] Google Cloud account (free trial gives $300 credit)
- [ ] `gcloud` CLI installed
- [ ] Docker installed (optional - Cloud Run can build for you)
- [ ] GitHub repository with your code

---

## Step 1: Set Up Google Cloud Project

### 1.1 Create Project

```bash
# Install gcloud CLI first (if not installed)
# Download from: https://cloud.google.com/sdk/docs/install

# Login to Google Cloud
gcloud auth login

# Create a new project
gcloud projects create whatsapp-repair-bot --name="WhatsApp Repair Bot"

# Set as default project
gcloud config set project whatsapp-repair-bot

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 1.2 Enable Billing

1. Go to: https://console.cloud.google.com/billing
2. Link a billing account (free tier applies automatically)
3. Note: You won't be charged unless you exceed free tier

---

## Step 2: Create Dockerfile

Create `Dockerfile` in the `whatsapp-repair-bot/` directory:

```dockerfile
# Use official Python runtime as base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY professionals.json .

# Set environment variable for Python path
ENV PYTHONPATH=/app

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.1 Create .dockerignore

Create `.dockerignore` to exclude unnecessary files:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Git
.git/
.gitignore

# Environment
.env
.env.*

# Documentation
*.md
!README.md

# Claude
.claude/
CLAUDE.md

# Logs
*.log

# Testing
.pytest_cache/
.coverage
```

---

## Step 3: Store Secrets in Secret Manager

**Why?** Don't hardcode API keys in container images.

### 3.1 Create Secrets

```bash
# WhatsApp Token
echo -n "EAAi5zvzs55EBRB2cVmVYlueCGUJYNlL4KwwXz1GgeuqwGrBQdtPx7vhuYoTYLkFSjbhFjJ2xDqAjKfGUdcrZBTTW7ByvQVVL59RGZB2lgFvZCpGQYbnRXeNwASF3XQPDy7yyqGYiS0eGeJ0CpHD7lJS8xxUrwY8lo7gApc9Drpg1ZByVSMxV77zRSgKajhPnWMOFwWDwMz4eyZARHlklHMvYcOyDjV1AEL9MMaTHNI4h91FKEVfmfOlQ7BY4cmHtg1qH9mXLheIO7MTpmAwZDZD" | \
  gcloud secrets create whatsapp-token --data-file=-

# Gemini API Key
echo -n "AIzaSyCMbi-Dt6_6KwvU7Z229rYNDt0TkH61X8s" | \
  gcloud secrets create gemini-api-key --data-file=-

# Phone Number ID
echo -n "1016577688214830" | \
  gcloud secrets create phone-number-id --data-file=-

# Verify Token
echo -n "houston_repair_webhook_secret_2026" | \
  gcloud secrets create verify-token --data-file=-
```

### 3.2 Verify Secrets Created

```bash
gcloud secrets list
```

---

## Step 4: Deploy to Cloud Run

### 4.1 Deploy from Source (Recommended - Easiest)

```bash
# Navigate to repo root
cd /c/Users/RMaranganti/Documents/home-tx-pricing-agent/whatsapp-repair-bot

# Deploy (Cloud Run will build the image for you)
gcloud run deploy whatsapp-repair-bot \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars PORT=8000,LOG_LEVEL=INFO,WHATSAPP_API_VERSION=v21.0 \
  --set-secrets WHATSAPP_TOKEN=whatsapp-token:latest,GEMINI_API_KEY=gemini-api-key:latest,PHONE_NUMBER_ID=phone-number-id:latest,VERIFY_TOKEN=verify-token:latest \
  --min-instances 0 \
  --max-instances 10 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60
```

**What this does:**
- Builds Docker image from source code
- Creates Cloud Run service
- Sets environment variables
- Mounts secrets securely
- Auto-scales 0-10 instances
- Allows public access (for WhatsApp webhooks)

### 4.2 Alternative: Deploy from Pre-built Image

If you prefer to build locally:

```bash
# Build image
docker build -t gcr.io/whatsapp-repair-bot/bot:latest .

# Push to Google Container Registry
docker push gcr.io/whatsapp-repair-bot/bot:latest

# Deploy
gcloud run deploy whatsapp-repair-bot \
  --image gcr.io/whatsapp-repair-bot/bot:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars PORT=8000,LOG_LEVEL=INFO,WHATSAPP_API_VERSION=v21.0 \
  --set-secrets WHATSAPP_TOKEN=whatsapp-token:latest,GEMINI_API_KEY=gemini-api-key:latest,PHONE_NUMBER_ID=phone-number-id:latest,VERIFY_TOKEN=verify-token:latest
```

### 4.3 Get Service URL

After deployment, you'll see:

```
Service [whatsapp-repair-bot] revision [whatsapp-repair-bot-00001-abc] has been deployed and is serving 100 percent of traffic.
Service URL: https://whatsapp-repair-bot-xyz123-uc.a.run.app
```

**Save this URL!** This is your permanent webhook URL.

---

## Step 5: Update Meta Webhook

1. Go to [Meta Developer Console](https://developers.facebook.com/apps)
2. Select your WhatsApp app
3. Go to WhatsApp → **Configuration** → **Webhook**
4. Click **"Edit"**
5. Update:
   - **Callback URL:** `https://whatsapp-repair-bot-xyz123-uc.a.run.app/webhook`
   - **Verify Token:** `houston_repair_webhook_secret_2026`
6. Click **"Verify and Save"**

**✅ You now have a permanent webhook URL!** No more Pinggy tunnels.

---

## Step 6: Test Production Deployment

### 6.1 Health Check

```bash
curl https://whatsapp-repair-bot-xyz123-uc.a.run.app/health
```

Expected response:
```json
{"status":"healthy","service":"whatsapp-repair-bot","version":"1.0.0"}
```

### 6.2 Check Logs

```bash
# View live logs
gcloud run services logs tail whatsapp-repair-bot --region us-central1

# Or view in console
# https://console.cloud.google.com/run
```

### 6.3 Send Test Message

1. Send "Hi" to your WhatsApp Business number
2. Should receive welcome message
3. Send a photo of a broken item
4. Should receive AI diagnosis

---

## Step 7: Monitor & Maintain

### 7.1 View Metrics

**Console:** https://console.cloud.google.com/run/detail/us-central1/whatsapp-repair-bot/metrics

**Metrics:**
- Request count
- Request latency
- Container instance count
- Memory utilization
- CPU utilization
- Error rate

### 7.2 Set Up Alerts

```bash
# Create alert for high error rate
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="WhatsApp Bot Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=5 \
  --condition-threshold-duration=60s
```

### 7.3 View Logs

**Real-time:**
```bash
gcloud run services logs tail whatsapp-repair-bot --region us-central1 --follow
```

**Search logs:**
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=whatsapp-repair-bot" \
  --limit 50 \
  --format json
```

---

## Step 8: Update & Redeploy

### 8.1 Deploy New Version

After making code changes:

```bash
# Commit changes
git add .
git commit -m "Fix: update professional recommendations"
git push

# Redeploy (simple!)
gcloud run deploy whatsapp-repair-bot \
  --source . \
  --region us-central1
```

Cloud Run will:
1. Build new image
2. Create new revision
3. Gradually shift traffic (0% → 100%)
4. Keep old revision for rollback

### 8.2 Rollback

If new version has issues:

```bash
# List revisions
gcloud run revisions list --service whatsapp-repair-bot --region us-central1

# Rollback to previous revision
gcloud run services update-traffic whatsapp-repair-bot \
  --to-revisions whatsapp-repair-bot-00001-abc=100 \
  --region us-central1
```

### 8.3 Update Secrets

```bash
# Update WhatsApp token
echo -n "NEW_TOKEN_HERE" | gcloud secrets versions add whatsapp-token --data-file=-

# Redeploy to pick up new secret
gcloud run deploy whatsapp-repair-bot \
  --source . \
  --region us-central1
```

---

## Step 9: Production Optimization

### 9.1 Custom Domain (Optional)

**Get a custom URL like:** `https://bot.yourdomain.com`

```bash
# Map custom domain
gcloud run domain-mappings create \
  --service whatsapp-repair-bot \
  --domain bot.yourdomain.com \
  --region us-central1
```

Then update DNS with the provided records.

### 9.2 Increase Performance

**For high traffic:**

```bash
gcloud run services update whatsapp-repair-bot \
  --min-instances 1 \
  --max-instances 50 \
  --cpu 2 \
  --memory 1Gi \
  --concurrency 80 \
  --region us-central1
```

**Settings explained:**
- `--min-instances 1` - Always have 1 warm instance (faster first request)
- `--max-instances 50` - Scale up to 50 instances under load
- `--cpu 2` - 2 vCPUs per instance
- `--memory 1Gi` - 1GB RAM per instance
- `--concurrency 80` - 80 requests per instance

**Cost impact:** Min instances = always running = ~$10-20/month

### 9.3 Enable Cloud CDN (for static assets)

If serving images/files:

```bash
gcloud compute backend-services update whatsapp-repair-bot \
  --enable-cdn \
  --region us-central1
```

---

## Step 10: CI/CD with GitHub Actions

**Automate deployment on git push!**

### 10.1 Create Service Account

```bash
# Create service account
gcloud iam service-accounts create github-deployer \
  --display-name="GitHub Actions Deployer"

# Grant Cloud Run Admin role
gcloud projects add-iam-policy-binding whatsapp-repair-bot \
  --member="serviceAccount:github-deployer@whatsapp-repair-bot.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# Grant Service Account User role
gcloud projects add-iam-policy-binding whatsapp-repair-bot \
  --member="serviceAccount:github-deployer@whatsapp-repair-bot.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Create key
gcloud iam service-accounts keys create key.json \
  --iam-account=github-deployer@whatsapp-repair-bot.iam.gserviceaccount.com
```

### 10.2 Add GitHub Secret

1. Go to GitHub repo → **Settings** → **Secrets** → **Actions**
2. Click **"New repository secret"**
3. Name: `GCP_SA_KEY`
4. Value: Copy contents of `key.json`
5. Click **"Add secret"**

### 10.3 Create GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches:
      - main  # Deploy on push to main

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Cloud SDK
      uses: google-github-actions/setup-gcloud@v1
      with:
        service_account_key: ${{ secrets.GCP_SA_KEY }}
        project_id: whatsapp-repair-bot
    
    - name: Deploy to Cloud Run
      run: |
        gcloud run deploy whatsapp-repair-bot \
          --source . \
          --region us-central1 \
          --platform managed \
          --allow-unauthenticated
```

Now every push to `main` auto-deploys! 🚀

---

## Troubleshooting

### Issue: "Permission denied" during deployment

**Solution:**
```bash
# Make sure you're authenticated
gcloud auth login

# Set correct project
gcloud config set project whatsapp-repair-bot
```

### Issue: Container fails to start

**Solution:**
```bash
# Check logs
gcloud run services logs tail whatsapp-repair-bot --region us-central1

# Common issues:
# 1. Missing PYTHONPATH - add ENV PYTHONPATH=/app to Dockerfile
# 2. Wrong port - Cloud Run sets PORT env var, use it
# 3. Missing dependencies - check requirements.txt
```

### Issue: "Service Unavailable" errors

**Solution:**
```bash
# Increase timeout and memory
gcloud run services update whatsapp-repair-bot \
  --timeout 300 \
  --memory 1Gi \
  --region us-central1
```

### Issue: High costs

**Solution:**
```bash
# Set budget alerts
gcloud billing budgets create \
  --billing-account BILLING_ACCOUNT_ID \
  --display-name "Monthly Budget" \
  --budget-amount 20USD

# Reduce min instances to 0
gcloud run services update whatsapp-repair-bot \
  --min-instances 0 \
  --region us-central1
```

---

## Cost Estimation

**Free Tier (first 2M requests/month):**
```
Requests: 2,000,000 free
GB-seconds: 360,000 free  
vCPU-seconds: 180,000 free
```

**Typical usage for this bot:**
```
~1,000 messages/day = 30,000 requests/month
Each request: ~500ms, 512MB RAM, 1 vCPU

Monthly cost: $0 (well within free tier)
```

**High usage (10,000 messages/day):**
```
300,000 requests/month
Still within free tier = $0
```

**You'd need >70,000 messages/day to exceed free tier!**

---

## Quick Commands Reference

```bash
# Deploy
gcloud run deploy whatsapp-repair-bot --source . --region us-central1

# View logs
gcloud run services logs tail whatsapp-repair-bot --region us-central1

# Update environment variable
gcloud run services update whatsapp-repair-bot \
  --update-env-vars LOG_LEVEL=DEBUG \
  --region us-central1

# Update secret
echo -n "NEW_VALUE" | gcloud secrets versions add SECRET_NAME --data-file=-

# List revisions
gcloud run revisions list --service whatsapp-repair-bot --region us-central1

# Rollback
gcloud run services update-traffic whatsapp-repair-bot \
  --to-revisions REVISION_NAME=100 \
  --region us-central1

# Delete service
gcloud run services delete whatsapp-repair-bot --region us-central1
```

---

## Next Steps After Deployment

1. ✅ Deploy to Cloud Run
2. ✅ Update Meta webhook URL
3. ✅ Test end-to-end (send WhatsApp message)
4. ✅ Set up monitoring alerts
5. ✅ Configure CI/CD (optional)
6. ✅ Add custom domain (optional)
7. ✅ Monitor costs in Cloud Console

**Your bot is now production-ready!** 🎉

---

**Resources:**
- Cloud Run Docs: https://cloud.google.com/run/docs
- Pricing Calculator: https://cloud.google.com/products/calculator
- Quickstart: https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-service

**Last Updated:** 2026-04-12  
**Maintainer:** Ravi Maranganti

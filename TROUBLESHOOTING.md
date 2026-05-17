# Troubleshooting Guide — WhatsApp Repair Bot (Twilio + GCP Cloud Run)

This document summarizes every issue encountered during development and deployment, and how each was resolved.

---

## 1. Migrating from Meta WhatsApp Cloud API to Twilio

**Issue:** The original codebase used Meta's WhatsApp Cloud API (JSON webhooks, Bearer token auth, media ID lookup). Twilio uses a completely different protocol.

**Key differences:**

| Feature | Meta (old) | Twilio (new) |
|---------|-----------|--------------|
| Webhook format | JSON POST | Form-encoded POST |
| Media delivery | Media ID → separate URL lookup | Direct URL in webhook payload |
| Auth | Bearer token | HTTP Basic (SID + Token) |
| Webhook verification | GET challenge/response | X-Twilio-Signature (optional) |
| Sender format | E.164 number | `whatsapp:+1234567890` |

**Fix:**
- Replaced `WebhookEvent` JSON models with `TwilioWebhookPayload` using FastAPI `Form()` fields
- Rewrote `WhatsAppService` to use Twilio REST API (`api.twilio.com`) with HTTP Basic auth
- Removed `mark_message_read()` (not available in Twilio)
- Added `python-multipart` to `requirements.txt` (required by FastAPI for `Form()` parsing)

---

## 2. GCP Cloud Run — `PORT` Reserved Variable

**Issue:** Attempting to set `PORT` as a Cloud Run environment variable failed with "PORT name is reserved".

**Fix:** Cloud Run automatically injects `PORT=8080`. Remove `PORT` from Cloud Run env vars entirely. The Dockerfile CMD uses `${PORT:-8080}` which reads the injected value automatically.

---

## 3. Cloud Build — Custom Service Account Requires Log Bucket

**Error:**
```
if 'build.service_account' is specified, the build must either (a) specify 'build.logs_bucket'...
```

**Fix:** Added to `cloudbuild.yaml`:
```yaml
options:
  defaultLogsBucketBehavior: REGIONAL_USER_OWNED_BUCKET
```

---

## 4. Cloud Build Step Failing — `gcloud run services update` vs `gcloud run deploy`

**Error:** Step #2 exited with non-zero status 2 / `gcloud help -- SEARCH_TERMS`

**Cause:** `gcloud run services update` fails if the service doesn't exist yet (first deploy). Also, `--startup-cpu-boost` caused argument parse errors in the `cloud-sdk:slim` image.

**Fix:**
- Changed `gcloud run services update` → `gcloud run deploy` (works for both create and update)
- Removed `--startup-cpu-boost` flag

---

## 5. Gemini SDK — Deprecated Package + Wrong Model Name

**Error:**
```
ModuleNotFoundError / FutureWarning: All support for google.generativeai has ended
404 models/gemini-1.5-flash is not found
```

**Cause:** The `google-generativeai` package is fully deprecated. Model `gemini-1.5-flash` is not available for new API keys.

**Fix:**
- Replaced `google-generativeai==0.8.3` with `google-genai==2.0.1` in `requirements.txt`
- Confirmed available models by running `client.models.list()`
- Switched to `gemini-2.5-flash` (confirmed working)
- Removed `Pillow` dependency (new SDK uses `types.Part.from_bytes()` directly)

---

## 6. Gemini API — `generate_content_async` Hanging on Cloud Run

**Error:** Request stuck at "Analyzing image..." with no response after 30+ seconds.

**Cause:** `generate_content_async` uses gRPC transport which can stall on Cloud Run's networking, especially on cold starts.

**Fix:**
- Replaced `generate_content_async()` with `asyncio.to_thread(generate_content, ...)` — runs the sync version in a thread pool without blocking the event loop
- Added `asyncio.wait_for(..., timeout=50)` to prevent indefinite hangs
- Bumped timeout from 30s → 50s

---

## 7. `requirements.txt` Dependency Conflict

**Error:**
```
ERROR: Cannot install google-genai==2.0.1 and httpx==0.27.2 because these package versions have conflicting dependencies.
```

**Cause:** `google-genai==2.0.1` requires `httpx>=0.28.0` but `httpx==0.27.2` was pinned.

**Fix:** Updated all package versions to latest compatible:

| Package | Old | New |
|---------|-----|-----|
| `httpx` | `0.27.2` | `0.28.1` |
| `fastapi` | `0.115.0` | `0.122.0` |
| `uvicorn` | `0.32.0` | `0.38.0` |
| `pydantic` | `2.9.2` | `2.12.4` |
| `pydantic-settings` | `2.6.0` | `2.14.1` |
| `python-multipart` | `0.0.12` | `0.0.20` |

---

## 8. Cloud Run Startup Probe Failing — Container Not Binding Port 8080

**Error:**
```
Default STARTUP TCP probe failed 1 time consecutively for container "placeholder-1" on port 8080.
```

**Cause:** `GeminiService()` and `WhatsAppService()` were instantiated at module level (import time). If credentials were missing/empty, `genai.Client(api_key="")` raised an exception before uvicorn could start listening.

**Fix:** Made both service clients lazy — clients are created only on first use, not at import time:
```python
@property
def client(self) -> genai.Client:
    if self._client is None:
        self._client = genai.Client(api_key=settings.gemini_api_key)
    return self._client
```

---

## 9. Secret Manager — Secret Names Case Mismatch

**Error:**
```
Secret projects/.../secrets/twilio-account-sid/versions/latest was not found
```

**Cause:** `cloudbuild.yaml` referenced lowercase secret names (`twilio-account-sid`) but secrets were created with UPPERCASE names (`TWILIO_ACCOUNT_SID`) by the `setup_secrets.sh` script.

**Fix:** Updated `cloudbuild.yaml` to use uppercase names matching what exists in Secret Manager:
```yaml
--set-secrets=TWILIO_ACCOUNT_SID=TWILIO_ACCOUNT_SID:latest,...
```

---

## 10. Secret Manager — IAM Permission Denied

**Error:**
```
https://api.twilio.com/2010-04-01/Accounts//Messages.json  ← empty Account SID
```

**Cause:** The Cloud Run compute service account (`845708853463-compute@developer.gserviceaccount.com`) didn't have `roles/secretmanager.secretAccessor` on the secrets.

**Fix:**
```bash
for SECRET in TWILIO_ACCOUNT_SID TWILIO_AUTH_TOKEN TWILIO_WHATSAPP_NUMBER GEMINI_API_KEY; do
  gcloud secrets add-iam-policy-binding $SECRET \
    --member="serviceAccount:845708853463-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --project=fastapi-test-493805
done
```

---

## 11. Twilio Sandbox — 400 Bad Request on Initial Send

**Error:**
```
httpx.HTTPStatusError: Client error '400 Bad Request'
https://api.twilio.com/2010-04-01/Accounts/ACd.../Messages.json
```

**Cause:** The recipient's WhatsApp number had not joined the Twilio sandbox.

**Fix:** From the test WhatsApp number, send:
```
join <sandbox-keyword>
```
to `+1 415 523 8886`. Find your sandbox keyword at: Twilio Console → Messaging → Try it out → Send a WhatsApp message.

---

## 12. Background Task Killed Before Completing on Cloud Run

**Cause:** `asyncio.create_task(process_message(...))` fires a background task after the HTTP 200 response. Cloud Run can throttle the CPU after the response is sent, killing the task before Gemini finishes.

**Fix:** Replaced with FastAPI's `BackgroundTasks` which keeps the instance alive until the task completes:
```python
# Before
asyncio.create_task(process_message(message, sender))

# After
background_tasks.add_task(process_message, message, sender)
```

---

## 13. Twilio 400 on Final Response — Message Too Long

**Error:** Gemini analysis succeeded but sending the formatted response to WhatsApp returned 400.

**Cause:** Twilio WhatsApp has a 1600 character limit. The combined homeowner brief + pro brief + professional recommendations exceeded the limit.

**Fix:**
1. Split response into two separate messages (homeowner message + pro message)
2. Updated Gemini system prompt to enforce concise responses: each section under 400 chars, total under 800 chars
3. Added hard truncation at 1550 chars per message as a safety fallback

---

## Quick Reference — Deployment Checklist

```
□ .env has all 4 credentials (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,
     TWILIO_WHATSAPP_NUMBER, GEMINI_API_KEY)
□ Secrets exist in Secret Manager: gcloud secrets list --project=PROJECT_ID
□ Compute SA has secretAccessor role on all 4 secrets
□ Twilio webhook URL set to: https://YOUR-URL.run.app/webhook (HTTP POST)
□ Test WhatsApp number has joined sandbox: "join <keyword>" → +14155238886
□ Health check passes: curl https://YOUR-URL.run.app/health
```

---

**Last Updated:** 2026-05-09
**Project:** whatsapp-repair-bot / fastapi-test-493805

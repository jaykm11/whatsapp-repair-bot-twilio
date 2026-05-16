# Firestore setup for WhatsApp bot (project: fastapi-test-493805)

Use this on the **dev** branch. Production (`main`) is unchanged until you merge and deploy.

## 1. Create a Firestore database (Console)

1. Open [Firestore](https://console.cloud.google.com/firestore/databases?project=fastapi-test-493805).
2. If you see **Create database**:
   - Mode: **Firestore Native** (not Datastore mode).
   - Location: **us-central1** (same region as your Cloud Run service), **or** **nam5 (United States)** multi-region.
   - Enable for production use.
3. If a database already exists, note its **database ID** (usually `(default)`).

The app uses collection `whatsapp_repair_chats` — Firestore creates it on first write.

## 2. IAM for Cloud Run

1. [Cloud Run](https://console.cloud.google.com/run?project=fastapi-test-493805) → **whatsapp-repair-bot** (us-central1) → copy the **service account** email.
2. [IAM](https://console.cloud.google.com/iam-admin/iam?project=fastapi-test-493805) → find that account → **Grant access** (or edit):
   - Role: **Cloud Datastore User** (`roles/datastore.user`)

This allows read/write to Firestore.

## 3. Environment variables on Cloud Run (when you deploy dev)

On **whatsapp-repair-bot** (us-central1), add:

| Variable | Value |
|----------|--------|
| `CONVERSATION_BACKEND` | `firestore` |
| `CONVERSATION_MAX_MESSAGES` | `24` (optional) |
| `GOOGLE_CLOUD_PROJECT` | `fastapi-test-493805` (often set automatically) |

Keep existing Twilio/Gemini secrets as they are.

Deploy a **new revision** after changing env vars.

## 4. Verify in logs

After deploy, startup should log:

```text
Conversation backend=firestore max_messages=24
```

Send a few WhatsApp messages, then in Firestore console → **Data** → collection `whatsapp_repair_chats` → documents keyed by phone digits.

## 5. Local testing (optional)

```bash
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT=fastapi-test-493805
export CONVERSATION_BACKEND=firestore
PYTHONPATH=. python app/main.py
```

## Troubleshooting

| Error | Fix |
|-------|-----|
| `403 Missing or insufficient permissions` | Add `roles/datastore.user` to Cloud Run service account |
| `The database (default) does not exist` | Create Firestore database in console |
| Still `Conversation backend=memory` | Set `CONVERSATION_BACKEND=firestore` on Cloud Run and redeploy |

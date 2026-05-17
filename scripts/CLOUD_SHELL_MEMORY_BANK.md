# Memory Bank setup without installing gcloud (Cloud Shell)

Project: **fastapi-test-493805**

## 1. Open Cloud Shell

1. Go to https://console.cloud.google.com/
2. Select project **fastapi-test-493805** (top bar).
3. Click the **Cloud Shell** icon (terminal) — top right.

`gcloud` is already installed and you are logged in.

## 2. Clone your repo (or paste commands)

```bash
git clone https://github.com/YOUR_USER/whatsapp-repair-bot-twilio.git
cd whatsapp-repair-bot-twilio
```

If the repo is only local, upload `scripts/setup_memory_bank.py` in Cloud Shell:
**⋮ menu → Upload → select the file**.

## 3. Run setup (Python — recommended)

```bash
pip install -q 'google-cloud-aiplatform>=1.111.0'
python scripts/setup_memory_bank.py --project fastapi-test-493805 --region us-central1
```

List existing engines only (no create):

```bash
python scripts/setup_memory_bank.py --project fastapi-test-493805 --list-only
```

Copy the printed `VERTEX_AGENT_ENGINE_NAME=projects/.../reasoningEngines/...` into Cloud Run.

## 4. Or use the bash script (gcloud + curl)

```bash
chmod +x scripts/setup_memory_bank.sh
./scripts/setup_memory_bank.sh --project fastapi-test-493805 --region us-central1
```

## 5. Set Cloud Run env var

Console → Cloud Run → **whatsapp-repair-bot** → Edit → Variables:

| Name | Value |
|------|--------|
| `VERTEX_AGENT_ENGINE_NAME` | (full resource name from step 3) |
| `GOOGLE_CLOUD_REGION` | `us-central1` |

Ensure the Cloud Run service account has **Vertex AI User** (`roles/aiplatform.user`).

## Optional: install gcloud on Windows later

https://cloud.google.com/sdk/docs/install#windows

Then: `gcloud init` and `gcloud config set project fastapi-test-493805`

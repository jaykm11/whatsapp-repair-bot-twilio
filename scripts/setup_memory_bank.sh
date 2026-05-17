#!/usr/bin/env bash
# =============================================================================
# setup_memory_bank.sh
# Provision Vertex AI Agent Platform (Reasoning Engine) with Memory Bank using
# gcloud + REST — no Jupyter notebook required.
#
# Prerequisites:
#   - gcloud installed and authenticated: gcloud auth login
#   - Billing enabled on the project
#   - Agent Platform / Vertex AI API enabled (this script enables it if missing)
#
# Usage:
#   ./scripts/setup_memory_bank.sh
#   ./scripts/setup_memory_bank.sh --project fastapi-test-493805 --region us-central1
#   ./scripts/setup_memory_bank.sh --list-only
#
# After success, set on Cloud Run:
#   VERTEX_AGENT_ENGINE_NAME=projects/.../locations/.../reasoningEngines/...
# =============================================================================
set -euo pipefail

export PATH="$PATH:/usr/local/google-cloud-sdk/bin:$HOME/google-cloud-sdk/bin:/opt/homebrew/bin"

PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-us-central1}"
DISPLAY_NAME="${DISPLAY_NAME:-whatsapp-repair-memory-bank}"
LIST_ONLY=false
CLOUD_RUN_SERVICE="${CLOUD_RUN_SERVICE:-whatsapp-repair-bot}"

while [[ $# -gt 0 ]]; do
  case $1 in
    --project) PROJECT_ID="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    --display-name) DISPLAY_NAME="$2"; shift 2 ;;
    --list-only) LIST_ONLY=true; shift ;;
    --cloud-run-service) CLOUD_RUN_SERVICE="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$PROJECT_ID" ]]; then
  PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
fi
if [[ -z "$PROJECT_ID" ]]; then
  echo "ERROR: Set a project: gcloud config set project YOUR_PROJECT_ID  or  --project YOUR_PROJECT_ID"
  exit 1
fi

echo "==> Project: $PROJECT_ID"
echo "==> Region:  $REGION"

# Agent Platform uses the Vertex AI API surface (aiplatform.googleapis.com).
echo "==> Enabling Vertex AI API (if needed)..."
gcloud services enable aiplatform.googleapis.com --project="$PROJECT_ID"

TOKEN=$(gcloud auth print-access-token)
BASE="https://${REGION}-aiplatform.googleapis.com/v1beta1"
PARENT="projects/${PROJECT_ID}/locations/${REGION}"

list_engines() {
  curl -sS -H "Authorization: Bearer ${TOKEN}" \
    "${BASE}/${PARENT}/reasoningEngines" | python3 -m json.tool 2>/dev/null \
    || curl -sS -H "Authorization: Bearer ${TOKEN}" "${BASE}/${PARENT}/reasoningEngines"
}

echo ""
echo "==> Existing Reasoning Engines (Agent Platform instances):"
list_engines

if [[ "$LIST_ONLY" == true ]]; then
  echo ""
  echo "Done (--list-only). If you see a reasoningEngine, copy its 'name' to VERTEX_AGENT_ENGINE_NAME."
  exit 0
fi

# Minimal Memory Bank config (same defaults as Google quickstart).
EMBED_MODEL="projects/${PROJECT_ID}/locations/${REGION}/publishers/google/models/text-embedding-005"
GEN_MODEL="projects/${PROJECT_ID}/locations/${REGION}/publishers/google/models/gemini-2.5-flash"

BODY=$(cat <<EOF
{
  "displayName": "${DISPLAY_NAME}",
  "description": "Memory Bank for WhatsApp home repair bot",
  "contextSpec": {
    "memoryBankConfig": {
      "similaritySearchConfig": {
        "embeddingModel": "${EMBED_MODEL}"
      },
      "generationConfig": {
        "model": "${GEN_MODEL}"
      }
    }
  }
}
EOF
)

echo ""
echo "==> Creating Reasoning Engine with Memory Bank (may take 1–3 minutes)..."
OP=$(curl -sS -X POST \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "${BODY}" \
  "${BASE}/${PARENT}/reasoningEngines")

echo "$OP" | python3 -m json.tool 2>/dev/null || echo "$OP"

# Long-running operation — poll until done.
OP_NAME=$(echo "$OP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('name',''))" 2>/dev/null || true)
if [[ -n "$OP_NAME" ]]; then
  echo "==> Waiting for operation: $OP_NAME"
  for _ in $(seq 1 60); do
    sleep 5
    RESULT=$(curl -sS -H "Authorization: Bearer ${TOKEN}" \
      "https://${REGION}-aiplatform.googleapis.com/v1beta1/${OP_NAME}")
    DONE=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('done', False))" 2>/dev/null || echo "False")
    if [[ "$DONE" == "True" ]]; then
      ENGINE_NAME=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('response',{}); print(r.get('name',''))" 2>/dev/null || true)
      echo ""
      echo "=============================================="
      echo "SUCCESS. Add to Cloud Run / .env:"
      echo "VERTEX_AGENT_ENGINE_NAME=${ENGINE_NAME}"
      echo "GOOGLE_CLOUD_REGION=${REGION}"
      echo "=============================================="
      break
    fi
    echo "   ... still creating"
  done
fi

# Grant Cloud Run service account Vertex AI User (for Memory Bank at runtime).
echo ""
echo "==> Granting roles/aiplatform.user to Cloud Run service account (if service exists)..."
CR_SA=$(gcloud run services describe "$CLOUD_RUN_SERVICE" \
  --project="$PROJECT_ID" --region="$REGION" \
  --format='value(spec.template.spec.serviceAccountName)' 2>/dev/null || true)

if [[ -n "$CR_SA" && "$CR_SA" != "null" ]]; then
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CR_SA}" \
    --role="roles/aiplatform.user" \
    --condition=None \
    --quiet >/dev/null 2>&1 || true
  echo "    Granted roles/aiplatform.user to: $CR_SA"
else
  echo "    Cloud Run service '$CLOUD_RUN_SERVICE' not found in $REGION — skip IAM or set manually."
fi

echo ""
echo "Next: implement app/services/memory_bank.py and set VERTEX_AGENT_ENGINE_NAME on deploy."

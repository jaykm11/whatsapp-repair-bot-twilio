#!/usr/bin/env bash
# =============================================================================
# setup_secrets.sh
# Reads .env and creates/updates every secret in GCP Secret Manager.
# Compatible with bash 3 (macOS default) — no associative arrays used.
#
# Usage:
#   ./scripts/setup_secrets.sh                        # auto-detect project
#   ./scripts/setup_secrets.sh --project my-project   # explicit project
#   ./scripts/setup_secrets.sh --env path/to/.env     # custom .env path
# =============================================================================
set -euo pipefail

# Add common gcloud installation paths so the script works without sourcing ~/.zshrc
export PATH="$PATH:/usr/local/google-cloud-sdk/bin:$HOME/google-cloud-sdk/bin:/opt/homebrew/bin:/usr/local/bin"

# ---------- defaults ---------------------------------------------------------
PROJECT_ID="fastapi-test-493805"
ENV_FILE="$(dirname "$0")/../.env"

# ---------- keys that go into Secret Manager (skip plain config values) ------
SECRET_KEYS="TWILIO_ACCOUNT_SID TWILIO_AUTH_TOKEN TWILIO_WHATSAPP_NUMBER GEMINI_API_KEY"

# ---------- parse args -------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case $1 in
    --project) PROJECT_ID="$2"; shift 2 ;;
    --env)     ENV_FILE="$2";   shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# ---------- resolve project --------------------------------------------------
if [[ -z "$PROJECT_ID" ]]; then
  PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
fi
if [[ -z "$PROJECT_ID" ]]; then
  echo "ERROR: No GCP project set. Run 'gcloud config set project YOUR_PROJECT_ID' or pass --project."
  exit 1
fi

# ---------- check .env exists ------------------------------------------------
ENV_FILE="$(cd "$(dirname "$ENV_FILE")" && pwd)/$(basename "$ENV_FILE")"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env file not found at $ENV_FILE"
  exit 1
fi

echo "Project : $PROJECT_ID"
echo ".env    : $ENV_FILE"
echo ""

# ---------- helper: get a value from .env for a given key -------------------
get_env_value() {
  local key="$1"
  grep -E "^${key}=" "$ENV_FILE" | head -1 | cut -d'=' -f2- | xargs
}

# ---------- create/update each secret ----------------------------------------
for KEY in $SECRET_KEYS; do
  VALUE="$(get_env_value "$KEY")"

  if [[ -z "$VALUE" ]]; then
    echo "SKIP   $KEY  (not set in .env)"
    continue
  fi

  if gcloud secrets describe "$KEY" \
       --project="$PROJECT_ID" \
       --format="value(name)" \
       >/dev/null 2>&1; then
    echo -n "$VALUE" | gcloud secrets versions add "$KEY" \
      --data-file=- \
      --project="$PROJECT_ID"
    echo "UPDATED $KEY"
  else
    echo -n "$VALUE" | gcloud secrets create "$KEY" \
      --data-file=- \
      --replication-policy=automatic \
      --project="$PROJECT_ID"
    echo "CREATED $KEY"
  fi
done

echo ""
echo "All secrets synced to project '$PROJECT_ID'."
echo ""

# ---------- optional: grant Cloud Run SA access ------------------------------
echo "Checking Cloud Run service account..."
CR_SA=$(gcloud run services describe whatsapp-repair-bot \
  --region=us-central1 \
  --project="$PROJECT_ID" \
  --format="value(spec.template.spec.serviceAccountName)" 2>/dev/null || true)

if [[ -n "$CR_SA" ]]; then
  echo "Granting secretAccessor to: $CR_SA"
  for KEY in $SECRET_KEYS; do
    gcloud secrets add-iam-policy-binding "$KEY" \
      --member="serviceAccount:$CR_SA" \
      --role="roles/secretmanager.secretAccessor" \
      --project="$PROJECT_ID" \
      --condition=None \
      >/dev/null 2>&1 && echo "  OK $KEY -> $CR_SA" || true
  done
else
  echo "  (Cloud Run service not found yet - IAM grants skipped, re-run after first deploy)"
fi

echo ""
echo "Done. Trigger a new Cloud Run deploy to pick up the latest secret versions."

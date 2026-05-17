# Dev branch handoff — Firestore + Memory Bank

For reviewers deploying **`dev`** (not `main`). Production on `main` is unchanged until this branch is merged and built.

**Project:** `fastapi-test-493805`  
**Cloud Run service:** `whatsapp-repair-bot` (us-central1, Container)  
**Twilio webhook:** same URL as today — unchanged by this work.

---

## GCP setup (already done)

| Item | Status |
|------|--------|
| Firestore Native DB in `us-central1` (`(default)`) | Created |
| IAM `roles/datastore.user` on `845708853463-compute@developer.gserviceaccount.com` | Granted |
| Vertex Reasoning Engine + Memory Bank | Created |
| Cloud Run env: `CONVERSATION_BACKEND=firestore` | Set |
| Cloud Run env: `VERTEX_AGENT_ENGINE_NAME`, `GOOGLE_CLOUD_REGION=us-central1` | Set |
| Twilio / Gemini secrets | Unchanged |

---

## What this branch adds

| Layer | File(s) | Role |
|-------|---------|------|
| Short-term chat | `app/services/conversation_store.py` | Last ~24 turns per phone in Firestore (`whatsapp_repair_chats`) |
| Long-term facts | `app/services/memory_bank.py` | Vertex Memory Bank per phone (`user_id` = digits) |
| Orchestration | `app/services/agent.py` | Text chat + image flows use both |
| Config | `app/config.py` | `CONVERSATION_BACKEND`, Vertex env vars |
| Chat model | `app/services/gemini.py` | `chat_reply()` with optional memory facts |

Setup guides:

- `scripts/CLOUD_SHELL_FIRESTORE.md`
- `scripts/CLOUD_SHELL_MEMORY_BANK.md`
- `scripts/setup_firestore.sh` / `scripts/setup_memory_bank.py`

---

## Message flow

### Text (non-welcome)

1. Load prior turns from Firestore.
2. Retrieve Memory Bank facts (similarity search on user message).
3. Gemini reply using history + facts.
4. Append user + assistant turns to Firestore.
5. Append exchange to Memory Bank session + trigger `memories.generate` (async).

### Text (`hi` / `help` / etc.)

- Sends welcome message; stores turns in Firestore only (no Memory Bank retrieve).

### Image

1. Store photo note in Firestore.
2. Existing Gemini image diagnosis + pro recommendations.
3. Store diagnosis summary in Firestore + Memory Bank.

### Graceful degradation

- **`VERTEX_AGENT_ENGINE_NAME` unset** → Memory Bank skipped; bot still runs.
- **Firestore errors** → logged; may break chat persistence (check IAM + `CONVERSATION_BACKEND=firestore`).

---

## Expected startup logs

```text
All credentials loaded. Service ready.
Conversation backend=firestore max_messages=24
Memory Bank enabled (region=us-central1)
```

If Memory Bank is disabled:

```text
Memory Bank disabled (VERTEX_AGENT_ENGINE_NAME not set)
```

---

## Deploy checklist

1. Merge or build from **`dev`** (Cloud Build → updates us-central1 container).
2. Confirm Cloud Run env vars (see GCP table above).
3. Deploy new revision.
4. Run the tests in **[TESTING_FIRESTORE_MEMORY_BANK.md](./TESTING_FIRESTORE_MEMORY_BANK.md)**.

---

## Known limitations

These are intentional tradeoffs for v1, not necessarily bugs.

### 1. New Vertex session per Memory Bank write

`memory_bank.py` creates a **new** Agent Engine session on each `record_exchange` call (no persisted `session_name` per user yet).

- **Effect:** Memories still generate, but consolidation across many short sessions can be slower or noisier than one long-lived session per phone.
- **Future improvement:** Store `vertex_session_name` on the Firestore user doc and reuse it.

### 2. Firestore append without transactions

`conversation_store.py` uses read → modify → write for `turns[]`.

- **Effect:** Fine for normal WhatsApp traffic. A rare race is possible if two messages from the same user arrive at the exact same time on different Cloud Run instances.
- **Future improvement:** Firestore transaction or subcollection per turn.

### 3. Broad default service account

Cloud Run uses `845708853463-compute@developer.gserviceaccount.com` with **`roles/editor`** (plus `datastore.user`).

- **Effect:** Works for a small project; broader than least-privilege.
- **Future improvement:** Dedicated runtime SA with only `datastore.user`, `secretmanager.secretAccessor`, `aiplatform.user`.

### 4. Memory Bank generation is async

`memories.generate` uses `wait_for_completion=False`.

- **Effect:** Facts may not appear for the **next** message immediately; allow a short delay when testing.
- **Not a bug:** Avoids Twilio webhook timeouts.

### 5. Welcome path skips Memory Bank retrieve

`hi` / `help` only update Firestore, not long-term memory retrieval.

- **Effect:** First message after welcome won't include Memory Bank facts until the user sends a normal text message.

### 6. `main` vs `dev`

Until `dev` is merged and deployed, production runs older code (image-only / no Firestore chat).

- **Effect:** GCP env vars alone do not change behavior until the **dev** image is live.

### 7. User-facing copy is plain text

Emoji were removed from `agent.py` and `professional_matcher.py` to avoid Windows/encoding issues in the repo.

---

## Branch layout

| Branch | Purpose |
|--------|---------|
| `main` | Matches remote; production baseline |
| `dev` | Firestore + Memory Bank + setup scripts |

---

## Quick troubleshooting

| Symptom | Check |
|---------|--------|
| `Conversation backend=memory` in logs | Set `CONVERSATION_BACKEND=firestore` and redeploy |
| Firestore permission denied | `roles/datastore.user` on Cloud Run SA |
| Memory Bank warnings in logs | `VERTEX_AGENT_ENGINE_NAME`, `GOOGLE_CLOUD_REGION`, `roles/aiplatform.user` (or Editor SA) |
| No collection in Firestore | Send at least one message after deploy; collection is created on first write |
| Chat still says "send a photo" only | Old `main` image still deployed — deploy `dev` |

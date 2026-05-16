# Testing Firestore + Memory Bank

Quick checklist for verifying **`dev`** on Cloud Run (`whatsapp-repair-bot`, **us-central1**, project `fastapi-test-493805`).

See also: [DEV_BRANCH_HANDOFF.md](./DEV_BRANCH_HANDOFF.md) for setup context and known limitations.

---

## Prerequisites

1. **`dev`** image deployed (not old `main` image-only build).
2. Cloud Run env vars set:

| Variable | Value |
|----------|--------|
| `CONVERSATION_BACKEND` | `firestore` |
| `VERTEX_AGENT_ENGINE_NAME` | `projects/.../reasoningEngines/...` |
| `GOOGLE_CLOUD_REGION` | `us-central1` |

3. Tester’s phone joined to Twilio WhatsApp sandbox (or production sender).

---

## Step 1 — Startup logs

**Cloud Run → `whatsapp-repair-bot` → Logs** (latest revision).

**Pass:**

```text
All credentials loaded. Service ready.
Conversation backend=firestore max_messages=24
Conversation store: Firestore (max_messages=24)
Memory Bank enabled (region=us-central1)
```

**Fail:**

| Log line | Fix |
|----------|-----|
| `Conversation backend=memory` | Set `CONVERSATION_BACKEND=firestore`, redeploy |
| `Memory Bank disabled` | Set `VERTEX_AGENT_ENGINE_NAME`, redeploy |
| `Conversation store: in-memory` | Same as Firestore backend |

---

## Step 2 — Firestore (short-term chat)

**Collection:** `whatsapp_repair_chats`  
**Document ID:** digits only from phone (`whatsapp:+15551234567` → `15551234567`)

### WhatsApp messages

| # | Send |
|---|------|
| 1 | `hi` |
| 2 | `My kitchen faucet drips every night` |
| 3 | `What problem did I mention in my last message?` |

### Verify

**Firestore → Data → `whatsapp_repair_chats` →** open doc for tester’s phone.

- [ ] `turns[]` grows after each message (`role`, `content`, `ts`)
- [ ] `updated_at` changes
- [ ] Message 3 mentions the **faucet** (uses recent history)

**If broken:** check IAM `roles/datastore.user` on `845708853463-compute@developer.gserviceaccount.com`; check Cloud Run logs for errors.

---

## Step 3 — Memory Bank (long-term facts)

Generation is **async** — wait **2–3 minutes** between storing a fact and asking about it.

Welcome (`hi`) does **not** use Memory Bank retrieve; use normal text messages.

### WhatsApp messages

| # | Send |
|---|------|
| 1 | `Please remember: my gate code is 4455 and I live on Oak Street.` |
| 2 | *(wait 2–3 min)* |
| 3 | `What is my gate code?` |

**Optional (photo path):**

| # | Send |
|---|------|
| 4 | Photo + caption `leaking under the sink` |
| 5 | Later: `What did you find when I sent the sink photo?` |

### Verify

- [ ] Reply to message 3 mentions **4455** or **Oak Street** (Gemini may paraphrase)
- [ ] Cloud Run logs have **no** `Memory Bank retrieve failed` or `Memory Bank record_exchange failed`

**If broken:** verify `VERTEX_AGENT_ENGINE_NAME` and `GOOGLE_CLOUD_REGION=us-central1`; check Vertex AI User on Cloud Run service account.

There is no “success” log for Memory Bank — absence of warnings + recall in chat is the signal.

---

## Step 4 — Both together

| # | Send | Tests |
|---|------|--------|
| 1 | `hi` | Firestore write (welcome) |
| 2 | `I have a slow leak in the upstairs bathroom` | Firestore + Memory record |
| 3 | *(wait 2 min)* | Memory indexing |
| 4 | `Which room did I say had the leak?` | Firestore (recent turns) |
| 5 | `What household issues have we discussed?` | Firestore + Memory retrieve |

- [ ] Step 4 correct (upstairs / bathroom)
- [ ] Step 5 reasonably summarizes prior issues

---

## Step 5 — Logs while testing

**Logs Explorer** filter:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="whatsapp-repair-bot"
("Memory Bank" OR "Conversation store" OR "Processing message")
```

| Log | Meaning |
|-----|---------|
| `Processing message from ... type: text` | Webhook handled |
| `Memory Bank retrieve failed` | Retrieve broken |
| `Memory Bank record_exchange failed` | Write/generate broken |
| `Error processing message` | Check stack trace (often Firestore or Gemini) |

---

## Optional — curl (Firestore only)

Replace URL and phone:

```bash
curl -X POST "https://YOUR-CLOUD-RUN-URL/webhook" \
  -d "MessageSid=SMtest001" \
  -d "From=whatsapp:+15551234567" \
  -d "To=whatsapp:+14155238886" \
  -d "Body=Test+firestore+message" \
  -d "NumMedia=0"
```

Then check Firestore doc **`15551234567`** for new `turns[]`.

---

## Pass / fail summary

| Feature | Pass |
|---------|------|
| **Firestore** | Startup `firestore`; doc exists with growing `turns[]`; bot recalls last few messages |
| **Memory Bank** | Startup `Memory Bank enabled`; no Memory Bank warnings; unique fact recalled after wait |
| **Both** | Multi-turn chat + optional photo follow-up feel continuous |

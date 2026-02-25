# WhatsApp AI Agent Workspace

A **proactive, autonomous AI agent** built with [Agno](https://agno.com) and
[Perplexity](https://perplexity.ai), connected to WhatsApp via the Meta Cloud API.

## Architecture

```
WhatsApp Cloud API
        │
        ▼
  app/main.py          ← FastAPI webhook receiver
        │
        ▼
  app/agents/
  ├── orchestrator.py  ← PlannerAgent: decompose → execute → self-correct
  ├── proactive.py     ← Heartbeat scanner (OpenClaw-style autonomous loop)
  └── schemas.py       ← Pydantic data models (Subtask, Plan, WorkingBuffer)
        │
        ▼
  storage/
  ├── working_buffer.json  ← current active plan state
  └── wal.jsonl            ← append-only event log
```

## Key Features

- **Task Decomposition** — PlannerAgent breaks messages into 3-5 atomic subtasks
- **Perplexity Search** — Real-time grounded intelligence via `PerplexitySearch` tool
- **Self-Correction** — Agent evaluates each subtask output and retries up to 2× if unsatisfactory
- **Heartbeat Loop** — `proactive.py` runs autonomously, scanning buffer and surfacing next actions
- **WAL Logging** — Every event appended to `storage/wal.jsonl` for full auditability

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env — at minimum set PERPLEXITY_API_KEY + WhatsApp tokens

# 3. Run the webhook server
uvicorn app.main:app --reload

# 4. (Separate terminal) Run the proactive heartbeat scanner
python -m app.agents.proactive

# 5. Expose to internet and configure in Meta Developer Portal
ngrok http 8000
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `PERPLEXITY_API_KEY` | ✅ | Perplexity API key |
| `WHATSAPP_VERIFY_TOKEN` | ✅ | Token for Meta webhook verification |
| `WHATSAPP_ACCESS_TOKEN` | ✅ | Meta Cloud API access token |
| `WHATSAPP_PHONE_NUMBER_ID` | ✅ | Your WhatsApp phone number ID |
| `HEARTBEAT_INTERVAL` | ❌ | Proactive scan interval in seconds (default: 30) |
| `OPENAI_API_KEY` | ❌ | Optional fallback LLM |
| `PGVECTOR_DB_URL` | ❌ | Postgres URL for persistent memory |
| `PORT` | ❌ | Server port (default: 8000) |

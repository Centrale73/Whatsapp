# WhatsApp Agent Workspace (Agno + Perplexity)

This repository contains an AI Agent workspace that connects to WhatsApp and leverages **Agno** and **Perplexity** to decompose tasks and act proactively.

## Architecture

1.  **FastAPI Webhook**: Receives messages from WhatsApp.
2.  **Orchestrator**: Uses Perplexity to decompose user requests into structured plans (JSON).
3.  **Proactive Scanner**: Runs on a schedule to check for stalled tasks and suggest actions (OpenClaw style).
4.  **Storage**:
    *   `storage/working_buffer.json`: Current state of active plans.
    *   `storage/wal.jsonl`: Append-only log of all events.

## Setup

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  Set up environment variables in `.env`:
    *   `WHATSAPP_VERIFY_TOKEN`
    *   `PERPLEXITY_API_KEY`
    *   `OPENAI_API_KEY` (if using Agno default models too)
3.  Run the server:
    ```bash
    uvicorn app.main:app --reload
    ```
4.  Expose to internet (e.g., using ngrok) and configure WhatsApp Webhook.

## Proactive Loop
Run the scanner separately:
```bash
python app/agents/proactive.py
```

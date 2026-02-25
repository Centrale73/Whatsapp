import os
import json
import logging

import httpx
from fastapi import FastAPI, Request, BackgroundTasks
from dotenv import load_dotenv

from app.agents.orchestrator import orchestrator

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="WhatsApp AI Agent Workspace")

WHATSAPP_ACCESS_TOKEN    = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_VERIFY_TOKEN    = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")


# ── Health ────────────────────────────────────────────────────────────────

@app.get("/")
def health():
    return {"status": "Agent Workspace Active"}


# ── Webhook Verification (Meta handshake) ─────────────────────────────────

@app.get("/webhook")
def verify_webhook(request: Request):
    mode      = request.query_params.get("hub.mode")
    token     = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verified by Meta.")
        return int(challenge)

    logger.warning("Webhook verification failed — token mismatch.")
    return {"error": "Verification failed"}, 403


# ── Incoming Message Receiver ─────────────────────────────────────────────

@app.post("/webhook")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives WhatsApp Cloud API events.
    Returns 200 immediately; heavy processing runs in background.
    """
    data = await request.json()
    logger.info(f"Raw webhook payload: {json.dumps(data)[:500]}")

    try:
        changes  = data["entry"][0]["changes"][0]["value"]
        messages = changes.get("messages", [])
        if not messages:
            return {"status": "no_message"}

        message    = messages[0]
        sender_id  = message["from"]
        text       = message.get("text", {}).get("body", "").strip()

        if text:
            background_tasks.add_task(_handle_message, sender_id, text)
        else:
            logger.info("Non-text message received — skipped.")

    except (KeyError, IndexError) as exc:
        logger.error(f"Webhook parse error: {exc}")

    return {"status": "received"}


# ── Background Message Handler ────────────────────────────────────────────

async def _handle_message(sender_id: str, text: str):
    """Run orchestrator pipeline and send reply via WhatsApp Cloud API."""
    try:
        response_text = orchestrator.process_message(text)
        await _send_whatsapp_message(sender_id, response_text)
    except Exception as exc:
        logger.error(f"Error handling message from {sender_id}: {exc}", exc_info=True)


async def _send_whatsapp_message(to: str, body: str):
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type":  "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to":   to,
        "type": "text",
        "text": {"body": body},
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=payload)
        logger.info(f"Sent to {to} → HTTP {resp.status_code}")


# ── Dev entrypoint ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

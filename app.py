import os
import uuid
import json
import re
import logging
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from agent import create_appointment_agent
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Appointment Setter")

# ── Twilio setup ──────────────────────────────────────────────────────────
account_sid   = os.getenv('TWILIO_ACCOUNT_SID')
auth_token    = os.getenv('TWILIO_AUTH_TOKEN')
twilio_client = Client(account_sid, auth_token) if account_sid and auth_token else None
SANDBOX_FROM  = "whatsapp:+14155238886"  # Twilio sandbox number (no business account needed)
OWNER_WA      = f"whatsapp:{os.getenv('OWNER_WHATSAPP', '')}"


def notify_owner(appt: dict):
    """Send appointment summary to your personal WhatsApp via Twilio sandbox."""
    if not twilio_client or not os.getenv('OWNER_WHATSAPP'):
        logger.warning("Twilio not configured or OWNER_WHATSAPP missing.")
        return
    body = (
        f"\U0001f4c5 New Appointment\n"
        f"\U0001f464 Person: {appt['person']}\n"
        f"\U0001f4cb Subject: {appt['subject']}\n"
        f"\u23f0 Time: {appt['time']}"
    )
    msg = twilio_client.messages.create(from_=SANDBOX_FROM, body=body, to=OWNER_WA)
    logger.info(f"Appointment notification sent: {msg.sid}")


def extract_booking(response_text: str):
    """Parse BOOK:{...} signal from agent response. Returns (clean_text, appt_dict|None)."""
    match = re.search(r'BOOK:(\{.*?\})', response_text)
    if match:
        try:
            appt = json.loads(match.group(1))
            clean = re.sub(r'BOOK:\{.*?\}', '', response_text).strip()
            return clean, appt
        except json.JSONDecodeError:
            pass
    return response_text, None


# ── Web chat endpoint (for website UI) ─────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


@app.get("/", response_class=HTMLResponse)
async def root():
    with open("templates/index.html") as f:
        return f.read()


@app.post("/chat")
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    agent = create_appointment_agent(session_id)
    result = agent.run(req.message)
    response_text = result.content if hasattr(result, 'content') else str(result)

    response_text, appt = extract_booking(response_text)
    if appt:
        notify_owner(appt)

    return {"session_id": session_id, "response": response_text}


# ── WhatsApp webhook (for direct WhatsApp bookings) ───────────────────────
def process_webhook_background(sender_number: str, incoming_msg: str):
    try:
        session_id = f"wa_{sender_number.replace('whatsapp:+', '')}"
        agent = create_appointment_agent(session_id)
        result = agent.run(incoming_msg)
        response_text = result.content if hasattr(result, 'content') else str(result)

        response_text, appt = extract_booking(response_text)
        if appt:
            notify_owner(appt)

        if twilio_client:
            twilio_client.messages.create(
                from_=SANDBOX_FROM,
                body=response_text,
                to=sender_number
            )
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)


@app.post("/webhook")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    form_data = await request.form()
    incoming_msg = form_data.get('Body', '').strip()
    sender_number = form_data.get('From', '')
    if not incoming_msg:
        return {"status": "no message"}
    background_tasks.add_task(process_webhook_background, sender_number, incoming_msg)
    resp = MessagingResponse()
    return str(resp)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

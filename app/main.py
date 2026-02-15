from fastapi import FastAPI, Request
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

class WhatsAppMessage(BaseModel):
    object: str
    entry: list

@app.get("/")
def read_root():
    return {"status": "Agent Workspace Active"}

@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    """
    Webhook endpoint for WhatsApp messages.
    This will serve as the entry point for the agentic workflow.
    """
    data = await request.json()
    # TODO: Parse incoming message
    # TODO: Send to Agent Orchestrator (Perplexity + Agno)
    # TODO: Log to WAL
    print(f"Received webhook data: {data}")
    return {"status": "received"}

@app.get("/webhook")
def verify_webhook(request: Request):
    """
    Verification endpoint for WhatsApp Cloud API setup.
    """
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == verify_token:
            return int(challenge)
        else:
            return {"status": "error", "message": "Verification failed"}, 403
    return {"status": "error", "message": "Missing parameters"}, 400

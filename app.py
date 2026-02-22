import os
import logging
from fastapi import FastAPI, Request, BackgroundTasks, Form
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from agent import get_whatsapp_agent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure structured logging for observability (Metric: Defect Rate tracking)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize Twilio Client for asynchronous responses (Avoiding 15s timeout defect)
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_client = Client(account_sid, auth_token) if account_sid and auth_token else None
twilio_number = os.getenv('TWILIO_PHONE_NUMBER')

# Initialize Agent
agent = get_whatsapp_agent()

def process_message_background(sender_number: str, incoming_msg: str):
    """
    Background task to process the message and send response asynchronously.
    This decouples processing time from the Twilio webhook timeout.
    """
    try:
        logger.info(f"Processing message from {sender_number}: {incoming_msg}")
        
        # Run agent logic (Sync or Async)
        # Using .run() as per Agno documentation for sync execution
        response = agent.run(incoming_msg)
        
        # Extract content safely
        response_text = response.content if hasattr(response, 'content') else str(response)

        # Send response back via Twilio API
        if twilio_client and twilio_number:
            message = twilio_client.messages.create(
                from_=twilio_number,
                body=response_text,
                to=sender_number
            )
            logger.info(f"Response sent to {sender_number}: {message.sid}")
        else:
            logger.warning("Twilio credentials not configured. Response not sent.")
            
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        # Optionally send error message to user

@app.post("/webhook")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook endpoint for Twilio.
    Returns 200 OK immediately and processes in background to avoid timeout.
    """
    # Parse form data from Twilio
    form_data = await request.form()
    incoming_msg = form_data.get('Body', '').strip()
    sender_number = form_data.get('From', '')

    if not incoming_msg:
        logger.info("Empty message received")
        return {"status": "no message"}

    # Add processing task to background
    background_tasks.add_task(process_message_background, sender_number, incoming_msg)

    # Return empty TwiML to acknowledge receipt without replying immediately
    resp = MessagingResponse()
    return str(resp)

if __name__ == "__main__":
    import uvicorn
    # Use environment port for deployment flexibility
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

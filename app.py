from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from agent import get_whatsapp_agent
import os

app = Flask(__name__)
# Initialize agent lazily or globally depending on preference
agent = get_whatsapp_agent()

@app.route("/webhook", methods=['POST'])
def whatsapp_webhook():
    # Get the incoming message body and sender
    incoming_msg = request.values.get('Body', '').lower()
    sender_number = request.values.get('From', '')

    print(f"Received message from {sender_number}: {incoming_msg}")

    # Process message through Agno Agent
    # Note: For production, use an async queue or background task to avoid Twilio 15s timeout
    try:
        response = agent.run(incoming_msg)
        response_text = response.content
    except Exception as e:
        response_text = "I encountered an error processing your request."
        print(f"Error: {e}")
    
    # Generate TwiML response
    resp = MessagingResponse()
    msg = resp.message()
    msg.body(response_text)

    return str(resp)

if __name__ == "__main__":
    # Ensure PERPLEXITY_API_KEY is set in environment
    if not os.getenv("PERPLEXITY_API_KEY"):
        print("CRITICAL: PERPLEXITY_API_KEY not found in environment.")
    
    # Run server (use gunicorn in production)
    app.run(port=5000, debug=True)

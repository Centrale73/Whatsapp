from agno.agent import Agent
from agno.models.perplexity import Perplexity
import os

def get_whatsapp_agent():
    """
    Returns a production-grade Agno Agent configured with Perplexity.
    Includes explicit instruction tuning for WhatsApp constraints.
    """
    # Check for API key
    if not os.getenv("PERPLEXITY_API_KEY"):
        print("WARNING: PERPLEXITY_API_KEY not found in environment.")

    return Agent(
        name="PerplexityWhatsAppAgent",
        model=Perplexity(id="sonar-pro"),
        description="A high-performance research agent connected to WhatsApp.",
        instructions=[
            "You are a helpful assistant responding via WhatsApp.",
            "Provide concise, accurate answers.",
            "Use Markdown formatting sparingly as it may vary across WhatsApp clients.",
            "Prioritize brevity and clarity due to mobile screen constraints.",
            "Always leverage your web-search capabilities for up-to-date info.",
            "If the query requires complex reasoning, break it down step-by-step."
        ],
        markdown=True,
        show_tool_calls=True, # For debugging/logging
        add_history_to_messages=True, # Enable memory for context
    )

from agno.agent import Agent
from agno.models.perplexity import Perplexity
import os

def get_whatsapp_agent():
    """
    Returns an Agno Agent configured with Perplexity for high-reasoning web-search tasks.
    """
    return Agent(
        name="PerplexityWhatsAppAgent",
        model=Perplexity(id="sonar-pro"),
        description="A high-performance research agent connected to WhatsApp.",
        instructions=[
            "You are a helpful assistant responding via WhatsApp.",
            "Provide concise, accurate answers.",
            "Use Markdown formatting sparingly as it may vary across WhatsApp clients.",
            "Always leverage your web-search capabilities for up-to-date info."
        ],
        markdown=True
    )

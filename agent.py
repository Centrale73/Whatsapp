import os
from agno.agent import Agent
from agno.models.perplexity import Perplexity
from agno.storage.sqlite import SqliteStorage
from pydantic import BaseModel, Field

# ── Structured Output Model ────────────────────────────────────────────────
class AppointmentDetails(BaseModel):
    subject: str = Field(..., description="The purpose of the appointment.")
    person_name: str = Field(..., description="Full name of the person.")
    preferred_time: str = Field(..., description="The date and time requested.")

def get_appointment_agent(session_id: str) -> Agent:
    """
    Factory to generate a production-ready Agno agent.
    Optimized for conversational flow on WhatsApp with session isolation.
    """
    return Agent(
        name="WhatsAppSetter",
        model=Perplexity(id="sonar"), # Fast, grounded, and cost-effective
        session_id=session_id,
        storage=SqliteStorage(
            table_name="agent_memory",
            db_file="storage/whatsapp_agent.db"
        ),
        description=(
            "You are a professional assistant for WhatsApp. "
            "Your primary goal is to schedule appointments. "
            "If the user asks general questions, use your Perplexity search "
            "to answer them accurately, but always gently steer back to booking."
        ),
        instructions=[
            "1. Be concise; WhatsApp users prefer short messages.",
            "2. Collect: Name, Subject, and Time.",
            "3. Ask for only one missing piece of information at a time.",
            "4. When all info is gathered, confirm the details with the user.",
            "5. After confirmation, use the 'set_appointment' signal."
        ],
        # Persistent memory configuration
        add_history_to_messages=True,
        num_history_responses=12,
        markdown=False, # WhatsApp has limited markdown support
    )

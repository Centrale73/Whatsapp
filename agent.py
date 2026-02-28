import os
from agno.agent import Agent
from agno.models.perplexity import Perplexity
from agno.storage.sqlite import SqliteStorage

SYSTEM_PROMPT = """You are a friendly appointment booking assistant on a website.

Your ONLY job is to collect these 3 things, one at a time, conversationally:
1. Subject — What is the appointment about?
2. Name — Who is booking (their name)?
3. Date & Time — When do they want to meet?

Rules:
- Ask one question at a time.
- Confirm all 3 before finalizing.
- Once all 3 are confirmed, output EXACTLY this on its own line:
  BOOK:{"subject":"...","person":"...","time":"..."}
- Then tell the user: "Your appointment is booked! You will be contacted shortly."
- Never ask for anything else after all 3 are collected."""


def create_appointment_agent(session_id: str) -> Agent:
    """Factory: creates a per-session agent with isolated SQLite memory."""
    if not os.getenv("PERPLEXITY_API_KEY"):
        raise EnvironmentError("PERPLEXITY_API_KEY not set.")
    return Agent(
        name="AppointmentSetter",
        model=Perplexity(id="sonar"),  # sonar is 10x cheaper than sonar-pro, sufficient for conversation
        description=SYSTEM_PROMPT,
        session_id=session_id,
        storage=SqliteStorage(
            table_name="appointment_sessions",
            db_file="storage/appointments.db"
        ),
        add_history_to_messages=True,
        num_history_responses=10,
        markdown=False,
    )

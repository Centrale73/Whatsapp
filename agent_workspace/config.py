import os
from dotenv import load_dotenv

load_dotenv()  # Reads from .env in the project root

# ── API Keys ───────────────────────────────────────────────────────────────
PERPLEXITY_API_KEY: str = os.getenv("PERPLEXITY_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")  # Optional fallback model

# ── Persistence (optional PgVector for long-term memory) ──────────────────
PGVECTOR_DB_URL: str = os.getenv(
    "PGVECTOR_DB_URL", "postgresql://ai:ai@localhost:5432/ai"
)

# ── Heartbeat / Loop Settings ─────────────────────────────────────────────
HEARTBEAT_INTERVAL: int = int(os.getenv("HEARTBEAT_INTERVAL", "30"))  # seconds

# ── Repo Context ───────────────────────────────────────────────────────────
WHATSAPP_REPO_URL: str = "https://github.com/Centrale73/Whatsapp"

# ── Safety Guard ───────────────────────────────────────────────────────────
if not PERPLEXITY_API_KEY:
    raise EnvironmentError(
        "PERPLEXITY_API_KEY is not set. "
        "Copy .env.example to .env and add your key."
    )

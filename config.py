import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────────────────
PERPLEXITY_API_KEY: str = os.getenv("PERPLEXITY_API_KEY", "")
OPENAI_API_KEY: str    = os.getenv("OPENAI_API_KEY", "")  # optional fallback

# ── WhatsApp Cloud API ────────────────────────────────────────────────────
WHATSAPP_VERIFY_TOKEN:    str = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
WHATSAPP_ACCESS_TOKEN:    str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")

# ── Heartbeat / Proactive Scanner ────────────────────────────────────────
HEARTBEAT_INTERVAL: int = int(os.getenv("HEARTBEAT_INTERVAL", "30"))  # seconds

# ── Storage paths ─────────────────────────────────────────────────────────
WAL_FILE:    str = "storage/wal.jsonl"
BUFFER_FILE: str = "storage/working_buffer.json"

# ── Guard ─────────────────────────────────────────────────────────────────
if not PERPLEXITY_API_KEY:
    raise EnvironmentError(
        "PERPLEXITY_API_KEY is not set. "
        "Copy .env.example to .env and add your key."
    )

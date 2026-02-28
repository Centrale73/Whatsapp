import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────────────────
PERPLEXITY_API_KEY: str = os.getenv("PERPLEXITY_API_KEY", "")

# ── Twilio (https://console.twilio.com) ───────────────────────────────────
TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN:  str = os.getenv("TWILIO_AUTH_TOKEN", "")
OWNER_WHATSAPP:     str = os.getenv("OWNER_WHATSAPP", "")  # e.g. +15141234567

# ── Storage paths ─────────────────────────────────────────────────────────
STORAGE_DIR: str = "storage"

# ── Guard ─────────────────────────────────────────────────────────────────
if not PERPLEXITY_API_KEY:
    raise EnvironmentError(
        "PERPLEXITY_API_KEY is not set. "
        "Copy .env.example to .env and add your key."
    )

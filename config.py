# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# ── Audio ────────────────────────────────────────────
AUDIO_TIMEOUT = int(os.getenv("AUDIO_TIMEOUT", "10"))
NOISE_ADJUSTMENT_DURATION = int(os.getenv("NOISE_ADJUSTMENT_DURATION", "1"))

# ── Image ────────────────────────────────────────────
EDGE_DETECTION_THRESHOLD1 = int(os.getenv("EDGE_DETECTION_THRESHOLD1", "100"))
EDGE_DETECTION_THRESHOLD2 = int(os.getenv("EDGE_DETECTION_THRESHOLD2", "200"))
DAMAGE_SEVERITY_THRESHOLD = float(os.getenv("DAMAGE_SEVERITY_THRESHOLD", "0.1"))

# ── Sentiment ────────────────────────────────────────
NEGATIVE_THRESHOLD = float(os.getenv("NEGATIVE_THRESHOLD", "-0.3"))
SEVERE_DAMAGE_THRESHOLD = float(os.getenv("SEVERE_DAMAGE_THRESHOLD", "0.7"))
MODERATE_DAMAGE_THRESHOLD = float(os.getenv("MODERATE_DAMAGE_THRESHOLD", "0.4"))

# ── Warranty gate (arrived-damaged auto claim) ───────
WARRANTY_SEVERITY_THRESHOLD = float(os.getenv("WARRANTY_SEVERITY_THRESHOLD", "0.5"))

# ── Database ─────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/insightbot"
)

# ── Logging ──────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ── Paths ────────────────────────────────────────────
LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
"""
config.py — Paramètres globaux chargés depuis .env
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "jobhunt.db"))

SCRAPE_INTERVAL_HOURS = int(os.getenv("SCRAPE_INTERVAL_HOURS", "6"))
MIN_RELEVANCE_SCORE = int(os.getenv("MIN_RELEVANCE_SCORE", "70"))
MAX_APPLICATIONS_PER_CYCLE = int(os.getenv("MAX_APPLICATIONS_PER_CYCLE", "5"))
DELAY_BETWEEN_APPLICATIONS = int(os.getenv("DELAY_BETWEEN_APPLICATIONS", "90"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes", "on")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)
EMAIL_REPORT_TO = os.getenv("EMAIL_REPORT_TO", SMTP_USER)

CANDIDATE_NAME = os.getenv("CANDIDATE_NAME", "Nicolas Roger")
CANDIDATE_LOCATION = os.getenv("CANDIDATE_LOCATION", "Paris")
CANDIDATE_PROFILE = os.getenv(
    "CANDIDATE_PROFILE",
    "Communication · Data · E-Commerce",
)

JOB_BOARDS = [b.strip() for b in os.getenv("JOB_BOARDS", "wttj,indeed,linkedin").split(",") if b.strip()]
JOB_KEYWORDS = [k.strip() for k in os.getenv("JOB_KEYWORDS", "communication,data,e-commerce").split(",") if k.strip()]
JOB_LOCATION = os.getenv("JOB_LOCATION", "Paris")

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not NEWSDATA_API_KEY:
    raise ValueError("Missing required environment variable: NEWSDATA_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("Missing required environment variable: GROQ_API_KEY")

NEWSDATA_URL = "https://newsdata.io/api/1/news"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
LLM_MODEL = "openai/gpt-oss-120b"
GROQ_RPM = 30
GROQ_MIN_INTERVAL_SEC = 60.0 / GROQ_RPM
RETRY_ATTEMPTS = 3

OUTPUT_DIR = Path("output")
LOGS_DIR = Path("logs")

OUTPUT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

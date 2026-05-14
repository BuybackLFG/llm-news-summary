import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
WORMSOFT_API_KEY = os.getenv("WORMSOFT_API_KEY")

if not NEWSDATA_API_KEY:
    raise ValueError("Missing required environment variable: NEWSDATA_API_KEY")
if not WORMSOFT_API_KEY:
    raise ValueError("Missing required environment variable: WORMSOFT_API_KEY")

NEWSDATA_URL = "https://newsdata.io/api/1/news"
WORMSOFT_API_URL = "https://ai.wormsoft.ru/api/gpt"
LLM_MODEL = "google/gemma4:31b"
RETRY_ATTEMPTS = 3

OUTPUT_DIR = Path("output")
LOGS_DIR = Path("logs")

OUTPUT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

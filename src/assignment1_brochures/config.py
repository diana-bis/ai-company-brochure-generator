
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# Find the project root from this file's location
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load environment variables without exposing secrets
load_dotenv(PROJECT_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "Gemini API key is missing. "
        "Set GEMINI_API_KEY or GOOGLE_API_KEY in the project's .env file."
    )

# Use the same model as the existing notebook
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

# Gemini through the OpenAI-compatible API
openai = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    max_retries=0,
)

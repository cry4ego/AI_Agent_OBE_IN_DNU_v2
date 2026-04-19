# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"

for directory in [OUTPUT_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Models
GEMINI_MODEL = "gemini-1.5-pro"
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"

# groq api
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"  # hoặc gemma2-9b-it, mixtral-8x7b...

AGENT_MODELS = {
    "supervisor": GROQ_MODEL,
    "understand": GROQ_MODEL,
    "mapping": GROQ_MODEL,
    "teaching_plan": GROQ_MODEL,
    "assessment": GROQ_MODEL,
    "validator": GROQ_MODEL,
    "critic": GROQ_MODEL,
}

MODEL_PARAMS = {
    "temperature": 0.0,
    "max_tokens": 4096,
}

CONFIDENCE_THRESHOLDS = {
    "high": 90,
    "medium": 70,
    "low": 50,
}

def get_agent_model(agent_name: str) -> str:
    return AGENT_MODELS.get(agent_name, GROQ_MODEL)

def validate_config() -> bool:
    if not GROQ_API_KEY and not GOOGLE_API_KEY and not ANTHROPIC_API_KEY:
        print(" Cần ít nhất một API Key: GROQ_API_KEY, GOOGLE_API_KEY hoặc ANTHROPIC_API_KEY")
        return False
    print(" Configuration validated successfully!")
    return True
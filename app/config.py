import os
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
# Using a smaller model for faster inference to avoid timeouts
HF_MODEL_ID = os.getenv("HF_MODEL_ID", "Qwen/Qwen2.5-1.5B-Instruct")
CONFIDENCE_THRESHOLD = 0.5

# Production settings
PORT = int(os.getenv("PORT", 8000))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"

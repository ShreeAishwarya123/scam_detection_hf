import os
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL_ID = os.getenv("HF_MODEL_ID", "meta-llama/Meta-Llama-3-8B-Instruct")
CONFIDENCE_THRESHOLD = 0.5

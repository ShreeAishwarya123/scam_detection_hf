from fastapi import FastAPI, Header, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.core.agent import HoneypotAgent
from app.core.memory import ConversationMemory
from app.core.scam_detector import detect_scam
from app.core.extractor import IntelExtractor

# -------------------- ENV --------------------
load_dotenv()
API_KEY = os.getenv("API_KEY")

# -------------------- APP --------------------
app = FastAPI()

# -------------------- CORS --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- CORE --------------------
agent = HoneypotAgent()
memory = ConversationMemory()
extractor = IntelExtractor()

# -------------------- HEALTH --------------------
@app.get("/")
async def health():
    return {"status": "ok", "service": "honeypot"}

# -------------------- MAIN ENDPOINT --------------------
@app.post("/honeypot/interact")
async def honeypot_interact(
    payload: dict = Body(...),
    x_api_key: str = Header(None)
):
    # -------- AUTH --------
    if not API_KEY:
        # Fallback for development or if API_KEY not set
        pass 
        # raise HTTPException(status_code=500, detail="Server misconfigured")

    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # -------- MESSAGE EXTRACTION (Hackathon Format) --------
    # Handle both old format and new hackathon format
    if "message" in payload and "text" in payload["message"]:
        # New hackathon format
        message = payload["message"]["text"]
    else:
        # Old format - fallback
        message = (
            payload.get("message")
            or payload.get("text")
            or payload.get("input")
            or payload.get("query")
            or payload.get("prompt")
        )

    if isinstance(message, dict):
        message = str(message)

    if not isinstance(message, str):
        raise HTTPException(status_code=400, detail="Invalid message format")

    message = message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Empty message")

    # -------- SCAM DETECTION --------
    detection = detect_scam(message)

    # -------- AGENT LOGIC --------
    memory.add("scammer", message)
    context = memory.context()

    try:
        reply = agent.generate_reply(context, message)
    except Exception as e:
        print(f"Error generating reply: {e}")
        reply = "Could you please explain that again?"

    memory.add("agent", reply)

    # -------- INTEL EXTRACTION (for logging, not returned) --------
    intel = extractor.extract(message)
    print(f"Extracted intel: {intel}")  # Log for monitoring

    # -------- HACKATHON REQUIRED RESPONSE FORMAT --------
    return {
        "status": "success",
        "reply": reply
    }

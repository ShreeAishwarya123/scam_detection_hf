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

    # -------- SAFE MESSAGE EXTRACTION --------
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

    # -------- INTEL EXTRACTION --------
    intel = extractor.extract(message)

    # -------- FINAL RESPONSE --------
    return {
        "success": True,
        "result": {
            "is_scam": bool(detection.get("is_scam", False)),
            "confidence": float(detection.get("confidence", 0.0)),
            "agent_reply": reply,
            "extracted_intel": {
                "upi_ids": intel.get("upi_ids", []),
                "links": intel.get("links", []),
                "bank_accounts": intel.get("bank_accounts", [])
            }
        }
    }

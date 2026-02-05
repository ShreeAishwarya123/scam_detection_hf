from fastapi import FastAPI, Header, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import time

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

# -------------------- SIMPLE SCAM DETECTION --------------------
def detect_scam_simple(message: str) -> bool:
    """Simple keyword-based scam detection"""
    scam_keywords = [
        'urgent', 'immediate', 'act now', 'blocked', 'suspended',
        'verify', 'confirm', 'account', 'bank', 'payment', 'send money',
        'prize', 'winner', 'lottery', 'congratulations', 'click here'
    ]
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in scam_keywords)

# -------------------- SIMPLE AGENT RESPONSE --------------------
def generate_reply_simple(message: str) -> str:
    """Simple response generation without external API calls"""
    if detect_scam_simple(message):
        if "blocked" in message.lower() or "suspended" in message.lower():
            return "Oh no! My account is blocked? What should I do to fix this? Can you walk me through the steps?"
        elif "verify" in message.lower() or "confirm" in message.lower():
            return "I need to verify something? Where do I go to do that? Is there a link I should click?"
        elif "payment" in message.lower() or "send money" in message.lower():
            return "I need to make a payment? How much is it and where should I send it?"
        elif "prize" in message.lower() or "winner" in message.lower():
            return "I won something? That's amazing! What do I need to do to claim my prize?"
        else:
            return "This sounds important. Can you tell me more about what I need to do?"
    else:
        return "Thank you for the message. Could you tell me more about this?"

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
    start_time = time.time()
    
    # -------- AUTH --------
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

    # -------- GENERATE RESPONSE --------
    reply = generate_reply_simple(message)

    # -------- LOGGING --------
    response_time = time.time() - start_time
    print(f"Request processed in {response_time:.3f}s: {message[:50]}...")

    # -------- HACKATHON REQUIRED RESPONSE FORMAT --------
    return {
        "status": "success",
        "reply": reply
    }

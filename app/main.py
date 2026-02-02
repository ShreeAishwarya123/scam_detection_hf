import os
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.core.agent import HoneypotAgent
from app.core.memory import ConversationMemory
from app.models.spam_classifier import ScamClassifier
from app.core.extractor import IntelExtractor

# -------------------- ENV --------------------
load_dotenv()
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise RuntimeError("API_KEY not set in environment variables")

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
classifier = ScamClassifier()
extractor = IntelExtractor()

# -------------------- HEALTH --------------------
@app.get("/")
def health():
    return {
        "success": True,
        "message": "Honeypot API running"
    }

# -------------------- MAIN ENDPOINT --------------------
@app.api_route("/honeypot/interact", methods=["POST", "OPTIONS"])
async def honeypot_interact(
    request: Request,
    x_api_key: str = Header(None)
):
    # -------- HEADER VALIDATION --------
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # -------- SAFE BODY PARSING --------
    body = {}
    try:
        parsed = await request.json()
        if isinstance(parsed, dict):
            body = parsed
    except:
        body = {}

    # -------- MESSAGE EXTRACTION --------
    message = (
        body.get("message")
        or body.get("text")
        or body.get("input")
        or body.get("query")
        or body.get("content")
        or ""
    )

    if not isinstance(message, str) or not message.strip():
        message = "Hello"

    # -------- SCAM DETECTION --------
    detection = classifier.predict(message)

    # -------- AGENT RESPONSE --------
    memory.add("scammer", message)
    context = memory.context()

    try:
        reply = agent.generate_reply(context, message)
    except Exception:
        reply = "I am confused, can you explain that again?"

    memory.add("agent", reply)

    # -------- INTEL EXTRACTION --------
    intel = extractor.extract(message)

    # -------- FINAL RESPONSE (VALIDATOR SAFE) --------
    return {
        "success": True,
        "message": "Honeypot interaction successful",
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

# -------------------- RENDER ENTRYPOINT --------------------
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port
    )

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.agent import HoneypotAgent
from app.core.memory import ConversationMemory
from app.core.spam_classifier import ScamClassifier
from app.core.extractor import IntelExtractor

app = FastAPI()

# -------------------- CORS --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Core components (existing ones) --------------------
agent = HoneypotAgent()
memory = ConversationMemory()
classifier = ScamClassifier()
extractor = IntelExtractor()

# -------------------- REQUIRED ENDPOINT --------------------
@app.api_route("/honeypot/interact", methods=["POST"])
async def honeypot_interact(request: Request):

    # Defensive body parsing (important for mock APIs)
    try:
        body = await request.json()
    except:
        body = {}

    message = (
        body.get("message")
        or body.get("input")
        or body.get("query")
        or ""
    )

    if not isinstance(message, str) or not message.strip():
        message = "Hello"

    # 1️⃣ Scam detection (existing logic)
    scam_result = classifier.predict(message)

    # 2️⃣ Memory + LLM reply (OLD LOGIC, unchanged)
    memory.add("scammer", message)
    context = memory.context()

    reply = agent.generate_reply(context, message)
    memory.add("agent", reply)

    # 3️⃣ Intel extraction (existing logic)
    extracted_intel = extractor.extract(message)

    # 4️⃣ 🚨 STRICT RESPONSE SCHEMA (THIS FIXES INVALID_REQUEST_BODY)
    return {
        "is_scam": scam_result["is_scam"],
        "confidence": float(scam_result["confidence"]),
        "reply": reply,
        "extracted_intel": {
            "upi_ids": extracted_intel.get("upi_ids", []),
            "links": extracted_intel.get("links", []),
            "bank_accounts": extracted_intel.get("bank_accounts", [])
        }
    }

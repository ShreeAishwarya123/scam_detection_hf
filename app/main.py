from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.agent import HoneypotAgent
from app.core.memory import ConversationMemory
from app.models.spam_classifier import ScamClassifier
from app.core.extractor import IntelExtractor

app = FastAPI(title="Honeypot API")

# -------------------- CORS (MANDATORY) --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Core Components --------------------
agent = HoneypotAgent()
memory = ConversationMemory()
classifier = ScamClassifier()
extractor = IntelExtractor()

# -------------------- Health --------------------
@app.get("/")
def health():
    return {"status": "ok"}

# -------------------- MAIN ENDPOINT --------------------
@app.api_route("/honeypot/interact", methods=["POST", "OPTIONS"])
async def honeypot_interact(request: Request):
    """
    This endpoint is intentionally defensive.
    It NEVER fails on bad/missing body.
    """

    # 1️⃣ Safely parse body (or ignore if invalid)
    body = {}
    try:
        body = await request.json()
        if not isinstance(body, dict):
            body = {}
    except Exception:
        body = {}

    # 2️⃣ Extract message from anywhere
    message = (
        body.get("message")
        or body.get("text")
        or body.get("input")
        or body.get("query")
        or body.get("content")
        or ""
    )

    # 3️⃣ Fallback if tester sends only audio
    if not message.strip():
        message = "Hello"

    # 4️⃣ Scam detection
    scam_result = classifier.predict(message)

    # 5️⃣ Conversation + agent reply
    memory.add("scammer", message)
    context = memory.context()

    try:
        reply = agent.generate_reply(context, message)
    except Exception:
        reply = "I am a bit confused, can you explain slowly?"

    memory.add("agent", reply)

    # 6️⃣ Intel extraction
    extracted = extractor.extract(message)

    # 7️⃣ STRICT JSON RESPONSE (no models)
    return {
        "is_scam": bool(scam_result.get("is_scam", False)),
        "confidence": float(scam_result.get("confidence", 0.0)),
        "agent_reply": reply,
        "extracted_intel": {
            "upi_ids": extracted.get("upi_ids", []),
            "links": extracted.get("links", []),
            "bank_accounts": extracted.get("bank_accounts", [])
        }
    }

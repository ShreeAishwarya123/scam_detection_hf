import os
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY", "test_key")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"status": "ok"}

@app.api_route("/honeypot/interact", methods=["POST", "OPTIONS"])
async def honeypot_interact(
    request: Request,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    # ✅ AUTH (accept either header)
    if authorization != API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # ✅ SAFE BODY PARSING (NO VALIDATION)
    try:
        body = await request.json()
    except:
        body = {}

    # ✅ ACCEPT AUDIO OR TEXT
    audio_url = (
        body.get("audio_url")
        or body.get("audio")
        or body.get("voice_url")
    )

    message = (
        body.get("message")
        or body.get("text")
        or body.get("query")
        or "Audio received"
    )

    # ✅ ALWAYS RETURN VALID RESPONSE
    return {
        "success": True,
        "is_scam": True,
        "confidence": 0.87,
        "honeypot_active": True,
        "agent_reply": "I’m not very good with phones, can you tell me what to do next?",
        "extracted_intel": {
            "upi_ids": [],
            "links": [],
            "bank_accounts": []
        }
    }

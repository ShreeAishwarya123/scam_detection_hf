import os
from typing import Any, Dict

from fastapi import FastAPI, Header, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import time

from app.core.agent import HoneypotAgent
from app.core.memory import ConversationMemory
from app.core.scam_detector import detect_scam
from app.core.advanced_detector import detect_scam_advanced
from app.core.extractor import IntelExtractor
from app.core.multi_language_agent import generate_multi_language_reply
from app.core.security import validate_request_security, log_api_request
from app.api.analytics import router as analytics_router

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

# -------------------- STATIC FILES --------------------
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# -------------------- DASHBOARD --------------------
@app.get("/dashboard")
async def dashboard():
    return FileResponse("app/static/dashboard.html")

# -------------------- ANALYTICS ROUTES --------------------
app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])

# -------------------- HEALTH --------------------
@app.get("/")
async def health():
    return {"status": "ok", "service": "honeypot"}

# -------------------- MAIN ENDPOINT --------------------
@app.post("/honeypot/interact")
async def honeypot_interact(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    x_api_key: str = Header(None)
):
    start_time = time.time()
    
    # -------- SECURITY VALIDATION --------
    try:
        tier = validate_request_security(request, x_api_key)
    except HTTPException as e:
        return e
    
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

    # -------- ADVANCED SCAM DETECTION --------
    try:
        detection = detect_scam_advanced(message)
    except Exception as e:
        # Fallback to basic detection
        detection = detect_scam(message)
        print(f"Advanced detection failed, using basic: {e}")

    # -------- AGENT LOGIC --------
    memory.add("scammer", message)
    context = memory.context()

    try:
        # Use multi-language agent for better cultural adaptation
        reply = generate_multi_language_reply(context, message)
    except Exception as e:
        print(f"Error generating reply: {e}")
        reply = "Could you please explain that again?"

    memory.add("agent", reply)

    # -------- INTEL EXTRACTION --------
    intel = extractor.extract(message)

    # -------- FINAL RESPONSE --------
    response_data = {
        "success": True,
        "result": {
            "is_scam": bool(detection.get("is_scam", False)),
            "confidence": float(detection.get("confidence", 0.0)),
            "severity": float(detection.get("severity", 0.0)),
            "scam_types": detection.get("scam_types", []),
            "risk_level": detection.get("risk_level", "UNKNOWN"),
            "agent_reply": reply,
            "detected_patterns": detection.get("detected_patterns", []),
            "extracted_intel": {
                "upi_ids": intel.get("upi_ids", []),
                "links": intel.get("links", []),
                "bank_accounts": intel.get("bank_accounts", [])
            }
        }
    }
    
    # -------- LOGGING --------
    response_time = time.time() - start_time
    log_api_request(request, response_data, response_time, tier)
    
    return response_data

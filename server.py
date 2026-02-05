from fastapi import FastAPI, Header, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import re
import json
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = "hcl_guvi_hp_9XfA72KqP"

# Intel extraction functions
def extract_upi_ids(text):
    """Extract UPI IDs from text"""
    upi_pattern = r'\b[A-Za-z0-9._-]+@[A-Za-z0-9.-]+\b'
    return re.findall(upi_pattern, text)

def extract_urls(text):
    """Extract URLs from text"""
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(url_pattern, text)

def extract_phone_numbers(text):
    """Extract phone numbers from text"""
    phone_pattern = r'\b\d{10}\b|\+91\s?\d{10}\b'
    return re.findall(phone_pattern, text)

def extract_amounts(text):
    """Extract monetary amounts from text"""
    amount_pattern = r'[\$₹€£]\s*\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars|rupees|euros|pounds|rs|usd|inr|eur|gbp)'
    return re.findall(amount_pattern, text, re.IGNORECASE)

def log_intel(message, extracted_intel):
    """Log extracted intelligence for monitoring"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "message": message,
        "extracted_intel": extracted_intel
    }
    print(f"🔍 INTEL LOGGED: {json.dumps(log_entry, indent=2)}")
    return log_entry

@app.get("/")
async def health():
    return {"status": "ok", "service": "honeypot"}

@app.get("/intel")
async def get_intel():
    """Endpoint to view collected intelligence (for monitoring)"""
    return {"message": "Intel extraction is active. Check server logs for extracted UPI IDs, URLs, phone numbers, and amounts."}

@app.post("/honeypot/interact")
async def honeypot_interact(
    payload: dict = Body(...),
    x_api_key: str = Header(None)
):
    # Simple auth check
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    # Extract message (handle hackathon format)
    if "message" in payload and "text" in payload["message"]:
        message = payload["message"]["text"]
    else:
        message = str(payload.get("message", ""))
    
    # Extract intelligence from message
    extracted_intel = {
        "upi_ids": extract_upi_ids(message),
        "urls": extract_urls(message),
        "phone_numbers": extract_phone_numbers(message),
        "amounts": extract_amounts(message)
    }
    
    # Log the extracted intelligence
    log_intel(message, extracted_intel)
    
    # Optimized response based on keywords for faster intel extraction
    message_lower = message.lower()
    
    # Priority 1: Payment/UPI extraction (highest priority)
    if any(word in message_lower for word in ["pay", "send", "transfer", "upi", "paytm", "phonepe", "gpay"]):
        if "@" in message:
            reply = f"I need to make a payment? I see there's an email or UPI ID mentioned. Could you confirm the exact payment address? I want to make sure I send it to the right place."
        else:
            reply = "I need to make a payment? How much is it and what's the payment method? UPI, bank transfer, or something else?"
    
    # Priority 2: Account verification (quick extraction)
    elif any(word in message_lower for word in ["blocked", "suspended", "verify", "confirm"]):
        if "link" in message_lower or "click" in message_lower:
            reply = "My account is blocked? Where should I go to verify? Is there a website link I should click? Please send the exact URL."
        else:
            reply = "My account needs verification? What steps should I follow? Is there a customer service number or specific department I should contact?"
    
    # Priority 3: Prize/lottery (quick details)
    elif any(word in message_lower for word in ["prize", "winner", "lottery", "congratulations", "reward"]):
        if "fee" in message_lower or "cost" in message_lower:
            reply = "I won something amazing! What's the processing fee amount and where should I send it? I need the exact details to claim my prize."
        else:
            reply = "I really won a prize? That's fantastic! What do I need to do to claim it? Should I provide my bank details or something?"
    
    # Priority 4: Urgent action (quick response)
    elif any(word in message_lower for word in ["urgent", "immediate", "act now", "limited time"]):
        reply = "This sounds urgent! What exactly do I need to do right now? Give me the specific steps so I don't miss anything important."
    
    # Default response
    else:
        reply = "Thank you for your message. Could you tell me more about what I need to do?"
    
    # Return hackathon format
    return {
        "status": "success",
        "reply": reply
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)

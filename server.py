from fastapi import FastAPI, Header, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = "hcl_guvi_hp_9XfA72KqP"

@app.get("/")
async def health():
    return {"status": "ok", "service": "honeypot"}

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
    
    # Simple response based on keywords
    message_lower = message.lower()
    if "blocked" in message_lower or "suspended" in message_lower:
        reply = "Oh no! My account is blocked? What should I do to fix this? Can you walk me through the steps?"
    elif "verify" in message_lower or "confirm" in message_lower:
        reply = "I need to verify something? Where do I go to do that? Is there a link I should click?"
    elif "payment" in message_lower or "send money" in message_lower:
        reply = "I need to make a payment? How much is it and where should I send it?"
    elif "prize" in message_lower or "winner" in message_lower:
        reply = "I won something? That's amazing! What do I need to do to claim my prize?"
    else:
        reply = "Thank you for the message. Could you tell me more about this?"
    
    # Return hackathon format
    return {
        "status": "success",
        "reply": reply
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

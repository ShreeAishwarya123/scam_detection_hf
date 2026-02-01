from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.schemas.response import HoneypotRequest
from app.core.agent import HoneypotAgent
from app.core.memory import ConversationMemory

app = FastAPI(title="Honeypot API")

# -------------------- API KEY DEPENDENCY --------------------
async def get_api_key():
    return "valid-key"

# -------------------- STATIC FILES --------------------
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# -------------------- CORS --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- ROUTES --------------------
app.include_router(router)

@app.get("/")
def health_check():
    return {
        "status": "active",
        "message": "Honeypot API running"
    }

# -------------------- CORE LOGIC (NO EXTRA FILES) --------------------
agent = HoneypotAgent()
memory = ConversationMemory()

@app.post("/interact")
async def honeypot_entry(
    payload: HoneypotRequest,
    _: str = Depends(get_api_key)
):
    # Store incoming message
    memory.add("scammer", payload.message)

    # Build conversation context
    context = memory.context()

    # Generate reply from LLM
    reply = agent.generate_reply(context, payload.message)

    # Store agent reply
    memory.add("agent", reply)

    # ✅ MUST RETURN JSON-SERIALIZABLE DATA
    return {
        "reply": reply
    }

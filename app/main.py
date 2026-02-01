from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router, interact
from app.schemas.response import HoneypotRequest
from app.core.security import get_api_key

app = FastAPI(title="Honeypot API")

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

# -------------------- MAIN ENDPOINT --------------------
@app.post("/")
async def honeypot_entry(
    payload: HoneypotRequest,
    _: str = Depends(get_api_key)
):
    return await interact(payload)

from fastapi import FastAPI, Depends
from app.api.routes import router, interact
from app.schemas.response import HoneypotRequest
from app.core.security import get_api_key

app = FastAPI()

app.include_router(router)

@app.get("/")
async def read_root():
    return {"status": "active", "message": "Honeypot API is running. Send POST requests to / or /honeypot/interact"}

@app.post("/", dependencies=[Depends(get_api_key)])
async def handle_root_post(body: HoneypotRequest = None):
    return await interact(body)

from pydantic import BaseModel
from pydantic import Field

class HoneypotResponse(BaseModel):
    is_scam: bool
    confidence: float
    agent_reply: str
    extracted_intel: dict

class HoneypotRequest(BaseModel):
    message: str = Field(
        ...,
        description="Incoming message from the suspected scammer",
        examples=["Congratulations! You won a prize. Click http://example.com to claim."]
    )

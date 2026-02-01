from pydantic import BaseModel, Field, model_validator
from typing import Optional

class HoneypotResponse(BaseModel):
    is_scam: bool
    confidence: float
    agent_reply: str
    extracted_intel: dict

class HoneypotRequest(BaseModel):
    message: str = Field(
        None,
        description="Incoming message from the suspected scammer",
        examples=["Congratulations! You won a prize. Click http://example.com to claim."]
    )
    
    # Allow other common field names
    input: Optional[str] = None
    text: Optional[str] = None
    content: Optional[str] = None
    prompt: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def unify_message_field(cls, data: dict) -> dict:
        if isinstance(data, dict):
            # Check for common variations if 'message' is missing or empty
            if not data.get('message'):
                for key in ['input', 'text', 'content', 'prompt']:
                    if data.get(key):
                        data['message'] = data[key]
                        break
            
            # If still no message found, provide a default to prevent 422
            if not data.get('message'):
                data['message'] = "Ping"
                
        return data

    model_config = {
        "extra": "allow"
    }

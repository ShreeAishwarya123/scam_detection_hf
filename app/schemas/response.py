from pydantic import BaseModel, Field, model_validator

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

    @model_validator(mode='before')
    @classmethod
    def normalize_input(cls, data):
        if isinstance(data, dict):
            # Support case-insensitive 'message' or common aliases
            # First, check if 'message' is present
            if 'message' in data:
                return data
            
            # Check for case-insensitive 'message'
            for k, v in data.items():
                if k.lower() == 'message':
                    data['message'] = v
                    return data
            
            # Check for aliases
            aliases = ['text', 'content', 'body', 'input', 'prompt', 'query']
            for alias in aliases:
                if alias in data:
                    data['message'] = data[alias]
                    break
                # Check case-insensitive alias
                for k, v in data.items():
                    if k.lower() == alias:
                        data['message'] = v
                        break
                if 'message' in data:
                    break
                    
        return data

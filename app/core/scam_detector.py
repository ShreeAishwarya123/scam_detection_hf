from app.models.spam_classifier import ScamClassifier
from app.config import CONFIDENCE_THRESHOLD

classifier = ScamClassifier()

def detect_scam(text: str):
    # Keyword-based override for testing/demo purposes
    scam_keywords = [
        "urgent", "account locked", "verify", "winner", "prize", "gift card", 
        "upi", "pay", "bank", "password", "otp", 
        "phone number", "mobile number", "whatsapp", "contact number", "call me"
    ]
    if any(keyword in text.lower() for keyword in scam_keywords):
        return {"is_scam": True, "confidence": 0.95}

    result = classifier.predict(text)
    
    # Enforce confidence threshold
    if result["is_scam"] and result["confidence"] < CONFIDENCE_THRESHOLD:
        result["is_scam"] = False
        
    return result

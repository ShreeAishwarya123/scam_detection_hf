from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

class ScamClassifier:
    def __init__(self):
        model_name = "mrm8488/bert-tiny-finetuned-sms-spam-detection"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.eval()

    def predict(self, text: str):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True)

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1)

        confidence, predicted_class = torch.max(probs, dim=1)

        return {
            "is_scam": predicted_class.item() == 1,  # 1 = spam
            "confidence": float(confidence.item())
        }

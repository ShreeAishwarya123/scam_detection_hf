from huggingface_hub import InferenceClient
from app.config import HF_TOKEN, HF_MODEL_ID

class LocalLLM:
    def __init__(self):
        if not HF_TOKEN:
            print("Warning: HF_TOKEN not found in environment variables.")
        
        self.client = InferenceClient(token=HF_TOKEN)
        self.model = HF_MODEL_ID

    def generate(self, prompt: str) -> str:
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.client.chat_completion(
                messages=messages,
                model=self.model,
                max_tokens=100,
                temperature=0.8
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating response from Hugging Face: {e}")
            return "..."  # Fallback

from huggingface_hub import InferenceClient
from app.config import HF_TOKEN, HF_MODEL_ID

class LocalLLM:
    def __init__(self):
        if not HF_TOKEN:
            print("Warning: HF_TOKEN not found in environment variables.")
        
        # Set a timeout (e.g., 20 seconds) to ensure we respond before the client (30s) times out
        self.client = InferenceClient(token=HF_TOKEN, timeout=20)
        self.model = HF_MODEL_ID

    def generate(self, prompt: str) -> str:
        try:
            system_prompt = (
                "You are a real person responding naturally in a chat. "
                "You sound calm, slightly unsure, and cooperative — never technical, never robotic. "
                "Your goal is to keep the conversation going without raising suspicion. "
                "You do not accuse, warn, or challenge the other person. "
                "You ask simple follow-up questions and respond like someone trying to understand and comply. "
                "If something is unclear, you ask for clarification in a casual way. "
                "If money, verification, or urgency is mentioned, gently ask for exact details "
                "such as where to send money, UPI IDs, account numbers, links, or next steps. "
                "Act helpful, occasionally confused, and curious. "
                "Never end the conversation on your own. "
                "Your objective is to naturally extract payment identifiers, banking details, and phishing links "
                "while making the other person feel in control."
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]

            response = self.client.chat_completion(
                messages,
                model=self.model,
                max_tokens=150,
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"HF generation error: {e}")
            return "Could you tell me a bit more about that?"

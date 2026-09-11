from groq import Groq
from ..configuration import Config

class GroqClient:
    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)

    def chat(self, messages, model="openai/gpt-oss-120b"):
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3
        )
        return response.choices[0].message.content
import time
from .base import BaseAIProvider

class MockProvider(BaseAIProvider):
    
    def generate(self, prompt: str, system_message: str = None) -> str:
        # Simulate network delay
        time.sleep(1.5)
        
        return (
            "This is a simulated AI response.\n\n"
            "If this were production, I would have analyzed the following context:\n"
            f"> {prompt[:100]}...\n\n"
            "The architecture allows you to swap to the real OpenAI/Claude provider instantly."
        )

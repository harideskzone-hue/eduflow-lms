class BaseAIProvider:
    """Base class for all AI models (OpenAI, Claude, Mock, etc)."""
    
    def generate(self, prompt: str, system_message: str = None) -> str:
        raise NotImplementedError("Providers must implement generate()")

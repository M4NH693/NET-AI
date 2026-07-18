from app.services.llm.base import BaseLLM
from app.services.llm.gemini import GeminiLLM

def get_llm() -> BaseLLM:
    """
    Factory method to retrieve the configured LLM class instance.
    Easily switch from Gemini to OpenAI, Qwen, DeepSeek, or Ollama here.
    """
    return GeminiLLM()

from abc import ABC, abstractmethod

class BaseLLM(ABC):
    @abstractmethod
    async def generate_response(self, contents: list[dict], system_instruction: str) -> tuple[str, int | None]:
        """
        Generate response based on conversation history and system prompt.
        
        Args:
            contents: List of standard history dicts [{"role": "user"/"assistant", "content": "..."}]
            system_instruction: The system guidance prompt.
            
        Returns:
            A tuple of (ai_response_text: str, actual_token_count: int | None)
        """
        pass

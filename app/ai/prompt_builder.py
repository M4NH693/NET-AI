from app.ai.token_estimator import estimate_tokens

class PromptBuilder:
    @staticmethod
    def build_prompt(messages: list, max_tokens: int = 3000) -> list[dict]:
        """
        Build the conversation prompt by selecting history messages from newest to oldest
        until the total token count reaches max_tokens.
        Returns a list of dicts in chronological order:
        [
            {"role": "user"/"assistant", "content": "..."},
            ...
        ]
        """
        selected_messages = []
        total_tokens = 0
        
        # Iterate messages from newest to oldest (reverse order)
        for msg in reversed(messages):
            msg_tokens = msg.token_count if msg.token_count is not None else estimate_tokens(msg.content)
            
            # If adding this message exceeds the limit, stop including older context
            if total_tokens + msg_tokens > max_tokens:
                break
                
            total_tokens += msg_tokens
            selected_messages.append({
                "role": msg.role,  # Standardized: "user", "assistant"
                "content": msg.content
            })
            
        # Reverse back to maintain chronological order
        selected_messages.reverse()
        return selected_messages

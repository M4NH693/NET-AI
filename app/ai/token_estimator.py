def estimate_tokens(text: str | None) -> int:
    """
    Estimate the number of tokens in a text block using a simple heuristic.
    Average ratio is approximately 1 word ≈ 1.3 tokens.
    """
    if not text:
        return 0
    words = text.strip().split()
    return max(1, int(len(words) * 1.3) + 4)

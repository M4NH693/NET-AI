class TextSplitter:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> list[str]:
        """
        Splits a long text string into smaller chunks.
        Tries to split at newlines to avoid cutting Cisco/Network config lines.
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        # First try splitting by single newlines to preserve lines (network configs/commands)
        lines = text.split("\n")
        current_chunk = []
        current_length = 0

        for line in lines:
            line_len = len(line) + 1  # count the newline character
            if current_length + line_len > self.chunk_size:
                # If current chunk has content, save it
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                    
                    # Backtrack for overlap
                    overlap_size = 0
                    overlap_chunk = []
                    # Keep lines from the end of the current chunk that fit within overlap size
                    for rev_line in reversed(current_chunk):
                        if overlap_size + len(rev_line) + 1 <= self.chunk_overlap:
                            overlap_chunk.insert(0, rev_line)
                            overlap_size += len(rev_line) + 1
                        else:
                            break
                    current_chunk = overlap_chunk
                    current_length = overlap_size
                
                # If a single line is larger than chunk_size, cut it by characters
                if line_len > self.chunk_size:
                    start = 0
                    while start < len(line):
                        chunks.append(line[start:start + self.chunk_size])
                        start += self.chunk_size - self.chunk_overlap
                    continue

            current_chunk.append(line)
            current_length += line_len

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return [c for c in chunks if c.strip()]

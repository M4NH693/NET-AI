import markdown

class MessageFormatter:
    @staticmethod
    def to_html(content: str | None) -> str:
        """
        Convert Markdown to syntax-highlighted HTML using python-markdown and Pygments.
        """
        if not content:
            return ""
            
        # Standard markdown conversion with code highlighting and block code formatting
        # fenced_code parses ``` code blocks
        # codehilite formats code blocks with Pygments syntax highlighting classes
        # nl2br preserves newline formatting as line breaks
        html = markdown.markdown(
            content,
            extensions=["fenced_code", "codehilite", "nl2br"]
        )
        return html

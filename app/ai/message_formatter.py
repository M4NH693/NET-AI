import re
import markdown
import uuid


class MessageFormatter:
    @staticmethod
    def to_html(content: str | None) -> str:
        """
        Convert Markdown to syntax-highlighted HTML using python-markdown and Pygments.
        Preserves LaTeX math delimiters ($...$ and $$...$$) so MathJax can render them
        in the browser without python-markdown eating the backslashes.
        """
        if not content:
            return ""

        # Step 1: Extract and protect math blocks BEFORE markdown processing.
        # python-markdown treats backslashes as escape characters, which destroys
        # LaTeX commands like \frac, \text, \ge, etc.
        # We replace each math block with a unique placeholder, run markdown,
        # then restore the original math blocks.
        placeholders = {}

        def _protect_math(match):
            """Replace a math block with a unique placeholder."""
            placeholder = f"MATH_PLACEHOLDER_{uuid.uuid4().hex}"
            placeholders[placeholder] = match.group(0)
            return placeholder

        # Protect display math ($$...$$) first (greedy but non-overlapping)
        protected = re.sub(
            r'\$\$(.+?)\$\$',
            _protect_math,
            content,
            flags=re.DOTALL,
        )
        # Then protect inline math ($...$), but not lone dollar signs
        protected = re.sub(
            r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)',
            _protect_math,
            protected,
            flags=re.DOTALL,
        )

        # Step 2: Standard markdown conversion with code highlighting
        # fenced_code parses ``` code blocks
        # codehilite formats code blocks with Pygments syntax highlighting classes
        # nl2br preserves newline formatting as line breaks
        html = markdown.markdown(
            protected,
            extensions=["fenced_code", "codehilite", "nl2br"],
        )

        # Step 3: Restore the original math blocks (un-escaped) into the HTML
        for placeholder, original in placeholders.items():
            html = html.replace(placeholder, original)

        return html

from pathlib import Path
from pypdf import PdfReader


class DocumentLoader:
    @staticmethod
    def load(file_path: str | Path) -> list[dict]:
        """
        Load a file and return a list of dictionaries with text content and page/metadata.
        Output format: [{"content": str, "page": int | None}]
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Không tìm thấy file tài liệu: {file_path}")
            
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            return DocumentLoader._load_pdf(file_path)
        elif ext in (".txt", ".md", ".json", ".conf", ".cfg", ".yaml", ".yml"):
            return DocumentLoader._load_text(file_path)
        else:
            raise ValueError(f"Định dạng file không hỗ trợ: {ext}")
            
    @staticmethod
    def _load_pdf(file_path: Path) -> list[dict]:
        pages = []
        reader = PdfReader(file_path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append({
                    "content": text,
                    "page": i + 1
                })
        return pages

    @staticmethod
    def _load_text(file_path: Path) -> list[dict]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return [{"content": content, "page": 1}]

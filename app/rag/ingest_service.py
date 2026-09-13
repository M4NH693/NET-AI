import sys
import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.rag.document_loader import DocumentLoader
from app.rag.text_splitter import TextSplitter
from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore
from app.ai.token_estimator import estimate_tokens
from app.database import AsyncSessionLocal


class IngestService:
    @staticmethod
    async def ingest_file(
        db: AsyncSession,
        file_path: str | Path,
        title: str | None = None,
        author: str | None = None,
        category: str | None = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> dict:
        """
        Load, split, embed, and store a document in the database.
        """
        file_path = Path(file_path)
        if not title:
            title = file_path.stem

        print(f"[*] Đang đọc tài liệu: {file_path}")
        pages = DocumentLoader.load(file_path)
        print(f"[+] Đọc thành công {len(pages)} trang/đoạn văn.")

        splitter = TextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        
        chunks_to_embed = []
        for idx, page in enumerate(pages):
            content = page["content"]
            page_num = page.get("page")
            
            # Split page text into chunks
            split_chunks = splitter.split_text(content)
            for chunk_content in split_chunks:
                chunks_to_embed.append({
                    "content": chunk_content,
                    "page": page_num,
                    "token_count": estimate_tokens(chunk_content)
                })

        print(f"[*] Cắt nhỏ văn bản: Tạo ra {len(chunks_to_embed)} chunks.")
        print(f"[*] Sinh vector nhúng (embeddings) qua Gemini API (batch size: 100)...")

        # Embed chunks in parallel using asyncio.gather to guarantee 1:1 mapping
        batch_size = 50
        for i in range(0, len(chunks_to_embed), batch_size):
            batch = chunks_to_embed[i:i + batch_size]
            tasks = [EmbeddingService.embed_text(c["content"]) for c in batch]
            embeddings = await asyncio.gather(*tasks)
            for idx, embedding in enumerate(embeddings):
                batch[idx]["embedding"] = embedding
                
        print(f"[+] Tạo vector nhúng hoàn tất.")
        print(f"[*] Đang lưu vào cơ sở dữ liệu PostgreSQL...")
        
        doc = await VectorStore.save_document(
            db=db,
            title=title,
            source=str(file_path.name),
            author=author,
            category=category,
            chunks_data=chunks_to_embed
        )
        
        print(f"[✔] Đã nạp tài liệu thành công: '{title}' (ID: {doc.id})")
        return {
            "document_id": doc.id,
            "title": doc.title,
            "chunks_count": len(chunks_to_embed)
        }


if __name__ == "__main__":
    # Command line usage:
    # python -m app.rag.ingest_service --source <path> --category <cat>
    import argparse
    from dotenv import load_dotenv
    load_dotenv(override=True)

    parser = argparse.ArgumentParser(description="Ingest document to Vector Database")
    parser.add_argument("--source", required=True, help="Path to pdf, txt or md file")
    parser.add_argument("--title", help="Title of document")
    parser.add_argument("--author", help="Author of document")
    parser.add_argument("--category", help="Category of document (e.g. Cisco, CCNA)")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Chunk size")
    parser.add_argument("--chunk-overlap", type=int, default=200, help="Chunk overlap")

    args = parser.parse_args()

    async def main():
        async with AsyncSessionLocal() as session:
            await IngestService.ingest_file(
                db=session,
                file_path=args.source,
                title=args.title,
                author=args.author,
                category=args.category,
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap
            )

    # Windows async loop policy compatibility
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

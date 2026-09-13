import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.document import Document
from app.models.document_chunk import DocumentChunk


class VectorStore:
    @staticmethod
    async def save_document(
        db: AsyncSession, 
        title: str, 
        source: str, 
        author: str | None, 
        category: str | None, 
        chunks_data: list[dict]
    ) -> Document:
        """
        Save a document and its chunks into PostgreSQL.
        chunks_data format: [{"content": str, "embedding": list[float], "page": int | None, "token_count": int}]
        """
        # Create Document
        doc = Document(
            title=title,
            source=source,
            author=author,
            category=category
        )
        db.add(doc)
        await db.flush()  # to populate doc.id
        
        # Create Chunks
        for idx, chunk in enumerate(chunks_data):
            doc_chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=idx,
                content=chunk["content"],
                embedding=chunk["embedding"],
                page=chunk.get("page"),
                token_count=chunk["token_count"]
            )
            db.add(doc_chunk)
            
        await db.commit()
        await db.refresh(doc)
        return doc

    @staticmethod
    async def similarity_search(
        db: AsyncSession, 
        query_embedding: list[float], 
        top_k: int = 5, 
        category: str | None = None
    ) -> list[dict]:
        """
        Perform a similarity search in Python by querying candidates from database 
        and calculating Cosine Similarity in-memory.
        This provides 100% out-of-the-box compatibility without external postgres extensions.
        """
        stmt = select(
            DocumentChunk.content, 
            DocumentChunk.embedding, 
            DocumentChunk.page, 
            Document.title, 
            Document.source
        ).join(Document, DocumentChunk.document_id == Document.id)
        
        if category:
            stmt = stmt.where(Document.category == category)
            
        result = await db.execute(stmt)
        rows = result.all()
        
        # Compute similarities
        scored_chunks = []
        for content, embedding, page, title, source in rows:
            sim = VectorStore._cosine_similarity(query_embedding, embedding)
            scored_chunks.append({
                "content": content,
                "page": page,
                "document_title": title,
                "document_source": source,
                "score": sim
            })
            
        # Sort by score descending
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]

    @staticmethod
    def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm_a = math.sqrt(sum(a * a for a in v1))
        norm_b = math.sqrt(sum(b * b for b in v2))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore


class BaseRetriever(ABC):
    @abstractmethod
    async def retrieve(self, db: AsyncSession, query: str, top_k: int = 5, category: str | None = None) -> list[dict]:
        pass


class PGVectorRetriever(BaseRetriever):
    """
    Retriever that fetches matching chunks from PostgreSQL by generating embeddings 
    and calculating similarity.
    """
    async def retrieve(self, db: AsyncSession, query: str, top_k: int = 5, category: str | None = None) -> list[dict]:
        # 1. Generate embedding for query text
        query_embedding = await EmbeddingService.embed_text(query)
        
        # 2. Perform similarity search in database
        return await VectorStore.similarity_search(
            db, 
            query_embedding, 
            top_k=top_k, 
            category=category
        )

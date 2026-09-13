from uuid import uuid4
from sqlalchemy import ForeignKey, Integer, Text, ARRAY, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("documents.id", ondelete="CASCADE"), 
        nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)  # Mảng Float (768 chiều) thay vì pgvector để tương thích mọi hệ thống
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Quan hệ N-1 về document gốc
    document = relationship("Document", back_populates="chunks")

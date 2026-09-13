import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv(override=True)

from app.database import AsyncSessionLocal
from app.rag.ingest_service import IngestService
from app.rag.retriever import PGVectorRetriever
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from sqlalchemy import select, delete


async def test_rag_flow():
    # 1. Create a temporary text file with network guides
    sample_content = (
        "Cấu hình định tuyến OSPF trên Router Cisco:\n"
        "Để kích hoạt giao thức OSPF, ta sử dụng lệnh 'router ospf <process-id>'.\n"
        "Sau đó, sử dụng lệnh 'network <ip-address> <wildcard-mask> area <area-id>' để quảng bá mạng.\n"
        "Ví dụ cấu hình mẫu OSPF:\n"
        "router ospf 1\n"
        " network 192.168.1.0 0.0.0.255 area 0\n"
        " network 10.0.0.0 0.0.0.3 area 0\n"
    )
    
    temp_file = Path("tests/sample_network_guide.txt")
    temp_file.parent.mkdir(exist_ok=True)
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(sample_content)
        
    print(f"[+] Đã tạo file kiểm thử tạm thời: {temp_file}")
    
    async with AsyncSessionLocal() as db:
        try:
            # 2. Ingest file into database
            print("\n--- Bắt đầu Ingest ---")
            ingest_result = await IngestService.ingest_file(
                db=db,
                file_path=temp_file,
                title="Hướng dẫn OSPF Cisco",
                category="test_network",
                chunk_size=200,
                chunk_overlap=50
            )
            doc_id = ingest_result["document_id"]
            
            # 3. Retrieve chunks using retriever
            print("\n--- Bắt đầu Retrieve ---")
            retriever = PGVectorRetriever()
            query = "Làm cách nào để cấu hình quảng bá interface trong OSPF?"
            results = await retriever.retrieve(db, query, top_k=2, category="test_network")
            
            print(f"\n[Kết quả tìm kiếm cho câu hỏi: '{query}']: ")
            for idx, res in enumerate(results):
                print(f"Top {idx+1} (Score: {res['score']:.4f}):")
                print(f"Nguồn: {res['document_title']} (Trang: {res['page']})")
                print(f"Nội dung:\n{res['content']}\n")
                
            # Verify top chunk matches expectations
            assert len(results) > 0, "Không trả về kết quả tìm kiếm nào!"
            assert "network" in results[0]["content"], "Kết quả tìm kiếm không chứa từ khóa cấu hình mạng mong đợi!"
            print("[✔] Kiểm tra kết quả tìm kiếm thành công!")
            
            # 4. Verify cascade delete
            print("\n--- Kiểm tra Cascade Delete ---")
            # Delete parent document
            await db.execute(delete(Document).where(Document.id == doc_id))
            await db.commit()
            
            # Check if chunks are deleted
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc_id))
            chunks = result.scalars().all()
            assert len(chunks) == 0, "Lỗi: Cascade delete không hoạt động, các chunks vẫn tồn tại!"
            print("[✔] Kiểm tra xóa Cascade Delete thành công!")
            
        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()
                print("[+] Đã xóa file kiểm thử tạm thời.")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_rag_flow())

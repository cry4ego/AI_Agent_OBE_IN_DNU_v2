import os, re, asyncio, torch, glob
import numpy as np
from typing import List
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from sentence_transformers import SentenceTransformer
from langchain_core.embeddings import Embeddings
from utils.local_llm import generate_response  # Qwen local
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.document_loaders import WebBaseLoader
from typing import List, Dict, Any, Optional
# ============================================================
# 1. Embedding LOCAL
# ============================================================
class LocalEmbedding(Embeddings):
    def __init__(self):
        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    def embed_documents(self, texts):
        return self.model.encode(texts, normalize_embeddings=True)

    def embed_query(self, text):
        return self.model.encode(text, normalize_embeddings=True)

# ============================================================
# 2. Chunking
# ============================================================
def chunk_all_md(base_dir: str) -> List[Document]:
    all_docs = []
    
    # Sử dụng os.path.abspath để chuyển về đường dẫn tuyệt đối, tránh lỗi đứng sai vị trí
    absolute_base_dir = os.path.abspath(base_dir)
    
    # Mẫu tìm kiếm: quét sâu vào tất cả thư mục con (**) để tìm file .md
    search_pattern = os.path.join(absolute_base_dir, "**", "*.md")
    
    # recursive=True cho phép quét sâu vào các thư mục như HD_Laodong, CS_Hr...
    files = glob.glob(search_pattern, recursive=True)
    
    print(f"--- Đang quét tại: {absolute_base_dir} ---")
    print(f"Tìm thấy {len(files)} file .md")
    
    if len(files) == 0:
        print("⚠️ CẢNH BÁO: Không tìm thấy file nào. Kiểm tra lại đường dẫn!")
        # In ra nội dung thư mục để debug
        if os.path.exists(absolute_base_dir):
            print(f"Nội dung thư mục gốc: {os.listdir(absolute_base_dir)}")

    for fpath in files:
        print(f"  > Đang xử lý: {os.path.relpath(fpath, absolute_base_dir)}")
        docs = chunk_single_md(fpath)
        all_docs.extend(docs)
    return all_docs

def chunk_single_md(file_path: str) -> List[Document]:
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    source = os.path.basename(file_path)
    pattern = r"^Điều\s+(\d+)[\.\:]\s*(.*)$"
    matches = list(re.finditer(pattern, text, re.MULTILINE))
    docs = []
    if not matches:
        docs.append(Document(page_content=text[:2000], metadata={"source_file": source}))
        return docs
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        block = text[start:end].strip()
        so_dieu = m.group(1)
        tieu_de = m.group(2).strip() if m.group(2) else ""
        lines = block.split("\n")
        header = lines[0].strip()
        content = "\n".join(lines[1:]).strip()
        if len(content) > 1000:
            sub_docs = split_by_clause(content, so_dieu, tieu_de, header, source)
            docs.extend(sub_docs)
        else:
            docs.append(Document(
                page_content=f"{header}\n{content}",
                metadata={"source_file": source, "dieu": so_dieu, "tieu_de": tieu_de}
            ))
    return docs

def split_by_clause(text: str, so_dieu: str, tieu_de: str, header: str, source: str) -> List[Document]:
    clause_pattern = r"^(\d+\.|[a-z]\))\s*.*$"
    clauses = list(re.finditer(clause_pattern, text, re.MULTILINE))
    if not clauses:
        return [Document(page_content=text[:2000], metadata={
            "source_file": source, "dieu": so_dieu, "tieu_de": tieu_de
        })]
    docs = []
    for j, cl in enumerate(clauses):
        start = cl.start()
        end = clauses[j+1].start() if j+1 < len(clauses) else len(text)
        chunk_text = text[start:end].strip()
        if len(chunk_text) > 1500:
            chunk_text = chunk_text[:1500] + "..."
        docs.append(Document(
            page_content=chunk_text,
            metadata={"source_file": source, "dieu": so_dieu, "tieu_de": tieu_de, "khoan": cl.group(1)}
        ))
    return docs

# ============================================================
# 3. Index Qdrant
# ============================================================
def build_index(docs: List[Document]):
    emb = LocalEmbedding()
    client = QdrantClient(":memory:")
    col_name = "vn_law_docs"
    if client.collection_exists(col_name):
        client.delete_collection(col_name)
    client.create_collection(
        collection_name=col_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )
    vs = QdrantVectorStore(client=client, collection_name=col_name, embedding=emb)
    vs.add_documents(docs)
    return vs

# ============================================================
# 4. LLM Relevance Gate (thay thế ngưỡng số)
# ============================================================
async def llm_relevance_gate(question: str, context: str) -> bool:
    """
    Dùng Qwen để đánh giá ngữ cảnh có thực sự chứa câu trả lời không.
    Đây là giải pháp thay thế cho ngưỡng similarity score đơn thuần.
    """
    prompt = f"""Bạn là chuyên gia đánh giá mức độ liên quan của tài liệu pháp lý.

Câu hỏi: {question}

Ngữ cảnh tìm được:
{context[:2000]}

Hãy trả lời CHÍNH XÁC một trong hai từ: "CÓ" hoặc "KHÔNG".
- "CÓ" nếu ngữ cảnh chứa thông tin để trả lời câu hỏi.
- "KHÔNG" nếu ngữ cảnh không liên quan hoặc không đủ thông tin.

Trả lời:"""
    messages = [{"role": "user", "content": prompt}]
    answer = generate_response(messages, max_new_tokens=10)
    return "CÓ" in answer.upper()

# ============================================================
# 5. Conditional Router với LLM Gate + Web Fallback + Fusion
# ============================================================
async def ask_with_smart_router(question: str, vs):
    """
    Pipeline thông minh:
    1. Tìm trong RAG nội bộ
    2. Dùng LLM Gate kiểm tra ngữ cảnh có thực sự liên quan
    3. Nếu KHÔNG → Web Search
    4. Fusion: kết hợp cả hai nguồn để có câu trả lời tốt nhất
    """
    # Bước 1: Tìm kiếm trong RAG
    retriever = vs.as_retriever(search_type="similarity", search_kwargs={"k": 5})
    rag_docs = retriever.invoke(question)
    
    # Chuẩn bị context từ RAG
    rag_context = ""
    rag_sources = []
    if rag_docs:
        context_parts = []
        for idx, doc in enumerate(rag_docs, start=1):
            src = doc.metadata.get("source_file", "unknown")
            dieu = doc.metadata.get("dieu", "")
            khoan = doc.metadata.get("khoan", "")
            tieu_de = doc.metadata.get("tieu_de", "")
            header = f"[Nguồn {idx}: {src}, Điều {dieu}"
            if khoan:
                header += f", Khoản {khoan}"
            header += f" – {tieu_de}]\n"
            context_parts.append(header + doc.page_content)
            rag_sources.append(doc.metadata)
        rag_context = "\n\n".join(context_parts)
    
    # Bước 2: LLM Relevance Gate
    print(" Đang kiểm tra mức độ liên quan của ngữ cảnh RAG...")
    is_relevant = await llm_relevance_gate(question, rag_context) if rag_context else False
    print(f"   Kết quả: {'CÓ' if is_relevant else 'KHÔNG'}")
    
    web_context = ""
    web_sources = []
    
    if is_relevant:
        # Trường hợp RAG đủ thông tin
        print(" Sử dụng RAG nội bộ...")
        final_context = rag_context
        all_sources = rag_sources
        source_type = "RAG Nội bộ"
    else:
        # Trường hợp RAG không đủ → Web Search
        print(" RAG không đủ thông tin, chuyển sang Web Search...")
        try:
            search = GoogleSerperAPIWrapper()
            search_results = search.results(question, num_results=3)
            urls = [res.get("link") for res in search_results.get("organic", [])[:3] if res.get("link")]
            
            if urls:
                print(f"   Đã tìm thấy {len(urls)} URL từ web:")
                for u in urls:
                    print(f"   - {u}")
                
                loader = WebBaseLoader(urls)
                web_docs = loader.load()
                web_parts = []
                for idx, doc in enumerate(web_docs, start=1):
                    url = doc.metadata.get("source", "Unknown URL")
                    content = doc.page_content[:1500]
                    header = f"[Nguồn Web {idx}: {url}]\n"
                    web_parts.append(header + content)
                    web_sources.append({"source_url": url, "source_type": "web"})
                web_context = "\n\n".join(web_parts)
                
                # Fusion: kết hợp cả RAG và Web nếu RAG có ít thông tin
                if rag_context:
                    print(" Fusion: Kết hợp thông tin từ RAG và Web...")
                    final_context = f"=== THÔNG TIN TỪ CƠ SỞ DỮ LIỆU NỘI BỘ ===\n{rag_context[:2000]}\n\n=== THÔNG TIN TỪ WEB ===\n{web_context}"
                    all_sources = rag_sources + web_sources
                    source_type = "Fusion (RAG + Web)"
                else:
                    final_context = web_context
                    all_sources = web_sources
                    source_type = "Web Search"
            else:
                final_context = rag_context if rag_context else "Không tìm thấy thông tin."
                all_sources = rag_sources
                source_type = "RAG Nội bộ (fallback)"
                
        except Exception as e:
            print(f" Lỗi Web Search: {e}")
            final_context = rag_context if rag_context else "Không thể tìm kiếm."
            all_sources = rag_sources
            source_type = "RAG Nội bộ (web search failed)"
    
    # Bước cuối: Sinh câu trả lời
    prompt = f"""Bạn là trợ lý pháp lý. Dựa vào các thông tin dưới đây, trả lời câu hỏi.
Khi trả lời, hãy trích dẫn nguồn cụ thể (ví dụ: "Theo Điều X của Nghị định Y..." hoặc "Theo nguồn từ URL Z...").

{final_context}

Câu hỏi: {question}
Trả lời:"""
    messages = [{"role": "user", "content": prompt}]
    answer = generate_response(messages, max_new_tokens=512)
    
    return answer, all_sources, source_type

# ============================================================
# Main
# ============================================================
async def main():
    data_dir = "data/TaiLieu_Chatbot"
    print("Đang quét và chunking tất cả file .md...")
    docs = chunk_all_md(data_dir)
    print(f"Tổng số chunks: {len(docs)}")
    print("Đang tạo index (local embedding)...")
    vs = build_index(docs)
    print("Index thành công.")

    question = "Thiết kế giáo án giảng dạy cho các học phần thuộc lĩnh vực công nghệ thông tin, bao gồm: Mạng máy tính, Cơ sở dữ liệu, An ninh mạng, Lập trình hướng đối tượng, Trí tuệ nhân tạo. Mỗi học phần nên có ít nhất 5 buổi học, với nội dung chi tiết cho từng buổi."
    print(f"\nHỏi: {question}")
    
    answer, sources, source_type = await ask_with_smart_router(question, vs)
    
    print(f"\n{'='*60}")
    print(f" Trả lời:\n{answer}\n")
    print(f" Loại nguồn: {source_type}")
    print(f" Nguồn tham khảo:")
    for s in sources:
        if "source_url" in s:
            print(f"  - URL: {s.get('source_url')}")
        else:
            print(f"  - File: {s.get('source_file')}, Điều {s.get('dieu','?')} – {s.get('tieu_de','')}")

    torch.cuda.empty_cache()

if __name__ == "__main__":
    asyncio.run(main())
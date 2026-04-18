"""
RAG Index Builder - Khởi tạo vector store với kiến thức OBE
Sử dụng Qdrant in-memory để dễ triển khai, không cần server riêng
"""

import os
import json
from typing import Optional
from utils.logger import get_logger
from utils.obe_utils import (
    PLO_DATA, PI_DATA, BLOOM_LEVELS, IRMA_LEVELS,
    HTTT_PLO_DATA, HTTT_PI_DATA, HTTT_PO_DATA,
    KHMT_PLO_DATA, KHMT_PI_DATA,
    PROGRAM_DATA,
)

logger = get_logger("rag.index_builder")

# Global vector store instance
_vector_store = None
_retriever = None


EMBEDDING_DIMENSION = 768  # Gemini embedding-001 output dimension


async def initialize_rag(force_rebuild: bool = False) -> bool:
    """
    Khởi tạo RAG system với dữ liệu OBE.
    
    Args:
        force_rebuild: Rebuild index dù đã tồn tại
    
    Returns:
        True nếu thành công
    """
    global _vector_store, _retriever

    if _vector_store is not None and not force_rebuild:
        logger.info("RAG đã được khởi tạo, bỏ qua.")
        return True

    logger.info("Đang khởi tạo RAG system...")

    try:
        docs = _build_obe_documents()
        _vector_store = await _create_vector_store(docs)
        _retriever = _vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5},
        )
        logger.info(f"RAG khởi tạo thành công với {len(docs)} tài liệu OBE")
        return True

    except Exception as e:
        logger.warning(f"Không thể khởi tạo Qdrant vector store: {e}")
        logger.info("Sử dụng fallback: kiến thức OBE từ obe_utils trực tiếp")
        _vector_store = None
        _retriever = None
        return False


def _build_obe_documents() -> list:
    """Xây dựng danh sách Document từ dữ liệu OBE."""
    from langchain_core.documents import Document

    docs = []

    # PLO documents
    for plo_code, plo_desc in PLO_DATA.items():
        docs.append(
            Document(
                page_content=f"{plo_code}: {plo_desc}",
                metadata={"type": "plo", "code": plo_code},
            )
        )

    # PI documents (kèm PLO cha)
    for plo_code, pis in PI_DATA.items():
        for pi_code, pi_desc in pis.items():
            docs.append(
                Document(
                    page_content=f"{pi_code} (thuộc {plo_code}): {pi_desc}",
                    metadata={
                        "type": "pi",
                        "code": pi_code,
                        "parent_plo": plo_code,
                    },
                )
            )

    # Bloom taxonomy documents
    bloom_text = "\n".join(
        [f"Mức {lvl} - {name}: Các động từ hành động tiêu biểu"
         for lvl, name in BLOOM_LEVELS.items()]
    )
    docs.append(
        Document(
            page_content=f"Bloom Taxonomy - Thang đánh giá nhận thức:\n{bloom_text}",
            metadata={"type": "bloom"},
        )
    )

    # IRMA levels document
    irma_text = "\n".join(
        [f"{level}: {desc}" for level, desc in IRMA_LEVELS.items()]
    )
    docs.append(
        Document(
            page_content=f"Mức độ IRMA trong OBE:\n{irma_text}",
            metadata={"type": "irma"},
        )
    )

    # OBE principles document
    docs.append(
        Document(
            page_content="""Nguyên tắc OBE (Outcome-Based Education):
1. CLO phải SMART: Specific, Measurable, Achievable, Relevant, Time-bound
2. Constructive Alignment: CLO → Teaching Activities → Assessment phải nhất quán
3. Assessment as Learning: đánh giá là công cụ học tập, không chỉ kiểm tra
4. Continuous Improvement: DCCT được cải tiến liên tục qua phản hồi
5. Student-Centered: thiết kế từ chuẩn đầu ra của sinh viên""",
            metadata={"type": "obe_principles"},
        )
    )

    # ---- Dữ liệu chương trình thực tế: HTTT & KHMT ----
    docs.extend(_build_program_documents("HTTT", HTTT_PLO_DATA, HTTT_PI_DATA, HTTT_PO_DATA))
    docs.extend(_build_program_documents("KHMT", KHMT_PLO_DATA, KHMT_PI_DATA, {}))

    # ---- Nạp tài liệu Markdown từ TailieuMD ----
    docs.extend(_load_tailieu_md_documents())

    return docs


def _build_program_documents(
    program_code: str,
    plo_data: dict,
    pi_data: dict,
    po_data: dict,
) -> list:
    """Xây dựng documents cho một chương trình đào tạo cụ thể."""
    from langchain_core.documents import Document

    docs = []
    program_info = PROGRAM_DATA.get(program_code, {})
    program_name = program_info.get("name", program_code)

    # PLO documents
    for plo_code, plo_desc in plo_data.items():
        docs.append(
            Document(
                page_content=f"[{program_code}] {plo_code}: {plo_desc}",
                metadata={"type": "plo", "code": plo_code, "program": program_code},
            )
        )

    # PI documents
    for plo_code, pis in pi_data.items():
        plo_desc = plo_data.get(plo_code, "")
        for pi_code, pi_desc in pis.items():
            docs.append(
                Document(
                    page_content=f"[{program_code}] {pi_code} (thuộc {plo_code}): {pi_desc}",
                    metadata={
                        "type": "pi",
                        "code": pi_code,
                        "parent_plo": plo_code,
                        "program": program_code,
                    },
                )
            )

    # PO documents
    for po_code, po_desc in po_data.items():
        docs.append(
            Document(
                page_content=f"[{program_code}] {po_code} - {program_name}: {po_desc}",
                metadata={"type": "po", "code": po_code, "program": program_code},
            )
        )

    return docs


def _load_tailieu_md_documents() -> list:
    """
    Nạp các tài liệu Markdown thực tế từ thư mục TailieuMD.
    Hỗ trợ HTTT và KHMT, bỏ qua file lỗi mã hóa.
    """
    from langchain_core.documents import Document

    docs = []

    # Tìm thư mục TailieuMD từ workspace root
    workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tailieu_base = os.path.join(os.path.dirname(workspace_root), "TailieuMD")

    # Fallback: tìm bên trong cùng thư mục workspace
    if not os.path.isdir(tailieu_base):
        tailieu_base = os.path.join(workspace_root, "..", "TailieuMD")
    if not os.path.isdir(tailieu_base):
        logger.warning(f"Không tìm thấy thư mục TailieuMD tại: {tailieu_base}")
        return docs

    program_dirs = {
        "HTTT": os.path.join(tailieu_base, "HTTT"),
        "KHMT": os.path.join(tailieu_base, "KHMT"),
    }

    for program_code, dir_path in program_dirs.items():
        if not os.path.isdir(dir_path):
            logger.warning(f"Không tìm thấy thư mục {program_code}: {dir_path}")
            continue

        md_files = [f for f in os.listdir(dir_path) if f.endswith(".md")]
        loaded = 0
        for fname in md_files:
            fpath = os.path.join(dir_path, fname)
            try:
                with open(fpath, encoding="utf-8") as fp:
                    content = fp.read().strip()
                if not content:
                    continue
                # Giới hạn 4000 ký tự / chunk để tránh quá tải embedding
                chunks = [content[i : i + 4000] for i in range(0, len(content), 4000)]
                for idx, chunk in enumerate(chunks):
                    docs.append(
                        Document(
                            page_content=f"[{program_code}][{fname}] {chunk}",
                            metadata={
                                "type": "tailieu_md",
                                "program": program_code,
                                "filename": fname,
                                "chunk_index": idx,
                            },
                        )
                    )
                loaded += 1
            except Exception as e:
                logger.warning(f"Bỏ qua file {fname}: {e}")

        logger.info(f"Đã nạp {loaded}/{len(md_files)} tài liệu Markdown cho {program_code}")

    return docs


async def _create_vector_store(docs: list):
    """Tạo Qdrant in-memory vector store."""
    from langchain_qdrant import QdrantVectorStore
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams

    from config import GOOGLE_API_KEY

    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=GOOGLE_API_KEY,
        )
    except Exception:
        # Fallback: dùng fake embeddings nếu không có API
        from langchain_core.embeddings import FakeEmbeddings
        embeddings = FakeEmbeddings(size=768)

    # Tạo Qdrant in-memory client
    client = QdrantClient(":memory:")
    collection_name = "obe_knowledge"

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=EMBEDDING_DIMENSION, distance=Distance.COSINE),
    )

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )

    vector_store.add_documents(docs)
    return vector_store


def get_retriever():
    """Lấy retriever đã khởi tạo."""
    return _retriever


def is_initialized() -> bool:
    """Kiểm tra RAG đã được khởi tạo chưa."""
    return _vector_store is not None

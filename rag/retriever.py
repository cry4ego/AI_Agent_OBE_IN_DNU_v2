"""
RAG Retriever — Lớp RAG (Layer 2) — Prose / Examples only

CHỈ truy xuất nội dung prose từ TailieuMD và DCCT examples.
KHÔNG truy xuất PLO/PI rules, IRMA rules, Bloom taxonomy.

Nguyên tắc:
  • PLO/PI rules → utils/kb.py (deterministic, function call)
  • Prose context → module này (cosine similarity, supplementary only)

Lý do: nếu PLO/PI ở đây, cosine similarity có thể miss rule cần thiết
→ agent mapping sai mà không có gì catch lại.
"""

from typing import List, Optional
from utils.logger import get_logger

logger = get_logger("rag.retriever")


def retrieve_tailieu_context(
    query: str,
    program: Optional[str] = None,
    k: int = 5,
) -> List[str]:
    """
    Truy xuất đoạn prose từ TailieuMD phù hợp với query.

    Dùng để bổ sung ngữ cảnh domain-specific vào prompt, KHÔNG dùng để tra rule.

    Args:
        query   : Từ khóa / mô tả CLO / tên học phần
        program : Lọc theo chương trình (HTTT / KHMT), None = không lọc
        k       : Số chunk trả về

    Returns:
        Danh sách đoạn text prose liên quan (có thể rỗng nếu RAG chưa init).
    """
    from rag.index_builder import get_retriever

    retriever = get_retriever()

    if retriever is None:
        return []

    try:
        docs = retriever.invoke(query)
        md_docs = [d for d in docs if d.metadata.get("type") == "tailieu_md"]
        if program:
            md_docs = [d for d in md_docs if d.metadata.get("program") == program]
        return [d.page_content for d in md_docs[:k]]
    except Exception as e:
        logger.warning("Lỗi RAG retrieval TailieuMD: %s", e)
        return []


def retrieve_domain_context(
    query: str,
    program: Optional[str] = None,
    k: int = 3,
) -> str:
    """
    Convenience wrapper: trả về prose context dạng 1 chuỗi để append vào prompt.
    Trả về chuỗi rỗng nếu RAG chưa init hoặc không tìm thấy gì.
    """
    chunks = retrieve_tailieu_context(query, program=program, k=k)
    if not chunks:
        return ""
    return "\n\n".join(chunks)


# ── TASK 4: Reranker với cross-encoder ────────────────────────────────────────

def rerank_results(
    docs: list,
    query: str,
    top_k: int = 5,
) -> list:
    """
    Sắp xếp lại kết quả retrieval bằng cross-encoder reranker.
    """
    if not docs:
        return docs

    try:
        from sentence_transformers import CrossEncoder

        model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        pairs = [(query, d.page_content) for d in docs]
        scores = model.predict(pairs)

        scored_docs = sorted(
            zip(docs, scores), key=lambda x: x[1], reverse=True
        )
        reranked = [doc for doc, _ in scored_docs[:top_k]]
        return reranked

    except Exception as e:
        # Nếu không load được cross-encoder, trả về top_k docs ban đầu
        return docs[:top_k]

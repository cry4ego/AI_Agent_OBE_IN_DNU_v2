import asyncio
import time
from utils.llm_helper import call_llm_json_async
from utils.logger import get_logger
from prompts.legal_agent_prompt import LEGAL_ADVISOR_SYSTEM_PROMPT

logger = get_logger("agents.legal_agent")

async def legal_advisor_node(state: dict) -> dict:
    query = state.get("legal_question", state.get("user_input", ""))
    if not query:
        state["errors"] = state.get("errors", []) + ["Không có câu hỏi pháp lý."]
        return state

    logger.info(f"[LegalAgent] Nhận câu hỏi: {query[:100]}...")

    # 1. Lấy ngữ cảnh từ RAG Legal với hybrid+BM25 (nếu có) hoặc vector search
    from rag.index_builder import get_legal_retriever
    retriever = get_legal_retriever()
    if retriever is None:
        state["errors"] = state.get("errors", []) + ["RAG Legal chưa được khởi tạo."]
        return state

    # Thử dùng hybrid search (nếu có module BM25) để tăng recall
    try:
        from rag.retriever import retrieve_hybrid, retrieve_hybrid_bm25
        # Sử dụng hybrid với RRF nếu khả dụng
        hybrid_results = retrieve_hybrid_bm25(
            query=query, session_id=None, k_obe=5, k_course=5, use_rerank=True, rerank_top_k=3
        )
        combined_context = "\n\n".join(hybrid_results["combined"][:3])  # chỉ lấy top-3
        raw_docs = hybrid_results.get("course", [])  # "course" thực ra là legal docs
    except Exception:
        # Fallback về vector search nếu hybrid không khả dụng
        raw_docs = retriever.invoke(query)
        combined_context = "\n\n".join([d.page_content[:800] for d in raw_docs[:3]])
    
    if not combined_context:
        state["errors"] = state.get("errors", []) + ["Không tìm thấy tài liệu liên quan."]
        return state

    # 2. Giới hạn context tối đa 2000 ký tự
    if len(combined_context) > 2000:
        combined_context = combined_context[:2000] + "..."

    # 3. Gọi LLM với timeout 600 giây và context đã tinh gọn
    start_time = time.time()
    try:
        raw_response = await asyncio.wait_for(
            call_llm_json_async(
                "legal_advisor",
                LEGAL_ADVISOR_SYSTEM_PROMPT.format(context=combined_context, question=query),
                query,  # user_prompt chỉ là câu hỏi
                timeout=600
            ),
            timeout=600
        )
        elapsed = time.time() - start_time
        logger.info(f"[LegalAgent] LLM phản hồi sau {elapsed:.1f}s")
        state["legal_answer"] = raw_response
        state["legal_contexts"] = [combined_context]
        state["legal_sources"] = []
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        logger.error(f"[LegalAgent] Timeout sau {elapsed:.1f}s")
        state["errors"] = state.get("errors", []) + [f"AI không phản hồi sau {elapsed:.1f} giây."]
    except Exception as e:
        logger.error(f"[LegalAgent] Lỗi: {e}")
        state["errors"] = state.get("errors", []) + [f"Lỗi LLM: {e}"]

    return state

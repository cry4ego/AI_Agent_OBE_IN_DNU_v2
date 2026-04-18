"""
QA Agent - Hỏi đáp dựa trên ĐCCT đã được tạo.

Đầu ra kép (dual output):
  GV (giảng viên) — câu trả lời kỹ thuật OBE + căn cứ PLO/PI/CLO
  SV (sinh viên)  — câu trả lời dễ hiểu + gợi ý học tập

Không nằm trong LangGraph main graph;
được gọi trực tiếp qua standalone function hoặc Streamlit session.
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from utils.logger import get_logger
from utils.llm_helper import get_llm
from rag.dcct_store import (
    index_dcct,
    retrieve_for_question,
    get_indexed_courses,
    get_dcct_summary,
)
from prompts.qa_prompt import get_qa_system_prompt, build_qa_user_prompt

logger = get_logger("agents.qa_agent")


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def index_dcct_from_state(course_code: str, state: Dict[str, Any]) -> Dict:
    """
    Index ĐCCT vào knowledge base sau khi agent hoàn thành.
    Trả về metadata tóm tắt.

    Args:
        course_code: Mã học phần
        state      : DCCTState đầy đủ

    Returns:
        {"course_code", "chunks_indexed", "clo_count", "session_count", "assessment_count"}
    """
    n = index_dcct(course_code, state)
    return {
        "course_code":      course_code,
        "chunks_indexed":   n,
        "clo_count":        len(state.get("clo_list", [])),
        "session_count":    len(state.get("teaching_plan", [])),
        "assessment_count": len(state.get("assessment_plan", [])),
    }


async def ask_dcct(
    course_code: str,
    question: str,
    role: str = "sv",
    history: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Đặt câu hỏi cho ĐCCT (async).

    Args:
        course_code: Mã học phần
        question   : Câu hỏi
        role       : "gv" hoặc "sv"
        history    : Lịch sử hội thoại [{role: "user"|"assistant", content: str}]

    Returns:
        {
          "answer"         : str,       # Câu trả lời đầy đủ
          "answer_gv"      : str,       # Phần trả lời cho GV (nếu role="gv")
          "answer_sv"      : str,       # Phần trả lời cho SV (nếu role="sv")
          "sources"        : list,      # Chunks đã dùng để trả lời
          "course_code"    : str,
          "role"           : str,
          "warning"        : str,       # Empty nếu không có cảnh báo
        }
    """
    history = history or []

    # Retrieve relevant chunks
    chunks, warning = retrieve_for_question(course_code, question, role, top_k=6)

    if warning:
        logger.warning(f"[QA] {warning}")
        return {
            "answer":    warning,
            "answer_gv": warning if role == "gv" else "",
            "answer_sv": warning if role == "sv" else "",
            "sources":   [],
            "course_code": course_code,
            "role":      role,
            "warning":   warning,
        }

    # Get course info from first chunk metadata
    meta        = chunks[0]["metadata"] if chunks else {}
    course_name = meta.get("course_name", course_code)

    # Build prompts
    system = get_qa_system_prompt(role)
    user   = build_qa_user_prompt(
        question        = question,
        role            = role,
        course_code     = course_code,
        course_name     = course_name,
        retrieved_chunks= chunks,
        history         = history,
    )

    # Call LLM (plain text, not JSON)
    try:
        llm      = get_llm("qa")
        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ]
        from langchain_core.messages import SystemMessage, HumanMessage
        lc_messages = [SystemMessage(content=system), HumanMessage(content=user)]
        response    = await llm.ainvoke(lc_messages)
        answer      = response.content

        logger.info(
            f"[QA] {course_code} | role={role} | "
            f"Q: {question[:60]}... | ans_len={len(answer)}"
        )

        return {
            "answer":      answer,
            "answer_gv":   answer if role == "gv" else _extract_gv_from_answer(answer),
            "answer_sv":   answer if role == "sv" else _extract_sv_from_answer(answer),
            "sources":     [
                {"section": c["section"], "content": c["content"][:200]}
                for c in chunks
            ],
            "course_code": course_code,
            "role":        role,
            "warning":     "",
        }

    except Exception as e:
        logger.error(f"[QA] Lỗi gọi LLM: {e}")
        return {
            "answer":      f"Lỗi xử lý câu hỏi: {e}",
            "answer_gv":   "",
            "answer_sv":   "",
            "sources":     [],
            "course_code": course_code,
            "role":        role,
            "warning":     str(e),
        }


def ask_dcct_sync(
    course_code: str,
    question: str,
    role: str = "sv",
    history: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Wrapper đồng bộ cho ask_dcct (dùng trong Streamlit).
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            ask_dcct(course_code, question, role, history)
        )
    finally:
        loop.close()


async def ask_dcct_dual(
    course_code: str,
    question: str,
    history: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Gọi song song cả GV lẫn SV, trả về đầu ra kép.
    Dùng asyncio.gather để tối ưu thời gian chờ.

    Returns:
        {
          "answer_gv": str,
          "answer_sv": str,
          "sources"  : list,
          "course_code": str,
          "warning"  : str,
        }
    """
    gv_task = ask_dcct(course_code, question, "gv", history)
    sv_task = ask_dcct(course_code, question, "sv", history)

    gv_result, sv_result = await asyncio.gather(gv_task, sv_task)

    return {
        "answer_gv":   gv_result["answer"],
        "answer_sv":   sv_result["answer"],
        "sources":     gv_result["sources"],   # giống nhau, dùng 1 bên
        "course_code": course_code,
        "warning":     gv_result["warning"] or sv_result["warning"],
    }


def ask_dcct_dual_sync(
    course_code: str,
    question: str,
    history: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """Wrapper đồng bộ cho ask_dcct_dual."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(ask_dcct_dual(course_code, question, history))
    finally:
        loop.close()


def get_suggested_questions(course_code: str, role: str = "sv") -> List[str]:
    """
    Trả về danh sách câu hỏi gợi ý dựa trên nội dung ĐCCT.

    Args:
        course_code: Mã học phần
        role       : "gv" hoặc "sv"

    Returns:
        Danh sách câu hỏi gợi ý
    """
    summary = get_dcct_summary(course_code)
    course_name = summary.get("course_name", course_code) if summary else course_code

    if role == "gv":
        return [
            f"CLO của {course_name} được phân bổ mức Bloom như thế nào?",
            "Mức độ bao phủ CLO trong kế hoạch giảng dạy ra sao?",
            "Trọng số đánh giá có phù hợp với mức độ Bloom không?",
            "CLO nào chưa được bao phủ đầy đủ trong teaching plan?",
            "Ánh xạ CLO → PLO có đảm bảo tính nhất quán không?",
            "Phân bổ tiết lý thuyết và thực hành có hợp lý không?",
        ]
    else:
        return [
            f"Học phần {course_name} gồm những nội dung gì?",
            "Mình cần đạt được những kỹ năng gì sau khi học xong?",
            "Điểm học phần được tính như thế nào?",
            "Buổi nào có kiểm tra hoặc thực hành quan trọng?",
            "Mình cần chuẩn bị gì cho các buổi lab?",
            "Làm thế nào để đạt điểm tốt trong học phần này?",
        ]


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_gv_from_answer(answer: str) -> str:
    """Trích phần "Câu trả lời chính" từ câu trả lời GV."""
    lines = answer.split("\n")
    section = []
    in_main = False
    for line in lines:
        if "### Câu trả lời chính" in line:
            in_main = True
            continue
        if line.startswith("###") and in_main:
            break
        if in_main:
            section.append(line)
    return "\n".join(section).strip() or answer


def _extract_sv_from_answer(answer: str) -> str:
    """Trích phần "Trả lời ngắn gọn" từ câu trả lời SV."""
    lines = answer.split("\n")
    section = []
    in_main = False
    for line in lines:
        if "### Trả lời ngắn gọn" in line:
            in_main = True
            continue
        if line.startswith("###") and in_main:
            break
        if in_main:
            section.append(line)
    return "\n".join(section).strip() or answer

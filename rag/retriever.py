"""
RAG Retriever - Truy xuất thông tin OBE từ vector store
Fallback về dữ liệu tĩnh nếu RAG chưa được khởi tạo
"""

from typing import List, Optional
from utils.logger import get_logger
from utils.obe_utils import (
    PLO_DATA, PI_DATA, get_pi_list_text, get_plo_list_text,
    get_pi_description, get_plo_for_pi,
    ALL_PLO_DATA, ALL_PI_DATA,
    PROGRAM_DATA,
    get_program_plo_data, get_program_pi_data,
    get_plo_list_text_for_program, get_pi_list_text_for_program,
    detect_program_from_plo,
)

logger = get_logger("rag.retriever")


def retrieve_relevant_plos(query: str, k: int = 5, program: Optional[str] = None) -> List[str]:
    """
    Truy xuất PLO liên quan đến query.
    
    Args:
        query: Câu hỏi/mô tả để tìm PLO phù hợp
        k: Số kết quả trả về
        program: Mã chương trình (HTTT/KHMT/GENERIC), None = tất cả
    
    Returns:
        Danh sách mô tả PLO liên quan
    """
    from rag.index_builder import get_retriever

    retriever = get_retriever()

    if retriever is not None:
        try:
            docs = retriever.invoke(query)
            plo_docs = [d for d in docs if d.metadata.get("type") == "plo"]
            if program:
                plo_docs = [d for d in plo_docs if d.metadata.get("program") == program]
            return [d.page_content for d in plo_docs[:k]]
        except Exception as e:
            logger.warning(f"Lỗi RAG retrieval: {e}, dùng fallback")

    # Fallback: trả về PLO của chương trình tương ứng
    plo_data = get_program_plo_data(program) if program else ALL_PLO_DATA
    return [f"{code}: {desc}" for code, desc in list(plo_data.items())[:k]]


def retrieve_relevant_pis(query: str, k: int = 8, program: Optional[str] = None) -> List[str]:
    """
    Truy xuất PI liên quan đến query.
    
    Args:
        query: Mô tả CLO/nội dung để tìm PI phù hợp
        k: Số kết quả trả về
        program: Mã chương trình (HTTT/KHMT/GENERIC), None = tất cả
    
    Returns:
        Danh sách mô tả PI liên quan
    """
    from rag.index_builder import get_retriever

    retriever = get_retriever()

    if retriever is not None:
        try:
            docs = retriever.invoke(query)
            pi_docs = [d for d in docs if d.metadata.get("type") == "pi"]
            if program:
                pi_docs = [d for d in pi_docs if d.metadata.get("program") == program]
            return [d.page_content for d in pi_docs[:k]]
        except Exception as e:
            logger.warning(f"Lỗi RAG retrieval: {e}, dùng fallback")

    # Fallback: trả về PI từ chương trình tương ứng
    pi_data = get_program_pi_data(program) if program else ALL_PI_DATA
    results = []
    for plo_code, pis in list(pi_data.items())[:4]:
        for pi_code, pi_desc in pis.items():
            results.append(f"{pi_code} (thuộc {plo_code}): {pi_desc}")
    return results[:k]


def retrieve_tailieu_context(query: str, program: Optional[str] = None, k: int = 5) -> List[str]:
    """
    Truy xuất nội dung tài liệu TailieuMD liên quan.
    
    Args:
        query: Câu hỏi/từ khóa tìm kiếm
        program: Lọc theo chương trình (HTTT/KHMT)
        k: Số kết quả trả về
    
    Returns:
        Danh sách đoạn nội dung tài liệu liên quan
    """
    from rag.index_builder import get_retriever

    retriever = get_retriever()

    if retriever is not None:
        try:
            docs = retriever.invoke(query)
            md_docs = [d for d in docs if d.metadata.get("type") == "tailieu_md"]
            if program:
                md_docs = [d for d in md_docs if d.metadata.get("program") == program]
            return [d.page_content for d in md_docs[:k]]
        except Exception as e:
            logger.warning(f"Lỗi RAG retrieval TailieuMD: {e}")

    return []


def get_full_obe_context(program: Optional[str] = None) -> str:
    """
    Lấy toàn bộ context OBE để đưa vào prompt.
    Sử dụng khi cần toàn bộ dữ liệu PLO/PI.
    
    Args:
        program: Mã chương trình (HTTT/KHMT/GENERIC), None = GENERIC
    """
    prog = program or "GENERIC"
    return f"""=== CHUẨN ĐẦU RA CHƯƠNG TRÌNH (PLO) - {prog} ===
{get_plo_list_text_for_program(prog)}

=== CHỈ SỐ NĂNG LỰC (PI) - {prog} ===
{get_pi_list_text_for_program(prog)}"""


def get_plo_pi_context_for_course(
    course_name: str,
    clo_descriptions: List[str],
    program: Optional[str] = None,
) -> str:
    """
    Lấy context PLO/PI phù hợp nhất cho học phần và CLO.
    
    Args:
        course_name: Tên học phần
        clo_descriptions: Danh sách mô tả CLO
        program: Mã chương trình (HTTT/KHMT/GENERIC)
    
    Returns:
        Text context với PLO/PI liên quan
    """
    # Kết hợp course name và CLO descriptions để tìm context
    combined_query = f"{course_name} " + " ".join(clo_descriptions[:3])

    relevant_pis = retrieve_relevant_pis(combined_query, k=10, program=program)

    if not relevant_pis:
        return get_full_obe_context(program)

    prog = program or "GENERIC"
    return f"""=== DANH SÁCH PLO (Chuẩn đầu ra chương trình - {prog}) ===
{get_plo_list_text_for_program(prog)}

=== PI LIÊN QUAN NHẤT ===
""" + "\n".join(relevant_pis)

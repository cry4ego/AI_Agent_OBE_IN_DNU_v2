# main.py
import asyncio
from config import validate_config
from state import DCCTState
from graph import get_graph
from rag.index_builder import initialize_rag
from rag.document_loader import read_file   # thêm import

async def run_agent(
    course_code: str,
    course_name: str,
    summary: str,
    credits: str = "3",
    program: str = None,
    outline: str = None,
    irma_matrix: dict = None,
    periods_per_session: int = 5,
    theory_per_session: int = 3,
):
    if not validate_config():
        return None

    await initialize_rag()

    initial_state: DCCTState = {
        "user_input": f"{course_code} - {course_name}\n{summary}",
        "course_code": course_code,
        "course_name": course_name,
        "credits": credits,
        "summary": summary,
        "program": program,
        "outline": outline,
        "outline_provided": bool(outline and outline.strip()),
        "outline_sessions": [],
        "session_clo_map": {},
        "irma_matrix": irma_matrix,
        "periods_per_session": periods_per_session,
        "theory_per_session": theory_per_session,
        "extracted_info": {},
        "clo_list": [],
        "mapping_matrix": [],
        "teaching_plan": [],
        "assessment_plan": [],
        "rubrics": {},
        "messages": [],
        "current_step": "understand",
        "confidence_score": 0.0,
        "critic_feedback": [],
        "retry_counts": {},
        "preview_data": None,
        "needs_human_input": False,
        "human_feedback": None,
        "final_dcct_data": None,
        "export_ready": False,
        "export_path": None,
        "qa_indexed": False,
        "qa_chunks_count": 0,
        "errors": [],
        "warnings": [],
    }

    graph = get_graph()

    try:
        config = {
            "configurable": {"thread_id": "1"},
            "recursion_limit": 200,
        }
        result = await graph.ainvoke(initial_state, config=config)
        print(f"✅ Hoàn thành. Confidence: {result.get('confidence_score', 0):.1f}%")
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    # Đọc file docx chứa lộ trình môn học
    outline_path = "uploads/Lộ trình học phần Xử lý ngôn ngữ tự nhiên.docx"
    try:
        outline_text = read_file(outline_path)
        print(f"✅ Đã đọc outline từ file: {outline_path}")
    except FileNotFoundError:
        print(f"⚠️ Không tìm thấy file {outline_path}, sẽ chạy không có outline.")
        outline_text = None
    except Exception as e:
        print(f"⚠️ Lỗi đọc file: {e}, sẽ chạy không có outline.")
        outline_text = None

    asyncio.run(run_agent(
        course_code="CSC4007",
        course_name="Xử lý ngôn ngữ tự nhiên",
        summary="Học phần về NLP và LLM, bao gồm prompt engineering, fine-tuning, RAG",
        credits="3",
        program="KHMT",
        outline=outline_text,   # truyền nội dung file docx
    ))
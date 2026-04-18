# state.py
from typing import TypedDict, List, Dict, Optional, Annotated
from langgraph.graph import add_messages
from pydantic import BaseModel


class CLO(BaseModel):
    code: str
    description: str
    bloom_verb: str
    pi_codes: List[str] = []
    mapping_level: str = ""


class OutlineSession(BaseModel):
    """Một buổi học được parse từ sườn GV — KHÔNG được thay đổi bởi agent."""
    no: int                          # Số thứ tự buổi (giữ nguyên từ GV)
    topic: str                       # Tên chủ đề (giữ nguyên văn GV)
    subtopics: List[str] = []        # Các nội dung nhỏ bên trong (nếu có)
    estimated_periods: int = 1       # Số tiết ước tính
    session_type: str = "LT"         # LT | TH (parse từ hint nếu có)


class Session(BaseModel):
    no: int
    content: str
    clo_codes: List[str] = []
    irma_level: str = ""
    activities: str = ""
    assessment: str = ""


class AssessmentComponent(BaseModel):
    code: str
    name: str
    weight: float = 0.0
    clo_mapping: List[str] = []
    rubric: Dict = {}


class DCCTState(TypedDict):
    # ── Input gốc ─────────────────────────────────────────────────────────────
    user_input: str
    course_code: str
    course_name: str
    credits: str
    summary: str
    program: Optional[str]           # "HTTT" | "KHMT" | "GENERIC" | None

    # Outline từ GV — raw text (bắt buộc được preserve)
    outline: Optional[str]

    # ── Trạng thái luồng outline ───────────────────────────────────────────────
    # True  = GV đã cung cấp outline → dùng Reverse-mapping flow
    # False = Không có outline → dùng Forward-generation flow
    outline_provided: bool

    # Outline sau khi parse thành cấu trúc (do Understand Agent tạo)
    # Đây là "xương sống" bất biến cho Teaching Plan
    outline_sessions: Optional[List[Dict]]   # List[OutlineSession.dict()]

    # Map buổi học → CLO (do Understand Agent sinh ngược từ outline)
    # VD: {"1": ["CLO1"], "2": ["CLO1", "CLO2"], ...}
    session_clo_map: Optional[Dict[str, List[str]]]

    # ── Processing ────────────────────────────────────────────────────────────
    extracted_info: Dict
    clo_list: List[CLO]
    mapping_matrix: List[Dict]
    teaching_plan: List[Session]     # Teaching Plan cuối cùng (giữ nguyên sườn GV nếu có)
    assessment_plan: List[AssessmentComponent]
    rubrics: Dict

    # ── Control ───────────────────────────────────────────────────────────────
    messages: Annotated[list, add_messages]
    current_step: str
    confidence_score: float

    # ── Validation ────────────────────────────────────────────────────────────
    critic_feedback: List[Dict]
    retry_counts: Dict[str, int]

    # ── Preview & Human ───────────────────────────────────────────────────────
    preview_data: Optional[Dict]
    needs_human_input: bool
    human_feedback: Optional[str]

    # ── Output ────────────────────────────────────────────────────────────────
    final_dcct_data: Optional[Dict]
    export_ready: bool
    export_path: Optional[str]

    # ── Q&A Knowledge Base ────────────────────────────────────────────────────
    # True sau khi ĐCCT được index vào knowledge base
    qa_indexed: bool
    # Số chunk đã index (thông tin hiển thị)
    qa_chunks_count: int

    errors: List[str]
    warnings: List[str]
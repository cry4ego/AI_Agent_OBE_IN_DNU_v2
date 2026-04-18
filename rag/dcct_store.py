"""
ĐCCT Knowledge Base Store

Lưu trữ và truy xuất nội dung ĐCCT đã được tạo ra bởi agent.
Mỗi học phần được index riêng thành các chunk có metadata phong phú,
cho phép Q&A chính xác theo học phần, CLO, buổi học, phương thức đánh giá.

Hỗ trợ hai vai trò:
  GV (giảng viên) — trả về câu trả lời kỹ thuật + căn cứ OBE
  SV (sinh viên)  — trả về câu trả lời dễ hiểu + gợi ý học tập
"""

import json
import time
from typing import Optional, List, Dict, Any, Tuple
from utils.logger import get_logger

logger = get_logger("rag.dcct_store")

# ── In-memory ĐCCT store (course_key → list of chunks) ────────────────────────
# Không cần vector store thứ hai; dùng simple BM25-style keyword overlap
# kết hợp với metadata filtering để retrieve.
# Đủ cho use-case Q&A trong 1 học phần (vài trăm chunk).
_dcct_knowledge: Dict[str, List[Dict]] = {}


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def index_dcct(course_code: str, dcct_state: Dict[str, Any]) -> int:
    """
    Index toàn bộ ĐCCT của một học phần vào knowledge base.

    Args:
        course_code: Mã học phần (key chính)
        dcct_state : DCCTState sau khi agent hoàn thành

    Returns:
        Số chunk được index
    """
    chunks = _build_dcct_chunks(course_code, dcct_state)
    _dcct_knowledge[course_code] = chunks
    logger.info(f"[DCCTStore] Indexed {len(chunks)} chunks cho {course_code}")
    return len(chunks)


def get_indexed_courses() -> List[str]:
    """Trả về danh sách học phần đã được index."""
    return list(_dcct_knowledge.keys())


def retrieve_for_question(
    course_code: str,
    question: str,
    role: str = "sv",
    top_k: int = 6,
) -> Tuple[List[Dict], str]:
    """
    Retrieve các chunk liên quan đến câu hỏi.

    Args:
        course_code: Mã học phần
        question   : Câu hỏi của người dùng
        role       : "gv" hoặc "sv"
        top_k      : Số chunk trả về

    Returns:
        (chunks, warning_message)
        chunks: list of {"section", "content", "metadata", "score"}
    """
    if course_code not in _dcct_knowledge:
        return [], f"Học phần '{course_code}' chưa được index. Vui lòng tạo ĐCCT trước."

    all_chunks = _dcct_knowledge[course_code]
    scored     = _score_chunks(question, all_chunks)
    top        = sorted(scored, key=lambda x: x["score"], reverse=True)[:top_k]

    return top, ""


def get_dcct_summary(course_code: str) -> Optional[Dict]:
    """Trả về metadata tổng hợp của ĐCCT (không phải chi tiết chunks)."""
    if course_code not in _dcct_knowledge:
        return None
    chunks = _dcct_knowledge[course_code]
    meta_chunk = next((c for c in chunks if c["section"] == "overview"), None)
    return meta_chunk["metadata"] if meta_chunk else None


def export_dcct_json(course_code: str) -> Optional[str]:
    """Xuất toàn bộ knowledge base của học phần dưới dạng JSON string."""
    if course_code not in _dcct_knowledge:
        return None
    return json.dumps(_dcct_knowledge[course_code], ensure_ascii=False, indent=2)


def load_dcct_json(course_code: str, json_str: str) -> int:
    """Load ĐCCT knowledge base từ JSON string đã lưu trước đó."""
    chunks = json.loads(json_str)
    _dcct_knowledge[course_code] = chunks
    logger.info(f"[DCCTStore] Loaded {len(chunks)} chunks từ JSON cho {course_code}")
    return len(chunks)


# ─────────────────────────────────────────────────────────────────────────────
# Internal: Build chunks from DCCTState
# ─────────────────────────────────────────────────────────────────────────────

def _build_dcct_chunks(course_code: str, state: Dict) -> List[Dict]:
    chunks: List[Dict] = []
    ts = time.strftime("%Y-%m-%d %H:%M")

    course_name = state.get("course_name", "")
    credits     = state.get("credits", "3")
    program     = state.get("program", "GENERIC")
    clo_list    = state.get("clo_list", [])
    mapping     = state.get("mapping_matrix", [])
    plan        = state.get("teaching_plan", [])
    assessment  = state.get("assessment_plan", [])
    rubrics     = state.get("rubrics", {})
    outline     = state.get("outline_sessions") or []

    base_meta = {
        "course_code": course_code,
        "course_name": course_name,
        "credits":     credits,
        "program":     program,
        "indexed_at":  ts,
    }

    # ── 1. Overview ───────────────────────────────────────────────────────────
    chunks.append({
        "section":  "overview",
        "content":  (
            f"Học phần: {course_code} - {course_name}\n"
            f"Tín chỉ: {credits} | Chương trình: {program}\n"
            f"Số CLO: {len(clo_list)} | Số buổi học: {len(plan)} | "
            f"Cấu phần đánh giá: {len(assessment)}\n"
            f"Mô tả: {state.get('summary', '')}"
        ),
        "keywords": [course_code, course_name, "tổng quan", "giới thiệu", "mục tiêu"],
        "metadata": {**base_meta, "type": "overview"},
    })

    # ── 2. CLO list ──────────────────────────────────────────────────────────
    for clo in clo_list:
        code = clo.get("code", "")
        desc = clo.get("description", "")
        bloom = clo.get("bloom_level_name", "")
        pi_codes = clo.get("pi_codes", [])
        source_sessions = clo.get("source_sessions", [])
        chunks.append({
            "section": "clo",
            "content": (
                f"{code}: {desc}\n"
                f"Bloom: {bloom} | Động từ: {clo.get('bloom_verb', '')}\n"
                f"PI liên quan: {', '.join(pi_codes) if pi_codes else 'Chưa xác định'}\n"
                f"Mức IRMA: {clo.get('mapping_level', '')}\n"
                + (f"Gắn với buổi: {source_sessions}" if source_sessions else "")
            ),
            "keywords": [
                code, "clo", "chuẩn đầu ra", "bloom", bloom.lower(),
                clo.get("bloom_verb", ""), *pi_codes,
            ],
            "metadata": {**base_meta, "type": "clo", "clo_code": code},
        })

    # ── 3. CLO-PLO Mapping ───────────────────────────────────────────────────
    if mapping:
        mapping_lines = []
        for m in mapping:
            mapping_lines.append(
                f"{m.get('clo_code','')}: PI {m.get('pi_code','')} → "
                f"PLO {m.get('plo_code','')} (mức {m.get('level','')})"
            )
        chunks.append({
            "section":  "mapping",
            "content":  "Ma trận CLO-PI-PLO:\n" + "\n".join(mapping_lines),
            "keywords": ["mapping", "ánh xạ", "plo", "pi", "ma trận", "clo-plo"],
            "metadata": {**base_meta, "type": "mapping"},
        })

    # ── 4. Teaching Plan sessions ────────────────────────────────────────────
    for session in plan:
        no      = session.get("no", "?")
        content = session.get("content", "")
        details = session.get("details", "")
        clos    = session.get("clo_codes", [])
        stype   = session.get("type", "LT")
        irma    = session.get("irma_level", "")
        act     = session.get("activities", "")
        week    = session.get("week", "?")
        chunks.append({
            "section": "teaching_plan",
            "content": (
                f"Buổi {no} (Tuần {week}, {stype}): {content}\n"
                f"Nội dung chi tiết: {details}\n"
                f"CLO: {', '.join(clos)} | Mức IRMA: {irma} | Hình thức: {act}\n"
                + (f"Đánh giá: {session.get('assessment','')}" if session.get("assessment") else "")
            ),
            "keywords": [
                f"buổi {no}", f"tuần {week}", stype.lower(), content.lower()[:40],
                *clos, irma, act.lower(), "kế hoạch", "lịch học",
            ],
            "metadata": {
                **base_meta, "type": "teaching_plan",
                "session_no": no, "week": week, "session_type": stype,
                "clo_codes": clos,
            },
        })

    # ── 5. Assessment plan ───────────────────────────────────────────────────
    for comp in assessment:
        code   = comp.get("code", "")
        name   = comp.get("name", "")
        weight = comp.get("weight", 0)
        clos   = comp.get("clo_mapping", [])
        chunks.append({
            "section": "assessment",
            "content": (
                f"Cấu phần đánh giá: {code} - {name}\n"
                f"Trọng số: {weight*100:.0f}%\n"
                f"CLO được đánh giá: {', '.join(clos)}\n"
                f"Rubric: {json.dumps(comp.get('rubric', {}), ensure_ascii=False)[:300]}"
            ),
            "keywords": [
                code, name, "đánh giá", "trọng số", "kiểm tra", "thi",
                f"{weight*100:.0f}%", *clos, "rubric",
            ],
            "metadata": {
                **base_meta, "type": "assessment",
                "component_code": code, "weight": weight,
            },
        })

    # ── 6. Rubrics (chi tiết) ─────────────────────────────────────────────────
    for clo_code, rubric in rubrics.items():
        if not rubric:
            continue
        rubric_text = json.dumps(rubric, ensure_ascii=False, indent=2)[:600]
        chunks.append({
            "section": "rubric",
            "content": f"Rubric cho {clo_code}:\n{rubric_text}",
            "keywords": [clo_code, "rubric", "tiêu chí", "đánh giá", "mức độ"],
            "metadata": {**base_meta, "type": "rubric", "clo_code": clo_code},
        })

    # ── 7. Outline sessions (GV's original) ─────────────────────────────────
    if outline:
        outline_text = "\n".join(
            f"Buổi {s.get('no','?')}: {s.get('topic','')} "
            f"({s.get('session_type','LT')}, {s.get('estimated_periods',1)} tiết)"
            for s in outline
        )
        chunks.append({
            "section":  "outline",
            "content":  f"Sườn buổi học (do GV cung cấp):\n{outline_text}",
            "keywords": ["sườn", "outline", "kế hoạch gốc", "buổi học"],
            "metadata": {**base_meta, "type": "outline"},
        })

    return chunks


# ─────────────────────────────────────────────────────────────────────────────
# Internal: Simple keyword-overlap scoring (no vector needed for 1 course)
# ─────────────────────────────────────────────────────────────────────────────

_SECTION_PRIORITY = {
    "clo":           1.5,
    "teaching_plan": 1.3,
    "assessment":    1.3,
    "mapping":       1.1,
    "rubric":        1.0,
    "outline":       0.9,
    "overview":      0.8,
}

# Vietnamese stop-words (rút gọn)
_STOP = {
    "là", "và", "của", "cho", "trong", "với", "có", "được", "các", "một",
    "những", "theo", "về", "từ", "đến", "tại", "sẽ", "đã", "đang",
    "không", "khi", "nếu", "thì", "mà", "hay", "hoặc",
}


def _tokenize(text: str) -> List[str]:
    import re
    tokens = re.split(r"[\s,.:;()/|]+", text.lower())
    return [t for t in tokens if t and t not in _STOP and len(t) > 1]


def _score_chunks(question: str, chunks: List[Dict]) -> List[Dict]:
    q_tokens = set(_tokenize(question))
    scored = []
    for chunk in chunks:
        kw_tokens  = set(t.lower() for t in chunk.get("keywords", []))
        cnt_tokens = set(_tokenize(chunk.get("content", "")))
        all_tokens = kw_tokens | cnt_tokens

        overlap = len(q_tokens & all_tokens)
        kw_hit  = len(q_tokens & kw_tokens)  # bonus for keyword hit

        priority = _SECTION_PRIORITY.get(chunk.get("section", ""), 1.0)
        raw_score = (overlap * 1.0 + kw_hit * 0.5) * priority

        scored.append({**chunk, "score": raw_score})
    return scored

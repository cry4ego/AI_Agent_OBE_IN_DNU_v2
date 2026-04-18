"""
Understand Agent - Phân tích học phần và sinh CLO theo Bloom Taxonomy.

Hai chế độ:
  REVERSE (outline_provided=True):  sườn GV → phân tích → sinh CLO ngược
  FORWARD (outline_provided=False): summary → sinh CLO xuôi
"""

import json
from typing import Dict, Any, List
from utils.logger import get_logger
from utils.llm_helper import call_llm_json_async, extract_json_from_response
from utils.obe_utils import get_bloom_level
from utils.outline_parser import parse_outline, is_raw_text_fallback
from prompts.understand_prompt import (
    get_understand_system_prompt,
    build_understand_user_prompt,
)

logger = get_logger("agents.understand")


async def understand_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phân tích thông tin học phần và sinh CLO.

    Input state:
        course_code, course_name, credits, summary, outline, program,
        outline_provided, human_feedback
    Output state:
        extracted_info, clo_list, outline_sessions, session_clo_map,
        outline_provided, current_step="understand_done"
    """
    course_code    = state.get("course_code", "")
    course_name    = state.get("course_name", "")
    credits        = state.get("credits", "3")
    summary        = state.get("summary", "")
    outline_raw    = state.get("outline") or ""
    program        = state.get("program")
    human_feedback = state.get("human_feedback")

    # ── Xác định luồng (REVERSE hay FORWARD) ──────────────────────────────────
    outline_provided = bool(outline_raw and outline_raw.strip())

    # Parse outline (nếu có)
    parse_result      = {"sessions": [], "parse_mode": None, "warnings": []}
    outline_sessions  = []
    parse_mode        = None
    parse_warnings    = []

    if outline_provided:
        parse_result   = parse_outline(outline_raw)
        outline_sessions = parse_result["sessions"]
        parse_mode     = parse_result["parse_mode"]
        parse_warnings = parse_result["warnings"]

        logger.info(
            f"[Understand] Chế độ REVERSE-MAPPING | parse_mode={parse_mode} "
            f"| {len(outline_sessions)} buổi | cảnh báo={len(parse_warnings)}"
        )
        for w in parse_warnings:
            logger.warning(f"[Understand/Parser] {w}")
    else:
        logger.info(f"[Understand] Chế độ FORWARD-GENERATION (không có outline)")

    # ── Gọi LLM ───────────────────────────────────────────────────────────────
    system_prompt = get_understand_system_prompt(outline_provided)
    user_prompt   = build_understand_user_prompt(
        course_code      = course_code,
        course_name      = course_name,
        credits          = credits,
        summary          = summary,
        outline_provided = outline_provided,
        outline_sessions = outline_sessions,
        outline_raw      = outline_raw,
        parse_mode       = parse_mode,
        parse_warnings   = parse_warnings,
        program          = program,
        human_feedback   = human_feedback,
    )

    warnings_out = list(state.get("warnings", []))
    warnings_out.extend([f"[Parser] {w}" for w in parse_warnings])

    try:
        raw_response = await call_llm_json_async(
            "understand", system_prompt, user_prompt
        )
        json_str = extract_json_from_response(raw_response)
        result   = json.loads(json_str)

        extracted_info = result.get("extracted_info", {})
        clo_raw_list   = result.get("clo_list", [])

        # Nếu REVERSE: LLM trả về outline_sessions mới (có thể giàu hơn parsed)
        # Ưu tiên output LLM nếu không phải raw_text và có dữ liệu thực
        llm_outline_sessions = result.get("outline_sessions", [])
        if outline_provided:
            if (
                llm_outline_sessions
                and not is_raw_text_fallback(llm_outline_sessions)
                and not is_raw_text_fallback(outline_sessions)
            ):
                # LLM đã enrich, dùng version của LLM (vẫn giữ topic gốc)
                final_outline_sessions = llm_outline_sessions
            else:
                # Giữ parsed version — an toàn hơn
                final_outline_sessions = outline_sessions
        else:
            final_outline_sessions = []

        # session_clo_map — chỉ có nghĩa khi REVERSE
        session_clo_map = result.get("session_clo_map", {}) if outline_provided else {}

        # Chuẩn hóa CLO
        clo_list = _normalize_clo_list(clo_raw_list)

        logger.info(
            f"[Understand] Hoàn thành: {len(clo_list)} CLO, "
            f"outline_provided={outline_provided}, "
            f"sessions={len(final_outline_sessions)}, "
            f"session_clo_map={len(session_clo_map)} entries"
        )

        return {
            "extracted_info":    extracted_info,
            "clo_list":          clo_list,
            "outline_provided":  outline_provided,
            "outline_sessions":  final_outline_sessions,
            "session_clo_map":   session_clo_map,
            "current_step":      "understand_done",
            "warnings":          warnings_out,
            "errors":            [],
        }

    except json.JSONDecodeError as e:
        logger.error(f"[Understand] Lỗi parse JSON: {e}")
        return {
            "outline_provided": outline_provided,
            "outline_sessions": outline_sessions,
            "session_clo_map":  {},
            "current_step":     "understand_done",
            "warnings":         warnings_out,
            "errors": state.get("errors", []) + [f"Understand: Lỗi parse JSON - {e}"],
        }
    except Exception as e:
        logger.error(f"[Understand] Lỗi: {e}")
        return {
            "outline_provided": outline_provided,
            "outline_sessions": outline_sessions,
            "session_clo_map":  {},
            "current_step":     "understand_done",
            "warnings":         warnings_out,
            "errors": state.get("errors", []) + [f"Understand: {e}"],
        }


def _normalize_clo_list(clo_raw_list: List[Dict]) -> List[Dict]:
    """Chuẩn hóa và validate danh sách CLO."""
    normalized = []

    for i, clo in enumerate(clo_raw_list):
        code        = clo.get("code") or f"CLO{i + 1}"
        description = clo.get("description", "").strip()
        bloom_verb  = clo.get("bloom_verb", "").strip()

        if not description:
            continue

        bloom_level      = clo.get("bloom_level")
        bloom_level_name = clo.get("bloom_level_name", "")
        if not bloom_level and bloom_verb:
            bloom_level, bloom_level_name = get_bloom_level(bloom_verb)

        normalized.append({
            "code":             code,
            "description":      description,
            "bloom_verb":       bloom_verb,
            "bloom_level":      bloom_level or 2,
            "bloom_level_name": bloom_level_name or "Hiểu (Understand)",
            "source_sessions":  clo.get("source_sessions", []),   # buổi nguồn (REVERSE)
            "pi_codes":         clo.get("pi_codes", []),
            "mapping_level":    clo.get("mapping_level", ""),
        })

    return normalized


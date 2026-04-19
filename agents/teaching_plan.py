"""
Teaching Plan Agent - Xây dựng kế hoạch giảng dạy động.

Hai chế độ:
  PRESERVE (outline_provided=True):
      Dùng outline_sessions làm skeleton bất biến.
      LLM chỉ enrich (CLO, IRMA, hoạt động, đánh giá).
  GENERATE (outline_provided=False):
      LLM tự sinh lịch từ CLO list theo phân bổ tín chỉ.
"""

import json
from typing import Dict, Any, List, Optional
from utils.logger import get_logger
from utils.llm_helper import call_llm_json_async, extract_json_from_response
from utils.obe_utils import calculate_sessions
from utils.outline_parser import is_raw_text_fallback
from prompts.teaching_plan_prompt import (
    build_teaching_plan_system_prompt,
    build_teaching_plan_user_prompt,
)

logger = get_logger("agents.teaching_plan")


async def teaching_plan_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Xây dựng kế hoạch giảng dạy chi tiết từng buổi.

    Input state:
        clo_list, mapping_matrix, credits, extracted_info,
        outline_provided, outline_sessions, session_clo_map
    Output state:
        teaching_plan, current_step="teaching_plan_done"
    """
    clo_list         = state.get("clo_list", [])
    mapping_matrix   = state.get("mapping_matrix", [])
    credits          = state.get("credits", "3")
    extracted_info   = state.get("extracted_info", {})
    outline_provided = state.get("outline_provided", False)
    outline_sessions = state.get("outline_sessions") or []
    session_clo_map  = state.get("session_clo_map") or {}

    logger.info(
        f"[TeachingPlan] Chế độ={'PRESERVE' if outline_provided else 'GENERATE'} | "
        f"outline_sessions={len(outline_sessions)} | credits={credits}"
    )

    # Tính phân bổ thời gian
    lab_periods    = int(extracted_info.get("lab_periods", 0) or 0)
    theory_periods = int(extracted_info.get("theory_periods", 0) or 0)
    if theory_periods + lab_periods > 0:
        theory_ratio = theory_periods / (theory_periods + lab_periods)
    else:
        theory_ratio = 0.7

    # Nếu PRESERVE: ưu tiên tổng tiết từ outline (tổng estimated_periods)
    if outline_provided and outline_sessions and not is_raw_text_fallback(outline_sessions):
        outline_total = sum(int(s.get("estimated_periods", 1) or 1) for s in outline_sessions)
        if outline_total > 0 and abs(outline_total - int(credits) * 15) > 5:
            logger.info(
                f"[TeachingPlan] Tổng tiết outline ({outline_total}) "
                f"khác tổng tín chỉ ({int(credits)*15}) — dùng outline làm chuẩn"
            )
    session_info = calculate_sessions(credits, theory_ratio)

    # Build prompts
    system_prompt  = build_teaching_plan_system_prompt(session_info, outline_provided)
    clo_list_text  = _format_clo_list(clo_list)
    mapping_summary = _format_mapping_summary(mapping_matrix)
    course_info    = _format_course_info(state, extracted_info, session_info)

    user_prompt = build_teaching_plan_user_prompt(
        course_info      = course_info,
        clo_list_text    = clo_list_text,
        mapping_summary  = mapping_summary,
        outline_sessions = outline_sessions,
        session_clo_map  = session_clo_map,
        outline_provided = outline_provided,
    )

    try:
        raw_response = await call_llm_json_async(
            "teaching_plan", system_prompt, user_prompt
        )
        json_str = extract_json_from_response(raw_response)
        result   = json.loads(json_str)

        teaching_plan = result.get("teaching_plan", [])
        teaching_plan = _normalize_plan(teaching_plan)

        # Guard PRESERVE: kiểm tra số buổi khớp với outline
        if outline_provided and outline_sessions and not is_raw_text_fallback(outline_sessions):
            teaching_plan = _enforce_outline_skeleton(
                teaching_plan, outline_sessions, session_clo_map, clo_list
            )

        logger.info(
            f"[TeachingPlan] Hoàn thành: {len(teaching_plan)} buổi | "
            f"outline_preserved={outline_provided}"
        )

        return {
            "teaching_plan": teaching_plan,
            "current_step":  "teaching_plan_done",
        }

    except json.JSONDecodeError as e:
        logger.error(f"[TeachingPlan] Lỗi parse JSON: {e}")
        fallback = _generate_fallback_plan(
            clo_list, session_info, outline_sessions, session_clo_map, outline_provided
        )
        return {
            "teaching_plan": fallback,
            "current_step":  "teaching_plan_done",
            "errors": state.get("errors", []) + [f"TeachingPlan: Lỗi parse JSON - {e}"],
        }
    except Exception as e:
        logger.error(f"[TeachingPlan] Lỗi: {e}")
        fallback = _generate_fallback_plan(
            clo_list, session_info, outline_sessions, session_clo_map, outline_provided
        )
        return {
            "teaching_plan": fallback,
            "current_step":  "teaching_plan_done",
            "errors": state.get("errors", []) + [f"TeachingPlan: {e}"],
        }


# ─────────────────────────────────────────────────────────────────────────────
# Guard: Preserve outline skeleton
# ─────────────────────────────────────────────────────────────────────────────

def _enforce_outline_skeleton(
    llm_plan: List[Dict],
    outline_sessions: List[Dict],
    session_clo_map: Dict[str, List[str]],
    clo_list: List[Dict],
) -> List[Dict]:
    """
    Đảm bảo teaching_plan khớp với outline GV.
    Nếu LLM thêm/bớt/đổi thứ tự buổi → reset về skeleton outline, giữ enrich từ LLM nếu có.
    """
    outline_count = len(outline_sessions)
    llm_count     = len(llm_plan)

    if llm_count != outline_count:
        logger.warning(
            f"[TeachingPlan/Guard] LLM tạo {llm_count} buổi, outline có {outline_count} buổi — "
            f"áp dụng outline skeleton."
        )

    # Build lookup LLM plan theo no
    llm_by_no = {s.get("no", i + 1): s for i, s in enumerate(llm_plan)}

    corrected = []
    cumulative_periods = 0
    for os_item in outline_sessions:
        no     = os_item["no"]
        topic  = os_item["topic"]
        periods = int(os_item.get("estimated_periods", 1) or 1)
        stype  = os_item.get("session_type", "LT")
        subs   = os_item.get("subtopics", [])

        # Lấy enrich từ LLM nếu có (match theo no)
        llm_s = llm_by_no.get(no, {})

        # week tính theo tích lũy tiết (3 tiết/tuần)
        week = max(1, (cumulative_periods // 3) + 1)
        cumulative_periods += periods

        # CLO từ session_clo_map (ưu tiên); fallback lấy từ LLM
        clos = session_clo_map.get(str(no)) or llm_s.get("clo_codes", [])
        if not clos and clo_list:
            clos = [clo_list[no % len(clo_list)]["code"]]

        corrected.append({
            "no":               no,
            "week":             llm_s.get("week", week),
            "type":             stype,
            "content":          topic,                          # NGUYÊN VĂN GV
            "details":          llm_s.get("details") or ("; ".join(subs) if subs else ""),
            "clo_codes":        clos,
            "irma_level":       llm_s.get("irma_level", "R"),
            "activities":       llm_s.get("activities", "Lecture" if stype == "LT" else "Lab"),
            "assessment":       llm_s.get("assessment", ""),
            "duration_periods": periods,
        })

    return corrected


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _format_clo_list(clo_list: List[Dict]) -> str:
    lines = []
    for clo in clo_list:
        pi_str = ", ".join(clo.get("pi_codes", [])) or "N/A"
        src    = clo.get("source_sessions", [])
        src_str = f" [từ buổi: {src}]" if src else ""
        lines.append(
            f"{clo['code']} (IRMA: {clo.get('mapping_level', 'R')}, "
            f"Bloom: {clo.get('bloom_level', 2)}){src_str}: {clo['description']}\n"
            f"  → PI: {pi_str}"
        )
    return "\n".join(lines)


def _format_mapping_summary(mapping_matrix: List[Dict]) -> str:
    if not mapping_matrix:
        return "Chưa có mapping"
    summary: Dict[str, List[str]] = {}
    for m in mapping_matrix:
        clo = m.get("clo_code", "")
        plo = m.get("plo_code", "")
        if clo not in summary:
            summary[clo] = []
        if plo not in summary[clo]:
            summary[clo].append(plo)
    return "\n".join([f"{clo} → {', '.join(plos)}" for clo, plos in summary.items()])


def _format_course_info(state: Dict, extracted_info: Dict, session_info: Dict) -> str:
    return (
        f"Học phần: {state.get('course_code', '')} - {state.get('course_name', '')}\n"
        f"Số tín chỉ: {session_info['credits']}\n"
        f"Tổng tiết: {session_info['total_periods']} "
        f"(LT: {session_info['theory_periods']}, TH: {session_info['lab_periods']})"
    )


def _normalize_plan(plan: List[Dict]) -> List[Dict]:
    normalized = []
    for i, session in enumerate(plan):
        normalized.append({
            "no":               session.get("no", i + 1),
            "week":             session.get("week", (i // 3) + 1),
            "type":             session.get("type", "LT"),
            "content":          session.get("content", f"Buổi {i + 1}"),
            "details":          session.get("details", ""),
            "clo_codes":        session.get("clo_codes", []),
            "irma_level":       session.get("irma_level", "R"),
            "activities":       session.get("activities", "Lecture"),
            "assessment":       session.get("assessment", ""),
            "duration_periods": session.get("duration_periods", 1),
        })
    return normalized


def _generate_fallback_plan(
    clo_list: List[Dict],
    session_info: Dict,
    outline_sessions: List[Dict],
    session_clo_map: Dict[str, List[str]],
    outline_provided: bool,
) -> List[Dict]:
    """Sinh kế hoạch cơ bản khi LLM fail."""

    # PRESERVE fallback: dùng outline skeleton
    if outline_provided and outline_sessions and not is_raw_text_fallback(outline_sessions):
        logger.info("[TeachingPlan/Fallback] Dùng outline skeleton làm fallback")
        plan = []
        for i, os_item in enumerate(outline_sessions):
            no    = os_item["no"]
            clos  = session_clo_map.get(str(no), [])
            if not clos and clo_list:
                clos = [clo_list[i % len(clo_list)]["code"]]
            plan.append({
                "no":               no,
                "week":             (i // 3) + 1,
                "type":             os_item.get("session_type", "LT"),
                "content":          os_item["topic"],
                "details":          "; ".join(os_item.get("subtopics", [])),
                "clo_codes":        clos,
                "irma_level":       "I" if i < 2 else ("M" if i > len(outline_sessions) - 3 else "R"),
                "activities":       "Lab" if os_item.get("session_type") == "TH" else "Lecture",
                "assessment":       "",
                "duration_periods": os_item.get("estimated_periods", 1),
            })
        return plan

    # GENERATE fallback: sinh từ CLO list
    logger.info("[TeachingPlan/Fallback] Sinh kế hoạch cơ bản từ CLO list")
    plan = []
    theory = session_info.get("theory_periods", 30)
    clo_codes = [c["code"] for c in clo_list]
    clo_count = max(len(clo_codes), 1)
    per_clo   = max(1, theory // clo_count)

    session_no = 1
    plan.append({
        "no": session_no, "week": 1, "type": "LT",
        "content": "Giới thiệu học phần, tổng quan nội dung",
        "details": "Giới thiệu mục tiêu, yêu cầu và kế hoạch học phần",
        "clo_codes": clo_codes[:2] if clo_codes else [],
        "irma_level": "I", "activities": "Lecture",
        "assessment": "", "duration_periods": 1,
    })
    session_no += 1

    for idx, clo_code in enumerate(clo_codes):
        for _ in range(per_clo):
            irma = "I" if idx == 0 else ("M" if idx == clo_count - 1 else "R")
            plan.append({
                "no": session_no, "week": (session_no // 3) + 1, "type": "LT",
                "content": f"Nội dung {clo_code}",
                "details": "",
                "clo_codes": [clo_code],
                "irma_level": irma, "activities": "Lecture",
                "assessment": "", "duration_periods": 1,
            })
            session_no += 1

    plan.append({
        "no": session_no, "week": (session_no // 3) + 1, "type": "LT",
        "content": "Ôn tập và tổng kết học phần",
        "details": "Ôn tập toàn bộ nội dung, hướng dẫn thi cuối kỳ",
        "clo_codes": clo_codes, "irma_level": "A", "activities": "Review",
        "assessment": "", "duration_periods": 1,
    })

    return plan

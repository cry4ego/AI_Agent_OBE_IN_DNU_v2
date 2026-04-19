"""
Assessment Agent - Thiết kế hệ thống đánh giá A1/A2.1/A2.2/A3 và Rubric
"""

import json
from typing import Dict, Any, List
from utils.logger import get_logger
from utils.llm_helper import call_llm_json_async, extract_json_from_response
from utils.obe_utils import DEFAULT_ASSESSMENT_WEIGHTS
from prompts.assessment_prompt import (
    ASSESSMENT_SYSTEM_PROMPT,
    build_assessment_user_prompt,
)

logger = get_logger("agents.assessment")


async def assessment_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Thiết kế hệ thống đánh giá và rubric.
    
    Input state: clo_list, mapping_matrix, teaching_plan, extracted_info
    Output state: assessment_plan, rubrics, current_step="assessment_done"
    """
    clo_list = state.get("clo_list", [])
    mapping_matrix = state.get("mapping_matrix", [])
    extracted_info = state.get("extracted_info", {})

    logger.info(f"[Assessment] Thiết kế đánh giá cho {len(clo_list)} CLO")

    has_lab = int(extracted_info.get("lab_periods", 0) or 0) > 0
    clo_list_text = _format_clo_list(clo_list)
    mapping_summary = _format_mapping_summary(mapping_matrix, clo_list)
    course_info = (
        f"Học phần: {state.get('course_code', '')} - {state.get('course_name', '')}\n"
        f"Số tín chỉ: {state.get('credits', '3')}\n"
        f"Loại: {extracted_info.get('course_type', 'lý thuyết+thực hành')}"
    )

    user_prompt = build_assessment_user_prompt(
        course_info, clo_list_text, mapping_summary, has_lab
    )

    try:
        raw_response = await call_llm_json_async(
            "assessment", ASSESSMENT_SYSTEM_PROMPT, user_prompt
        )
        json_str = extract_json_from_response(raw_response)
        result = json.loads(json_str)

        assessment_plan = result.get("assessment_plan", [])
        rubrics = result.get("rubrics", {})
        grading_policy = result.get("grading_policy", {})

        assessment_plan = _normalize_assessment_plan(assessment_plan, clo_list)

        logger.info(
            f"[Assessment] Hoàn thành: {len(assessment_plan)} cấu phần đánh giá"
        )

        return {
            "assessment_plan": assessment_plan,
            "rubrics": rubrics,
            "current_step": "assessment_done",
        }

    except json.JSONDecodeError as e:
        logger.error(f"[Assessment] Lỗi parse JSON: {e}")
        fallback_plan = _generate_fallback_assessment(clo_list)
        return {
            "assessment_plan": fallback_plan["assessment_plan"],
            "rubrics": fallback_plan["rubrics"],
            "current_step": "assessment_done",
            "errors": state.get("errors", []) + [f"Assessment: Lỗi parse JSON - {e}"],
        }
    except Exception as e:
        logger.error(f"[Assessment] Lỗi: {e}")
        fallback_plan = _generate_fallback_assessment(clo_list)
        return {
            "assessment_plan": fallback_plan["assessment_plan"],
            "rubrics": fallback_plan["rubrics"],
            "current_step": "assessment_done",
            "errors": state.get("errors", []) + [f"Assessment: {e}"],
        }


def _format_clo_list(clo_list: List[Dict]) -> str:
    lines = []
    for clo in clo_list:
        lines.append(
            f"{clo['code']} [Bloom {clo.get('bloom_level', 2)} - "
            f"IRMA: {clo.get('mapping_level', 'R')}]: {clo['description']}"
        )
    return "\n".join(lines)


def _format_mapping_summary(mapping_matrix: List[Dict], clo_list: List[Dict]) -> str:
    if not mapping_matrix:
        return "Chưa có mapping"
    lines = []
    for clo in clo_list:
        mappings = [m for m in mapping_matrix if m.get("clo_code") == clo["code"]]
        plos = list({m.get("plo_code", "") for m in mappings})
        lines.append(f"{clo['code']} → {', '.join(plos)}")
    return "\n".join(lines)


def _normalize_assessment_plan(plan: List[Dict], clo_list: List[Dict]) -> List[Dict]:
    """Chuẩn hóa assessment plan, đảm bảo trọng số = 100%."""
    if not plan:
        return _generate_fallback_assessment(clo_list)["assessment_plan"]

    # Đảm bảo trọng số cộng thành 1.0
    total_weight = sum(float(p.get("weight", 0)) for p in plan)
    if abs(total_weight - 1.0) > 0.01 and total_weight > 0:
        for p in plan:
            p["weight"] = round(float(p.get("weight", 0)) / total_weight, 2)

    normalized = []
    for p in plan:
        normalized.append({
            "code": p.get("code", "A1"),
            "name": p.get("name", ""),
            "description": p.get("description", ""),
            "weight": float(p.get("weight", 0.1)),
            "format": p.get("format", ""),
            "frequency": p.get("frequency", ""),
            "clo_mapping": p.get("clo_mapping", []),
            "bloom_levels_assessed": p.get("bloom_levels_assessed", []),
            "duration_minutes": p.get("duration_minutes"),
        })

    return normalized


def _generate_fallback_assessment(clo_list: List[Dict]) -> Dict:
    """Tự sinh assessment cơ bản."""
    clo_codes = [c["code"] for c in clo_list]
    # CLO mức thấp (Bloom 1-2)
    low_clos = [c["code"] for c in clo_list if c.get("bloom_level", 2) <= 2]
    # CLO mức cao (Bloom 4-6)
    high_clos = [c["code"] for c in clo_list if c.get("bloom_level", 2) >= 4]

    assessment_plan = [
        {
            "code": "A1",
            "name": "Đánh giá quá trình",
            "description": "Chuyên cần, bài tập về nhà, quiz trên lớp",
            "weight": 0.10,
            "format": "Quiz online/bài tập (5 lần)",
            "frequency": "Mỗi 3 tuần 1 lần",
            "clo_mapping": clo_codes,
            "bloom_levels_assessed": [1, 2],
            "duration_minutes": None,
        },
        {
            "code": "A2.1",
            "name": "Kiểm tra giữa kỳ",
            "description": "Kiểm tra lý thuyết nửa đầu học kỳ",
            "weight": 0.20,
            "format": "Thi viết 60 phút (trắc nghiệm + tự luận)",
            "frequency": "1 lần (tuần 8)",
            "clo_mapping": low_clos or clo_codes[:len(clo_codes)//2 + 1],
            "bloom_levels_assessed": [1, 2, 3],
            "duration_minutes": 60,
        },
        {
            "code": "A2.2",
            "name": "Thực hành / Bài tập lớn",
            "description": "Dự án thực hành nhóm, báo cáo kết quả",
            "weight": 0.30,
            "format": "Bài tập lớn nhóm (2-3 người) + báo cáo",
            "frequency": "1 lần (tuần 12-13)",
            "clo_mapping": high_clos or clo_codes[len(clo_codes)//2:],
            "bloom_levels_assessed": [3, 4, 5, 6],
            "duration_minutes": None,
        },
        {
            "code": "A3",
            "name": "Thi cuối kỳ",
            "description": "Thi tổng hợp cuối học kỳ",
            "weight": 0.40,
            "format": "Thi viết 90 phút (trắc nghiệm + tự luận/thực hành)",
            "frequency": "1 lần (tuần 15)",
            "clo_mapping": clo_codes,
            "bloom_levels_assessed": [1, 2, 3, 4],
            "duration_minutes": 90,
        },
    ]

    rubrics = {
        "A2.2": {
            "criteria": [
                {
                    "criterion": "Chất lượng giải pháp kỹ thuật",
                    "weight_in_component": 0.4,
                    "levels": {
                        "excellent": {"score_range": "90-100", "description": "Giải pháp sáng tạo, tối ưu, đáp ứng đầy đủ yêu cầu"},
                        "good": {"score_range": "70-89", "description": "Giải pháp đúng, hoạt động tốt, có một số điểm cần cải thiện nhỏ"},
                        "pass": {"score_range": "50-69", "description": "Giải pháp cơ bản đúng, còn một số lỗi nhỏ"},
                        "fail": {"score_range": "0-49", "description": "Giải pháp sai hoặc không hoàn chỉnh"},
                    },
                },
                {
                    "criterion": "Báo cáo và trình bày",
                    "weight_in_component": 0.3,
                    "levels": {
                        "excellent": {"score_range": "90-100", "description": "Báo cáo rõ ràng, đầy đủ, trình bày chuyên nghiệp"},
                        "good": {"score_range": "70-89", "description": "Báo cáo khá đầy đủ, trình bày tốt"},
                        "pass": {"score_range": "50-69", "description": "Báo cáo đủ nội dung cơ bản"},
                        "fail": {"score_range": "0-49", "description": "Báo cáo thiếu nhiều nội dung quan trọng"},
                    },
                },
                {
                    "criterion": "Làm việc nhóm và tiến độ",
                    "weight_in_component": 0.3,
                    "levels": {
                        "excellent": {"score_range": "90-100", "description": "Phân công rõ ràng, tiến độ đúng hạn, cộng tác tốt"},
                        "good": {"score_range": "70-89", "description": "Tiến độ tốt, có sự phân công hợp lý"},
                        "pass": {"score_range": "50-69", "description": "Hoàn thành đúng hạn với hỗ trợ từ giảng viên"},
                        "fail": {"score_range": "0-49", "description": "Không hoàn thành đúng hạn hoặc thiếu sự cộng tác"},
                    },
                },
            ]
        }
    }

    return {"assessment_plan": assessment_plan, "rubrics": rubrics}

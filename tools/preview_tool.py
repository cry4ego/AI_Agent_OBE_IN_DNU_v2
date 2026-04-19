"""
Preview Tool - Hiển thị preview DCCT cho giảng viên xem và xác nhận
"""

import json
from typing import Dict, Any
from utils.logger import get_logger

logger = get_logger("tools.preview")


async def preview_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tạo preview DCCT để giảng viên xem và phản hồi.
    
    Input state: final_dcct_data hoặc dữ liệu riêng lẻ
    Output state: preview_data, needs_human_input=True
    """
    logger.info("[Preview] Tạo preview DCCT")

    final_dcct = state.get("final_dcct_data") or _build_preview_from_state(state)
    preview_data = _format_preview(final_dcct, state)

    # In preview ra console (trong thực tế sẽ hiển thị qua Streamlit)
    _print_preview_to_console(preview_data)

    return {
        "preview_data": preview_data,
        "needs_human_input": True,
        "current_step": "preview_done",
    }


def _build_preview_from_state(state: Dict) -> Dict:
    """Xây dựng preview từ state nếu final_dcct_data chưa có."""
    return {
        "course_info": {
            "code": state.get("course_code", ""),
            "name": state.get("course_name", ""),
            "credits": state.get("credits", "3"),
            **state.get("extracted_info", {}),
        },
        "clo_list": state.get("clo_list", []),
        "mapping_matrix": state.get("mapping_matrix", []),
        "teaching_plan": state.get("teaching_plan", []),
        "assessment_plan": state.get("assessment_plan", []),
        "rubrics": state.get("rubrics", {}),
        "confidence_score": state.get("confidence_score", 0),
    }


def _format_preview(dcct_data: Dict, state: Dict) -> Dict:
    """Format dữ liệu DCCT thành dạng preview thân thiện."""
    clo_list = dcct_data.get("clo_list", [])
    assessment_plan = dcct_data.get("assessment_plan", [])
    teaching_plan = dcct_data.get("teaching_plan", [])
    mapping_matrix = dcct_data.get("mapping_matrix", [])
    course_info = dcct_data.get("course_info", {})

    # Thống kê
    clo_bloom_dist = {}
    for clo in clo_list:
        bl = clo.get("bloom_level_name", "N/A")
        clo_bloom_dist[bl] = clo_bloom_dist.get(bl, 0) + 1

    plo_coverage = {}
    for m in mapping_matrix:
        plo = m.get("plo_code", "")
        if plo:
            plo_coverage[plo] = plo_coverage.get(plo, 0) + 1

    total_weight = sum(float(a.get("weight", 0)) for a in assessment_plan)

    return {
        "course_summary": {
            "code": course_info.get("code", state.get("course_code", "")),
            "name": course_info.get("name", state.get("course_name", "")),
            "credits": course_info.get("credits", state.get("credits", "3")),
            "type": course_info.get("course_type", "N/A"),
        },
        "clo_preview": [
            {
                "code": c["code"],
                "description": c["description"],
                "bloom": c.get("bloom_level_name", "N/A"),
                "pi_codes": c.get("pi_codes", []),
                "irma": c.get("mapping_level", "N/A"),
            }
            for c in clo_list
        ],
        "teaching_plan_summary": {
            "total_sessions": len(teaching_plan),
            "theory_sessions": sum(1 for s in teaching_plan if s.get("type") == "LT"),
            "lab_sessions": sum(1 for s in teaching_plan if s.get("type") == "TH"),
        },
        "assessment_summary": [
            {
                "code": a["code"],
                "name": a["name"],
                "weight_percent": f"{a.get('weight', 0) * 100:.0f}%",
                "clo_count": len(a.get("clo_mapping", [])),
            }
            for a in assessment_plan
        ],
        "plo_coverage": plo_coverage,
        "bloom_distribution": clo_bloom_dist,
        "confidence_score": dcct_data.get("confidence_score", state.get("confidence_score", 0)),
        "total_assessment_weight": round(total_weight * 100),
        "issues": state.get("errors", []) + state.get("warnings", []),
    }


def _print_preview_to_console(preview: Dict):
    """In preview ra console (fallback khi không có Streamlit UI)."""
    print("\n" + "=" * 60)
    print("📋 PREVIEW ĐỀ CƯƠNG CHI TIẾT HỌC PHẦN (DCCT)")
    print("=" * 60)

    course = preview.get("course_summary", {})
    print(f"\n📚 HỌC PHẦN: {course.get('code', '')} - {course.get('name', '')}")
    print(f"   Số tín chỉ: {course.get('credits', 'N/A')} | Loại: {course.get('type', 'N/A')}")

    print(f"\n🎯 CHUẨN ĐẦU RA HỌC PHẦN (CLO): {len(preview.get('clo_preview', []))} CLO")
    for clo in preview.get("clo_preview", []):
        print(f"   {clo['code']} [{clo['bloom']} | IRMA:{clo['irma']}]: {clo['description'][:70]}...")

    plan = preview.get("teaching_plan_summary", {})
    print(f"\n📅 KẾ HOẠCH GIẢNG DẠY:")
    print(f"   Tổng: {plan.get('total_sessions', 0)} buổi "
          f"(LT: {plan.get('theory_sessions', 0)}, TH: {plan.get('lab_sessions', 0)})")

    print(f"\n📊 HỆ THỐNG ĐÁNH GIÁ:")
    for a in preview.get("assessment_summary", []):
        print(f"   {a['code']}: {a['name']} - {a['weight_percent']} → {a['clo_count']} CLO")

    print(f"\n🎓 PLO COVERAGE: {', '.join(preview.get('plo_coverage', {}).keys())}")
    print(f"\n✨ CONFIDENCE SCORE: {preview.get('confidence_score', 0):.1f}%")
    print(f"   Trọng số đánh giá tổng: {preview.get('total_assessment_weight', 0)}%")

    issues = preview.get("issues", [])
    if issues:
        print(f"\n⚠️  ISSUES ({len(issues)}):")
        for issue in issues[:5]:
            print(f"   - {issue}")

    print("\n" + "=" * 60)

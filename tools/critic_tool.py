"""
Critic Tool - Agent phản biện độc lập, kiểm chứng output của từng agent
"""

import json
from typing import Dict, Any
from utils.logger import get_logger
from utils.llm_helper import call_llm_json_async, extract_json_from_response
from prompts.critic_prompt import build_critic_system_prompt, build_critic_user_prompt

logger = get_logger("tools.critic")


async def critic_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Critic Agent kiểm tra output của bước vừa hoàn thành.
    
    Đọc current_step để biết cần review gì:
    - understand_done → review CLO
    - mapping_done → review mapping
    - teaching_plan_done → review teaching plan
    - assessment_done → review assessment
    
    Output: cập nhật critic_feedback list
    """
    current_step = state.get("current_step", "")

    # Map từ done step sang tên bước để review
    step_map = {
        "understand_done": "understand",
        "mapping_done": "mapping",
        "teaching_plan_done": "teaching_plan",
        "assessment_done": "assessment",
    }

    step_name = step_map.get(current_step)
    if not step_name:
        logger.warning(f"[Critic] Không xác định được bước cần review: {current_step}")
        return {}

    logger.info(f"[Critic] Đang review bước: {step_name}")

    # Lấy output cần review
    output_json, context = _extract_step_output(state, step_name)

    # Truyền extra context cho system prompt (e.g. outline_provided)
    extra_ctx = {}
    if step_name == "teaching_plan":
        extra_ctx["outline_provided"] = state.get("outline_provided", False)

    system_prompt = build_critic_system_prompt(step_name, extra_ctx)
    user_prompt = build_critic_user_prompt(step_name, output_json, context)

    try:
        raw_response = await call_llm_json_async(
            "critic", system_prompt, user_prompt
        )
        json_str = extract_json_from_response(raw_response)
        feedback = json.loads(json_str)

        # Đảm bảo có đủ fields
        feedback.setdefault("step", step_name)
        feedback.setdefault("passed", True)
        feedback.setdefault("score", 70)
        feedback.setdefault("critical_issues", [])
        feedback.setdefault("minor_issues", [])
        feedback.setdefault("suggestions", [])
        feedback.setdefault("summary", "")

        passed = feedback.get("passed", True)
        score = feedback.get("score", 70)
        logger.info(
            f"[Critic] {step_name}: {'✓ PASS' if passed else '✗ FAIL'} "
            f"(score={score})"
        )
        if feedback.get("critical_issues"):
            logger.warning(f"[Critic] Critical issues: {feedback['critical_issues']}")

        # Append feedback vào list hiện có
        existing_feedback = list(state.get("critic_feedback", []))
        existing_feedback.append(feedback)

        return {"critic_feedback": existing_feedback}

    except json.JSONDecodeError as e:
        logger.error(f"[Critic] Lỗi parse JSON: {e}")
        # Fallback: pass if no obvious issues
        feedback = _basic_critic(state, step_name)
        existing_feedback = list(state.get("critic_feedback", []))
        existing_feedback.append(feedback)
        return {"critic_feedback": existing_feedback}

    except Exception as e:
        logger.error(f"[Critic] Lỗi: {e}")
        feedback = _basic_critic(state, step_name)
        existing_feedback = list(state.get("critic_feedback", []))
        existing_feedback.append(feedback)
        return {"critic_feedback": existing_feedback}


def _extract_step_output(state: Dict, step_name: str) -> tuple:
    """Trích xuất output và context cho từng bước."""
    if step_name == "understand":
        output = {
            "clo_count": len(state.get("clo_list", [])),
            "clo_list": state.get("clo_list", []),
            "extracted_info": state.get("extracted_info", {}),
        }
        context = f"Học phần: {state.get('course_code', '')} - {state.get('course_name', '')}"

    elif step_name == "mapping":
        output = {
            "mapping_matrix": state.get("mapping_matrix", []),
            "clo_with_pis": [
                {"code": c["code"], "pi_codes": c.get("pi_codes", []),
                 "mapping_level": c.get("mapping_level", "")}
                for c in state.get("clo_list", [])
            ],
        }
        context = f"{len(state.get('clo_list', []))} CLO cần được ánh xạ"

    elif step_name == "teaching_plan":
        plan             = state.get("teaching_plan", [])
        outline_provided = state.get("outline_provided", False)
        outline_sessions = state.get("outline_sessions") or []

        output = {
            "total_sessions":      len(plan),
            "teaching_plan_sample": plan[:5],
            "clo_coverage":        _count_clo_coverage(plan),
            "outline_provided":    outline_provided,
        }

        if outline_provided and outline_sessions:
            # Thêm so sánh topic để Critic kiểm tra preserve
            outline_topics  = [s.get("topic", "") for s in outline_sessions]
            plan_topics     = [s.get("content", "") for s in plan]
            outline_mismatch = _check_outline_preservation(outline_topics, plan_topics)
            output["outline_session_count"]     = len(outline_sessions)
            output["plan_session_count"]         = len(plan)
            output["outline_topics_sample"]      = outline_topics[:5]
            output["plan_topics_sample"]          = plan_topics[:5]
            output["outline_mismatch_detected"]  = bool(outline_mismatch)
            output["mismatch_details"]            = outline_mismatch[:3]  # first 3 diffs

        context = (
            f"Học phần {state.get('credits', '3')} tín chỉ, "
            f"{len(state.get('clo_list', []))} CLO"
            + (
                f" | CHẾ ĐỘ: PRESERVE (GV đã cung cấp {len(outline_sessions)} buổi)"
                if outline_provided else " | CHẾ ĐỘ: GENERATE"
            )
        )

    elif step_name == "assessment":
        assessment_plan = state.get("assessment_plan", [])
        total_weight = sum(float(a.get("weight", 0)) for a in assessment_plan)
        output = {
            "assessment_plan": assessment_plan,
            "total_weight": round(total_weight, 2),
            "rubrics_available": list(state.get("rubrics", {}).keys()),
        }
        context = f"{len(state.get('clo_list', []))} CLO cần được đánh giá"

    else:
        output = {}
        context = ""

    return json.dumps(output, ensure_ascii=False, indent=2), context


def _check_outline_preservation(
    outline_topics: list, plan_topics: list
) -> list:
    """
    So sánh topic GV với topic trong teaching_plan.
    Trả về list các chênh lệch (nếu có).
    """
    mismatches = []
    for i, (orig, gen) in enumerate(zip(outline_topics, plan_topics)):
        # Normalize: lower + strip để tránh lỗi format nhỏ
        orig_n = orig.strip().lower()
        gen_n  = gen.strip().lower()
        if orig_n and gen_n and orig_n != gen_n:
            # Cho phép gen là superset (có thêm chi tiết)
            if orig_n not in gen_n and gen_n not in orig_n:
                mismatches.append({
                    "session": i + 1,
                    "outline_topic": orig[:80],
                    "plan_topic":    gen[:80],
                })
    if len(outline_topics) != len(plan_topics):
        mismatches.append({
            "session": "N/A",
            "outline_topic": f"Outline có {len(outline_topics)} buổi",
            "plan_topic":    f"Teaching plan có {len(plan_topics)} buổi",
        })
    return mismatches


def _count_clo_coverage(teaching_plan) -> Dict:
    """Đếm số buổi mỗi CLO được dạy."""
    coverage = {}
    for session in teaching_plan:
        for clo in session.get("clo_codes", []):
            coverage[clo] = coverage.get(clo, 0) + 1
    return coverage


def _basic_critic(state: Dict, step_name: str) -> Dict:
    """Critic cơ bản không cần LLM (fallback)."""
    issues = []
    passed = True

    if step_name == "understand":
        clo_count = len(state.get("clo_list", []))
        if clo_count < 3:
            issues.append(f"Quá ít CLO: {clo_count}")
            passed = False

    elif step_name == "mapping":
        if not state.get("mapping_matrix"):
            issues.append("Mapping matrix trống")
            passed = False

    elif step_name == "teaching_plan":
        if not state.get("teaching_plan"):
            issues.append("Kế hoạch giảng dạy trống")
            passed = False
        else:
            # Kiểm tra outline preservation (chỉ khi outline_provided=True)
            outline_provided = state.get("outline_provided", False)
            outline_sessions = state.get("outline_sessions") or []
            if outline_provided and outline_sessions:
                plan_topics    = [s.get("content", "") for s in state["teaching_plan"]]
                outline_topics = [s.get("topic", "") for s in outline_sessions]
                mismatches     = _check_outline_preservation(outline_topics, plan_topics)
                if mismatches:
                    for m in mismatches:
                        issues.append(
                            f"[Outline Guard] Buổi {m['session']}: "
                            f"GV='{m['outline_topic']}' ≠ Plan='{m['plan_topic']}'"
                        )
                    passed = False

    elif step_name == "assessment":
        assessment_plan = state.get("assessment_plan", [])
        if not assessment_plan:
            issues.append("Assessment plan trống")
            passed = False
        else:
            total = sum(float(a.get("weight", 0)) for a in assessment_plan)
            if abs(total - 1.0) > 0.05:
                issues.append(f"Trọng số không hợp lệ: {total:.2f}")
                passed = False

    return {
        "step": step_name,
        "passed": passed,
        "score": 70 if passed else 40,
        "critical_issues": issues if not passed else [],
        "minor_issues": [],
        "suggestions": [],
        "summary": f"Basic validation: {'PASS' if passed else 'FAIL'}",
    }

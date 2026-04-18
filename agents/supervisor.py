"""
Supervisor Agent - Điều phối luồng workflow OBE DCCT.

Không sử dụng LLM - chỉ logic thuần để routing.

Hai luồng dựa trên outline_provided:
  REVERSE (outline_provided=True):  sườn GV bất biến, Teaching Plan ở chế độ PRESERVE
  FORWARD (outline_provided=False): Teaching Plan tự sinh từ CLO
"""

from typing import Dict, Any
from utils.logger import get_logger

logger = get_logger("agents.supervisor")

# Thứ tự các bước trong workflow
STEP_SEQUENCE = ["understand", "mapping", "teaching_plan", "assessment", "final_validator"]

# Map từ "bước_done" sang tên bước
STEP_DONE_MAP = {
    "understand_done": "understand",
    "mapping_done": "mapping",
    "teaching_plan_done": "teaching_plan",
    "assessment_done": "assessment",
}

MAX_RETRIES = 2


def supervisor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Supervisor điều phối luồng workflow dựa trên:
    1. current_step: bước hiện tại / đã hoàn thành
    2. critic_feedback: phản hồi từ Critic sau mỗi bước
    3. retry_counts: số lần đã retry mỗi bước
    4. outline_provided: xác định luồng REVERSE hay FORWARD

    Quy tắc routing:
    - Nếu current_step là tên bước thông thường → route thẳng
    - Nếu current_step là "X_done" → kiểm tra critic_feedback → tiến hoặc retry
    """
    current         = state.get("current_step", "understand")
    retry_counts    = dict(state.get("retry_counts", {}))
    critic_feedback = state.get("critic_feedback", [])
    outline_provided = state.get("outline_provided", False)
    outline_sessions = state.get("outline_sessions") or []

    logger.info(
        f"Supervisor: current_step={current}, retries={retry_counts}, "
        f"outline_provided={outline_provided}, sessions={len(outline_sessions)}"
    )

    # Guard: outline_provided=True nhưng outline_sessions rỗng → warn
    if (
        outline_provided
        and current == "teaching_plan"
        and not outline_sessions
    ):
        logger.warning(
            "[Supervisor] outline_provided=True nhưng outline_sessions rỗng. "
            "Teaching Plan sẽ chạy ở GENERATE mode làm fallback."
        )

    # === TRƯỜNG HỢP 1: Bước thông thường (lần đầu hoặc đã được set) ===
    if current in STEP_SEQUENCE:
        mode_tag = "PRESERVE" if (outline_provided and current == "teaching_plan") else ""
        logger.info(f"Supervisor → {current} {mode_tag}")
        return {"current_step": current}

    # === TRƯỜNG HỢP 2: Bước vừa hoàn thành (X_done) ===
    if current in STEP_DONE_MAP:
        step_name = STEP_DONE_MAP[current]

        # Ghi log luồng sau khi understand xong
        if step_name == "understand":
            flow = "REVERSE-MAPPING" if outline_provided else "FORWARD-GENERATION"
            logger.info(f"[Supervisor] Luồng xác định: {flow}")

        # Tìm phản hồi critic gần nhất cho bước này
        step_feedbacks = [
            f for f in critic_feedback if f.get("step") == step_name
        ]
        last_feedback = step_feedbacks[-1] if step_feedbacks else None

        # Kiểm tra nếu critic fail
        if last_feedback and not last_feedback.get("passed", True):
            retries = retry_counts.get(step_name, 0)
            if retries < MAX_RETRIES:
                retry_counts[step_name] = retries + 1
                logger.warning(
                    f"Supervisor: Critic FAIL cho '{step_name}', "
                    f"retry lần {retries + 1}/{MAX_RETRIES}"
                )
                return {"current_step": step_name, "retry_counts": retry_counts}
            else:
                logger.warning(
                    f"Supervisor: Đã retry '{step_name}' {MAX_RETRIES} lần, "
                    f"tiến tới bước tiếp theo dù chưa đạt"
                )

        # Tiến đến bước tiếp theo
        idx = STEP_SEQUENCE.index(step_name)
        if idx + 1 < len(STEP_SEQUENCE):
            next_step = STEP_SEQUENCE[idx + 1]
            logger.info(f"Supervisor: {step_name} ✓ → {next_step}")
            return {"current_step": next_step}

    # === TRƯỜNG HỢP 3: Sau final_validator hoặc trạng thái không xác định ===
    if current == "final_validator_done" or current not in STEP_SEQUENCE + list(STEP_DONE_MAP.keys()):
        logger.warning(f"Supervisor: Trạng thái không xác định '{current}', reset về understand")
        return {"current_step": "understand"}

    return {"current_step": current}


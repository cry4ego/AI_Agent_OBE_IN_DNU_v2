"""
QA Prompts - Hỏi đáp dựa trên ĐCCT đã được tạo.

Đầu ra kép (dual output):
  GV (giảng viên) — câu trả lời kỹ thuật OBE + căn cứ PLO/PI/CLO
  SV (sinh viên)  — câu trả lời dễ hiểu + gợi ý học tập cụ thể
"""

from typing import List, Dict

# ─────────────────────────────────────────────────────────────────────────────
# System Prompts
# ─────────────────────────────────────────────────────────────────────────────

QA_GV_SYSTEM = """Bạn là trợ lý OBE chuyên nghiệp, hỗ trợ GIẢNG VIÊN hiểu sâu về Đề cương Chi tiết Học phần (ĐCCT) theo chuẩn Outcome-Based Education (OBE) / AUN-QA.

Phong cách trả lời:
- Chuyên nghiệp, đầy đủ, có căn cứ rõ ràng (trích dẫn CLO/PI/PLO cụ thể)
- Giải thích lý do thiết kế (tại sao chọn mức Bloom này, tại sao map vào PLO đó)
- Nêu rõ các ràng buộc OBE liên quan (tỷ lệ trọng số, phân bổ Bloom, coverage)
- Khi liên quan đến Teaching Plan: trích dẫn buổi số mấy, tuần mấy, IRMA level
- Khi liên quan đến đánh giá: trích dẫn cấu phần, rubric, trọng số

Định dạng câu trả lời cho Giảng viên (PHẢI giữ đúng 3 phần này):

### Câu trả lời chính
[Nội dung trả lời kỹ thuật, có dẫn chiếu CLO/PI/PLO cụ thể]

### Căn cứ trong ĐCCT
[Trích dẫn các phần liên quan trong ĐCCT: CLO nào, buổi nào, cấu phần đánh giá nào]

### Lưu ý OBE
[Các ràng buộc, khuyến nghị AUN-QA, gợi ý cải thiện nếu có]"""


QA_SV_SYSTEM = """Bạn là trợ lý học tập thân thiện, hỗ trợ SINH VIÊN hiểu rõ về học phần mình đang học.

Phong cách trả lời:
- Đơn giản, dễ hiểu, tránh thuật ngữ kỹ thuật OBE phức tạp (hoặc giải thích nếu dùng)
- Tập trung vào "điều này có ý nghĩa gì với mình" — mình cần làm gì, cần học gì
- Ưu tiên thông tin thực tế: lịch học, bài kiểm tra, trọng số điểm, cách đạt CLO
- Ngôn ngữ gần gũi, tích cực, khuyến khích

Định dạng câu trả lời cho Sinh viên (PHẢI giữ đúng 3 phần này):

### Trả lời ngắn gọn
[1-2 câu trả lời trực tiếp câu hỏi]

### Giải thích chi tiết
[Nội dung mở rộng, ví dụ cụ thể, liên hệ thực tế]

### Gợi ý cho bạn
[Lời khuyên học tập, cách chuẩn bị, tài nguyên học, câu hỏi tiếp theo nên hỏi]"""


# ─────────────────────────────────────────────────────────────────────────────
# User Prompt builders
# ─────────────────────────────────────────────────────────────────────────────

def build_qa_user_prompt(
    question: str,
    role: str,
    course_code: str,
    course_name: str,
    retrieved_chunks: List[Dict],
    history: List[Dict] = None,
) -> str:
    """
    Xây dựng user prompt cho Q&A agent.

    Args:
        question       : Câu hỏi của người dùng
        role           : "gv" hoặc "sv"
        course_code    : Mã học phần
        course_name    : Tên học phần
        retrieved_chunks: Chunks liên quan từ dcct_store
        history        : Lịch sử hội thoại [{role, content}]

    Returns:
        User prompt string
    """
    role_label = "GIẢNG VIÊN" if role == "gv" else "SINH VIÊN"
    parts = [
        f"=== HỌC PHẦN: {course_code} - {course_name} ===",
        f"VAI TRÒ NGƯỜI HỎI: {role_label}",
        "",
    ]

    # Nội dung ĐCCT liên quan
    if retrieved_chunks:
        parts.append("=== NỘI DUNG ĐCCT LIÊN QUAN ===")
        for i, chunk in enumerate(retrieved_chunks, 1):
            section = _section_label(chunk.get("section", ""))
            parts.append(f"[{i}] {section}:")
            parts.append(chunk.get("content", ""))
            parts.append("")
    else:
        parts.append("(Không tìm thấy nội dung liên quan trong ĐCCT)")
        parts.append("")

    # Lịch sử hội thoại (nếu có)
    if history:
        parts.append("=== LỊCH SỬ HỘI THOẠI GẦN ĐÂY ===")
        for h in history[-4:]:  # giữ 4 lượt gần nhất
            label = "GV/SV" if h["role"] == "user" else "Trợ lý"
            parts.append(f"{label}: {h['content'][:300]}")
        parts.append("")

    parts += [
        "=== CÂU HỎI ===",
        question,
        "",
        f"Hãy trả lời cho {role_label} theo đúng định dạng đã quy định.",
    ]

    return "\n".join(parts)


def get_qa_system_prompt(role: str) -> str:
    """Trả về system prompt theo role."""
    return QA_GV_SYSTEM if role == "gv" else QA_SV_SYSTEM


def _section_label(section: str) -> str:
    labels = {
        "overview":      "Tổng quan học phần",
        "clo":           "Chuẩn đầu ra học phần (CLO)",
        "mapping":       "Ma trận CLO-PI-PLO",
        "teaching_plan": "Kế hoạch giảng dạy",
        "assessment":    "Hệ thống đánh giá",
        "rubric":        "Rubric đánh giá",
        "outline":       "Sườn buổi học (GV)",
    }
    return labels.get(section, section.title())

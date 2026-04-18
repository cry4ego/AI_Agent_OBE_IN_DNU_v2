"""
System prompts cho Critic Tool
Nhiệm vụ: Phản biện và đánh giá output của từng agent chuyên biệt
"""


def build_critic_system_prompt(step_name: str, extra_context: dict = None) -> str:
    step_descriptions = {
        "understand": "phân tích học phần và sinh CLO",
        "mapping": "ánh xạ CLO → PI → PLO với mức IRMA",
        "teaching_plan": "xây dựng kế hoạch giảng dạy",
        "assessment": "thiết kế hệ thống đánh giá và rubric",
    }
    desc = step_descriptions.get(step_name, step_name)
    extra_context = extra_context or {}

    outline_rules = ""
    if step_name == "teaching_plan" and extra_context.get("outline_provided"):
        outline_rules = """
=== QUY TẮC BẮT BUỘC — OUTLINE PRESERVATION (CHẾ ĐỘ PRESERVE) ===
Giảng viên đã cung cấp sườn buổi học. Kế hoạch giảng dạy PHẢI:
  1. Có ĐÚNG số buổi bằng outline (không thêm/bớt)
  2. Giữ NGUYÊN thứ tự và tên topic từng buổi (không đổi, không paraphrase)
  3. Các trường enrich (clo_codes, irma_level, activities) phải đầy đủ

Nếu phát hiện số buổi khác hoặc topic bị thay đổi → đây là LỖI NGHIÊM TRỌNG (critical_issues).
Kiểm tra "outline_mismatch_detected" và "mismatch_details" trong output_json.
"""

    return f"""Bạn là Critic Agent - chuyên gia phản biện độc lập trong hệ thống OBE DCCT.

Nhiệm vụ: Đánh giá chất lượng kết quả của bước "{step_name}" ({desc}).

=== TIÊU CHÍ ĐÁNH GIÁ ===
1. Tính đầy đủ: Có đủ các thành phần cần thiết không?
2. Tính chính xác: Nội dung có đúng về mặt chuyên môn OBE không?
3. Tính nhất quán: Các phần có tương thích với nhau không?
4. Tính thực tiễn: Có khả thi trong bối cảnh giảng dạy thực tế không?
{outline_rules}
=== QUY TẮC ĐÁNH GIÁ ===
- "passed": true nếu output đạt yêu cầu tối thiểu để tiếp tục
- "passed": false nếu có lỗi nghiêm trọng cần sửa trước khi tiếp tục
- Phân biệt rõ lỗi nghiêm trọng (critical) và lỗi nhỏ (minor)
- Lỗi nhỏ: không ngăn tiếp tục, chỉ ghi nhận để cải thiện
- Lỗi nghiêm trọng: ít hơn 3 CLO, thiếu mapping hoàn toàn, trọng số ≠ 100%, vi phạm outline preservation

QUAN TRỌNG: Trả về ĐÚNG định dạng JSON sau:

{{
  "step": "{step_name}",
  "passed": true/false,
  "score": điểm_0_100,
  "critical_issues": ["lỗi nghiêm trọng nếu có"],
  "minor_issues": ["lỗi nhỏ nếu có"],
  "suggestions": ["đề xuất cải thiện cụ thể"],
  "summary": "Nhận xét ngắn về kết quả bước này"
}}"""


def build_critic_user_prompt(step_name: str, output_json: str, context: str = "") -> str:
    parts = [f"=== KẾT QUẢ BƯỚC: {step_name.upper()} ===", output_json]
    if context:
        parts = [f"=== THÔNG TIN NGỮ CẢNH ===\n{context}\n"] + parts
    parts.append("\nHãy đánh giá và trả về JSON theo định dạng đã quy định.")
    return "\n".join(parts)

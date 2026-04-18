"""
Outline Parser - Parse sườn nội dung GV thành cấu trúc buổi học chuẩn hóa.

Chiến lược parse (ưu tiên):
  1. Markdown table  (| No | Nội dung | ...)
  2. Numbered list   (1. / 1) / Tuần 1: / Buổi 1:)
  3. Raw text        → fallback, cảnh báo, để LLM xử lý

Output chuẩn:
  List[OutlineSessionDict] = [
      {
          "no": int,
          "topic": str,          # nguyên văn GV
          "subtopics": List[str],
          "estimated_periods": int,
          "session_type": "LT" | "TH",
      }
  ]
"""

import re
from typing import List, Dict, Optional
from utils.logger import get_logger

logger = get_logger("utils.outline_parser")

# ── Heuristic: nhận biết dòng thực hành ─────────────────────────────────────
_TH_KEYWORDS = re.compile(
    r"\b(thực hành|lab|laboratory|thực nghiệm|demo|bài tập thực|practice|hands.?on)\b",
    re.IGNORECASE | re.UNICODE,
)


def parse_outline(outline_text: str) -> Dict:
    """
    Parse sườn GV thành cấu trúc chuẩn hóa.

    Returns:
        {
            "sessions": List[OutlineSessionDict],
            "parse_mode": "markdown_table" | "numbered_list" | "raw_text",
            "warnings": List[str],
        }
    """
    if not outline_text or not outline_text.strip():
        return {"sessions": [], "parse_mode": "empty", "warnings": ["Outline rỗng"]}

    text = outline_text.strip()

    # 1. Thử markdown table
    result = _try_parse_markdown_table(text)
    if result:
        logger.info(f"[OutlineParser] Đã parse thành công: markdown_table ({len(result)} buổi)")
        return {"sessions": result, "parse_mode": "markdown_table", "warnings": []}

    # 2. Thử numbered list
    result = _try_parse_numbered_list(text)
    if result:
        logger.info(f"[OutlineParser] Đã parse thành công: numbered_list ({len(result)} buổi)")
        return {"sessions": result, "parse_mode": "numbered_list", "warnings": []}

    # 3. Fallback: raw text
    logger.warning(
        "[OutlineParser] Không thể parse cấu trúc rõ ràng — dùng raw_text fallback. "
        "LLM sẽ xử lý trực tiếp. Nên cung cấp outline dạng bảng hoặc danh sách đánh số."
    )
    return {
        "sessions": _fallback_raw_text(text),
        "parse_mode": "raw_text",
        "warnings": [
            "Không nhận ra định dạng outline (bảng hoặc danh sách đánh số). "
            "Outline được chuyển sang dạng raw text để LLM xử lý. "
            "Kết quả có thể kém chính xác hơn — nên dùng bảng Markdown hoặc danh sách đánh số."
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Chiến lược 1: Markdown table
# ─────────────────────────────────────────────────────────────────────────────

def _try_parse_markdown_table(text: str) -> Optional[List[Dict]]:
    """
    Parse bảng Markdown.
    Chấp nhận các dạng header:
      | STT | Nội dung | Số tiết | Loại |
      | Tuần | Chủ đề | ... |
      | No | Topic | ... |
    """
    lines = [l.rstrip() for l in text.splitlines()]
    table_lines = [l for l in lines if l.strip().startswith("|")]

    if len(table_lines) < 3:  # cần ít nhất header + separator + 1 data row
        return None

    # Xác định chỉ số cột
    header_row = _split_table_row(table_lines[0])
    if not header_row:
        return None

    col_no      = _find_col_index(header_row, ["stt", "no", "buổi", "tuần", "week", "session", "#"])
    col_topic   = _find_col_index(header_row, ["nội dung", "chủ đề", "topic", "content", "tên", "bài"])
    col_periods = _find_col_index(header_row, ["tiết", "số tiết", "periods", "hours", "giờ"])
    col_type    = _find_col_index(header_row, ["loại", "type", "lt/th", "hình thức"])

    if col_topic is None:
        return None  # Không có cột nội dung → không phải outline table

    sessions = []
    auto_no = 1

    for row_line in table_lines[2:]:  # bỏ qua header + separator
        cells = _split_table_row(row_line)
        if not cells:
            continue

        topic = _get_cell(cells, col_topic).strip()
        if not topic or topic == "---":
            continue

        # Số thứ tự
        raw_no = _get_cell(cells, col_no) if col_no is not None else ""
        no = _parse_int(raw_no, default=auto_no)

        # Số tiết
        raw_periods = _get_cell(cells, col_periods) if col_periods is not None else ""
        periods = _parse_int(raw_periods, default=1)

        # Loại buổi
        raw_type = _get_cell(cells, col_type) if col_type is not None else ""
        session_type = _infer_session_type(raw_type, topic)

        sessions.append({
            "no": no,
            "topic": topic,
            "subtopics": [],
            "estimated_periods": periods,
            "session_type": session_type,
        })
        auto_no = no + 1

    return sessions if len(sessions) >= 2 else None


# ─────────────────────────────────────────────────────────────────────────────
# Chiến lược 2: Numbered list
# ─────────────────────────────────────────────────────────────────────────────

# Nhận dạng dòng bắt đầu buổi mới
_SESSION_START = re.compile(
    r"^(?:"
    r"(?:buổi|tuần|week|session|bài|chương|lecture|lab)\s*(\d+)\s*[:\.\-\)]"  # từ khóa + số
    r"|(\d+)\s*[\.\)\-\:]"                                                       # số đầu dòng
    r")\s*(.+)$",
    re.IGNORECASE | re.UNICODE,
)

# Nhận dạng dòng subtopic (thụt vào hoặc bắt đầu bằng dấu đầu dòng)
_SUBTOPIC_LINE = re.compile(r"^\s+[-•*\+]\s+.+|^\s{2,}.+", re.UNICODE)


def _try_parse_numbered_list(text: str) -> Optional[List[Dict]]:
    """
    Parse danh sách đánh số.
    Ví dụ:
        1. Giới thiệu học phần
           - Mục tiêu
           - Nội quy
        2. Lý thuyết đồ thị
        Buổi 3: Thuật toán sắp xếp
    """
    lines = text.splitlines()
    sessions = []
    current: Optional[Dict] = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        m = _SESSION_START.match(stripped)
        if m:
            if current:
                sessions.append(current)
            # Nhóm 1: từ khóa + số; nhóm 2: số đơn; nhóm 3: nội dung
            no_str = m.group(1) or m.group(2) or str(len(sessions) + 1)
            topic = m.group(3).strip()
            no = int(no_str)
            current = {
                "no": no,
                "topic": topic,
                "subtopics": [],
                "estimated_periods": 1,
                "session_type": _infer_session_type("", topic),
            }
        elif current and (line.startswith("  ") or line.startswith("\t") or stripped.startswith("-") or stripped.startswith("•") or stripped.startswith("*")):
            # Dòng subtopic
            sub = stripped.lstrip("-•*+ \t")
            if sub:
                current["subtopics"].append(sub)
        # Các dòng khác (text block, tiêu đề không đánh số) → bỏ qua

    if current:
        sessions.append(current)

    return sessions if len(sessions) >= 2 else None


# ─────────────────────────────────────────────────────────────────────────────
# Fallback: Raw text
# ─────────────────────────────────────────────────────────────────────────────

def _fallback_raw_text(text: str) -> List[Dict]:
    """
    Không parse được cấu trúc → trả về một session duy nhất chứa toàn bộ raw text.
    LLM sẽ nhận raw text này và tự phân tách.
    """
    return [{
        "no": 0,
        "topic": "__RAW_TEXT__",
        "subtopics": [text],
        "estimated_periods": 0,
        "session_type": "LT",
    }]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _split_table_row(row: str) -> List[str]:
    """Tách dòng markdown table thành danh sách cell."""
    row = row.strip()
    if not row.startswith("|"):
        return []
    cells = row.split("|")
    return [c.strip() for c in cells[1:-1]] if len(cells) > 2 else []


def _get_cell(cells: List[str], idx: Optional[int]) -> str:
    if idx is None or idx >= len(cells):
        return ""
    return cells[idx]


def _find_col_index(header: List[str], keywords: List[str]) -> Optional[int]:
    """Tìm chỉ số cột khớp với bất kỳ keyword nào (case-insensitive)."""
    for i, cell in enumerate(header):
        cell_low = cell.lower()
        for kw in keywords:
            if kw in cell_low:
                return i
    return None


def _parse_int(s: str, default: int = 1) -> int:
    m = re.search(r"\d+", s)
    return int(m.group()) if m else default


def _infer_session_type(type_hint: str, topic: str) -> str:
    """Xác định LT hay TH từ gợi ý loại hoặc từ khóa trong topic."""
    combined = (type_hint + " " + topic).lower()
    if _TH_KEYWORDS.search(combined):
        return "TH"
    if "th" in type_hint.lower() and len(type_hint.strip()) <= 4:
        return "TH"
    return "LT"


def is_raw_text_fallback(outline_sessions: List[Dict]) -> bool:
    """Kiểm tra outline_sessions có phải dạng raw text fallback không."""
    return (
        len(outline_sessions) == 1
        and outline_sessions[0].get("topic") == "__RAW_TEXT__"
    )


def outline_sessions_to_text(outline_sessions: List[Dict]) -> str:
    """Chuyển outline_sessions trở lại plain text để đưa vào prompt LLM."""
    if is_raw_text_fallback(outline_sessions):
        subs = outline_sessions[0].get("subtopics", [])
        return subs[0] if subs else ""
    lines = []
    for s in outline_sessions:
        typ = f" [{s.get('session_type', 'LT')}]"
        periods = s.get("estimated_periods", 1)
        period_str = f" ({periods} tiết)" if periods > 0 else ""
        lines.append(f"{s['no']}. {s['topic']}{typ}{period_str}")
        for sub in s.get("subtopics", []):
            lines.append(f"   - {sub}")
    return "\n".join(lines)

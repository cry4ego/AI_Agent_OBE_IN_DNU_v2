"""
RAG Document Loader - Đọc và chunk file đề cương môn học
Hỗ trợ định dạng: .docx, .pdf, .txt
Tương thích với index_builder.py và retriever.py hiện có
"""

import os
import re
from pathlib import Path
from typing import List, Optional
from utils.logger import get_logger

logger = get_logger("rag.document_loader")


# ─── Cấu hình chunking ───────────────────────────────────────────────────────

CHUNK_SIZE = 500          # Số ký tự tối đa mỗi chunk
CHUNK_OVERLAP = 80        # Số ký tự overlap giữa các chunk liên tiếp
MIN_CHUNK_LENGTH = 30     # Giảm từ 50 → 30 để không bỏ qua content ngắn hợp lệ


# ─── Data class ──────────────────────────────────────────────────────────────

class CourseChunk:
    """Đại diện cho một đoạn nội dung từ đề cương môn học."""

    def __init__(self, content: str, metadata: dict):
        self.content = content
        self.metadata = metadata  # type, source, section, chunk_index

    def __repr__(self):
        preview = self.content[:60].replace("\n", " ")
        return f"<CourseChunk [{self.metadata.get('section', '?')}] '{preview}...'>"


# ─── Đọc file theo định dạng ─────────────────────────────────────────────────

def _read_docx(file_path: str) -> str:
    """Đọc nội dung từ file .docx, bao gồm cả nội dung trong bảng."""
    try:
        from docx import Document
        from docx.oxml.ns import qn

        doc = Document(file_path)
        content_parts = []

        # Duyệt theo thứ tự xuất hiện trong file (paragraph + table xen kẽ)
        for block in doc.element.body:
            # Paragraph thường
            if block.tag == qn('w:p'):
                text = ''.join(
                    node.text for node in block.iter()
                    if node.tag == qn('w:t') and node.text
                )
                if text.strip():
                    content_parts.append(text.strip())

            # Bảng (table)
            elif block.tag == qn('w:tbl'):
                for row in block.iter(qn('w:tr')):
                    cells = []
                    for cell in row.iter(qn('w:tc')):
                        cell_text = ''.join(
                            node.text for node in cell.iter()
                            if node.tag == qn('w:t') and node.text
                        )
                        if cell_text.strip():
                            cells.append(cell_text.strip())
                    if cells:
                        content_parts.append(' | '.join(cells))

        return '\n'.join(content_parts)

    except ImportError:
        raise ImportError(
            "Thiếu thư viện python-docx. Chạy: pip install python-docx"
        )
    except Exception as e:
        raise RuntimeError(f"Không thể đọc file .docx: {e}")


def _read_txt(file_path: str) -> str:
    """Đọc nội dung từ file .txt."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="latin-1") as f:
            return f.read()


def _read_pdf(file_path: str) -> str:
    """Đọc nội dung từ file .pdf."""
    try:
        from PyPDF2 import PdfReader
        
        reader = PdfReader(file_path)
        content_parts = []
        
        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                content_parts.append(text.strip())
        
        return '\n'.join(content_parts)
    
    except ImportError:
        raise ImportError(
            "Thiếu thư viện PyPDF2. Chạy: pip install PyPDF2"
        )
    except Exception as e:
        raise RuntimeError(f"Không thể đọc file .pdf: {e}")


def read_file(file_path: str) -> str:
    """
    Đọc nội dung file đề cương theo đúng định dạng.

    Args:
        file_path: Đường dẫn tới file (.docx / .pdf / .txt)

    Returns:
        Nội dung raw dạng string

    Raises:
        ValueError: Định dạng file không được hỗ trợ
        FileNotFoundError: File không tồn tại
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

    suffix = path.suffix.lower()

    if suffix == ".docx":
        logger.info(f"Đọc file .docx: {path.name}")
        return _read_docx(file_path)
    elif suffix == ".pdf":
        logger.info(f"Đọc file .pdf: {path.name}")
        return _read_pdf(file_path)
    elif suffix == ".txt":
        logger.info(f"Đọc file .txt: {path.name}")
        return _read_txt(file_path)
    else:
        raise ValueError(
            f"Định dạng '{suffix}' chưa được hỗ trợ. "
            "Chỉ hỗ trợ: .docx, .pdf, .txt"
        )


# ─── Phát hiện section trong đề cương ────────────────────────────────────────

# Các từ khóa tiêu biểu của từng section trong đề cương DNU
SECTION_PATTERNS = {
    "thong_tin_mon_hoc": [
        r"thông tin môn học", r"thông tin học phần",
        r"tên môn học", r"mã môn", r"số tín chỉ"
    ],
    "mo_ta_mon_hoc": [
        r"mô tả môn học", r"mô tả học phần",
        r"giới thiệu môn học", r"tóm tắt nội dung"
    ],
    "clo": [
        r"chuẩn đầu ra", r"course learning outcome",
        r"CLO", r"kết quả học tập mong đợi"
    ],
    "noi_dung": [
        r"nội dung môn học", r"nội dung chi tiết",
        r"kế hoạch giảng dạy", r"phân bổ thời gian",
        r"chương \d+", r"tuần \d+"
    ],
    "danh_gia": [
        r"phương pháp đánh giá", r"hình thức đánh giá",
        r"kiểm tra", r"thi", r"thang điểm"
    ],
    "tai_lieu": [
        r"tài liệu tham khảo", r"giáo trình",
        r"sách tham khảo", r"học liệu"
    ],
    "dieu_kien": [
        r"điều kiện tiên quyết", r"môn học trước",
        r"yêu cầu đầu vào"
    ],
}


def _detect_section(text_line: str) -> Optional[str]:
    """Phát hiện section của một dòng text dựa trên từ khóa."""
    line_stripped = text_line.strip()
    for section_name, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                return section_name
    return None


# ─── Chunking ─────────────────────────────────────────────────────────────────

def _split_into_chunks(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Tách text thành các chunk có độ dài chunk_size với overlap.
    Ưu tiên tách tại dấu xuống dòng hoặc dấu chấm để giữ nguyên câu.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end >= len(text):
            # Chunk cuối cùng
            final_chunk = text[start:].strip()
            if len(final_chunk) >= MIN_CHUNK_LENGTH:
                chunks.append(final_chunk)
            break

        # Tìm điểm tách gần nhất (ưu tiên \n, rồi ". ", rồi " ")
        cut = -1
        for sep in ["\n", ". ", " "]:
            pos = text.rfind(sep, start, end)
            if pos > start:
                cut = pos + len(sep)
                break

        if cut == -1:
            cut = end  # Cắt cứng nếu không tìm được

        chunk_text = text[start:cut].strip()
        if len(chunk_text) >= MIN_CHUNK_LENGTH:
            chunks.append(chunk_text)
        
        # Tính start tiếp theo với overlap
        # Đảm bảo luôn tiến về phía trước
        start = max(cut - overlap, start + 1)

    return chunks


def chunk_course_document(
    raw_text: str,
    source_filename: str,
    course_name: str = "",
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> List[CourseChunk]:
    """
    Tách nội dung đề cương thành các CourseChunk có metadata đầy đủ.

    Args:
        raw_text: Nội dung raw đọc từ file
        source_filename: Tên file gốc (để ghi vào metadata)
        course_name: Tên môn học (nếu biết trước)
        chunk_size: Số ký tự tối đa mỗi chunk
        overlap: Số ký tự overlap

    Returns:
        Danh sách CourseChunk
    """
    lines = raw_text.split("\n")
    sections: List[dict] = []  # [{"section": str, "lines": [str]}]
    current_section = "general"
    current_lines = []

    # Phân chia theo section
    for line in lines:
        detected = _detect_section(line)
        if detected:
            if current_lines:
                sections.append({
                    "section": current_section,
                    "text": "\n".join(current_lines).strip()
                })
            current_section = detected
            current_lines = [line]
        else:
            current_lines.append(line)

    # Lưu section cuối
    if current_lines:
        sections.append({
            "section": current_section,
            "text": "\n".join(current_lines).strip()
        })

    # Tạo CourseChunk từ mỗi section
    all_chunks: List[CourseChunk] = []
    chunk_index = 0

    for section_data in sections:
        section_name = section_data["section"]
        section_text = section_data["text"]

        if not section_text:
            continue

        sub_chunks = _split_into_chunks(section_text, chunk_size, overlap)

        for sub in sub_chunks:
            # Bỏ qua chunk quá ngắn (tiêu đề rỗng, v.v.)
            if len(sub.strip()) < MIN_CHUNK_LENGTH:
                continue
            all_chunks.append(
                CourseChunk(
                    content=sub,
                    metadata={
                        "type": "course_outline",
                        "section": section_name,
                        "source": source_filename,
                        "course_name": course_name,
                        "chunk_index": chunk_index,
                    }
                )
            )
            chunk_index += 1

    logger.info(
        f"Chunking hoàn tất: {len(all_chunks)} chunks "
        f"từ {len(sections)} sections — file: {source_filename}"
    )
    return all_chunks


# ─── API chính ────────────────────────────────────────────────────────────────

def load_course_document(
    file_path: str,
    course_name: str = "",
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> List[CourseChunk]:
    """
    Hàm chính: Đọc file đề cương và trả về danh sách CourseChunk.

    Args:
        file_path: Đường dẫn tới file (.docx / .pdf / .txt)
        course_name: Tên môn học (tùy chọn, giúp metadata chính xác hơn)
        chunk_size: Kích thước chunk (mặc định 500 ký tự)
        overlap: Overlap giữa các chunk (mặc định 80 ký tự)

    Returns:
        List[CourseChunk] — sẵn sàng để đưa vào vector store

    Example:
        chunks = load_course_document("uploads/CTDL_GT.docx", course_name="Cấu trúc dữ liệu")
    """
    filename = Path(file_path).name

    try:
        raw_text = read_file(file_path)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        logger.error(f"Lỗi đọc file '{filename}': {e}")
        raise

    if not raw_text.strip():
        logger.warning(f"File '{filename}' rỗng hoặc không trích xuất được text.")
        return []

    chunks = chunk_course_document(
        raw_text=raw_text,
        source_filename=filename,
        course_name=course_name,
        chunk_size=chunk_size,
        overlap=overlap,
    )

    return chunks


def chunks_to_langchain_documents(chunks: List[CourseChunk]):
    """
    Chuyển đổi List[CourseChunk] → List[Document] của LangChain
    để đưa thẳng vào QdrantVectorStore.add_documents().

    Returns:
        List[langchain_core.documents.Document]
    """
    from langchain_core.documents import Document

    return [
        Document(page_content=chunk.content, metadata=chunk.metadata)
        for chunk in chunks
    ]

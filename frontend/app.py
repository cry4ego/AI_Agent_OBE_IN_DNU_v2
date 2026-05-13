# """
# Streamlit Frontend - Giao diện người dùng cho OBE DCCT Agent
# """

# import asyncio
# import json
# import os
# import sys
# from datetime import datetime
# from pathlib import Path

# # Đảm bảo có thể import từ project root
# sys.path.insert(0, str(Path(__file__).parent.parent))

# import streamlit as st

# # ============================================================
# # HISTORY HELPERS (lưu/đọc lịch sử DCCT vào disk)
# # ============================================================

# _HISTORY_FILE = Path(__file__).parent.parent / "output" / "dcct_history.json"


# def _load_history() -> list:
#     """Đọc danh sách DCCT đã tạo từ file JSON."""
#     if _HISTORY_FILE.exists():
#         try:
#             return json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
#         except Exception:
#             return []
#     return []


# def _save_to_history(result: dict) -> None:
#     """Thêm/cập nhật một DCCT vào file JSON lịch sử."""
#     try:
#         history = _load_history()
#         course_code = result.get("course_code", "UNKNOWN")
#         entry = {
#             "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
#             "course_code": course_code,
#             "course_name": result.get("course_name", ""),
#             "credits": result.get("credits", ""),
#             "result": result,
#         }
#         # Thay thế entry cũ nếu cùng mã học phần
#         history = [h for h in history if h.get("course_code") != course_code]
#         history.insert(0, entry)   # mới nhất lên đầu
#         history = history[:30]     # giữ tối đa 30 bản
#         _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
#         _HISTORY_FILE.write_text(
#             json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
#         )
#     except Exception:
#         pass  # history là tính năng phụ, không để crash app


# # ============================================================
# # PAGE CONFIG
# # ============================================================

# st.set_page_config(
#     page_title="OBE DCCT Agent - ĐH Đại Nam",
#     page_icon="🎓",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

# # ============================================================
# # STYLES
# # ============================================================

# st.markdown("""
# <style>
#     .main-header {
#         background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%);
#         padding: 1.5rem;
#         border-radius: 10px;
#         color: white;
#         margin-bottom: 1.5rem;
#     }
#     .section-card {
#         background: #f8f9fa;
#         padding: 1rem;
#         border-radius: 8px;
#         border-left: 4px solid #2d6a9f;
#         margin: 0.5rem 0;
#     }
#     .clo-item {
#         background: white;
#         padding: 0.7rem;
#         border-radius: 6px;
#         border: 1px solid #dee2e6;
#         margin: 0.3rem 0;
#     }
#     .confidence-high { color: #28a745; font-weight: bold; font-size: 1.2em; }
#     .confidence-mid { color: #ffc107; font-weight: bold; font-size: 1.2em; }
#     .confidence-low { color: #dc3545; font-weight: bold; font-size: 1.2em; }
#     .metric-box {
#         text-align: center;
#         padding: 1rem;
#         background: #e8f4f8;
#         border-radius: 8px;
#     }
# </style>
# """, unsafe_allow_html=True)

# # ============================================================
# # SIDEBAR
# # ============================================================

# with st.sidebar:
#     st.markdown("### 🎓 DNU - Khoa CNTT")
#     st.markdown("### ⚙️ Cài đặt Agent")

#     st.markdown("**API Keys:**")
#     google_key = st.text_input("Google API Key", type="password",
#                                value=os.getenv("GOOGLE_API_KEY", ""),
#                                help="Gemini API key từ Google AI Studio")
#     anthropic_key = st.text_input("Anthropic API Key", type="password",
#                                   value=os.getenv("ANTHROPIC_API_KEY", ""),
#                                   help="Claude API key từ Anthropic Console")

#     if google_key:
#         os.environ["GOOGLE_API_KEY"] = google_key
#     if anthropic_key:
#         os.environ["ANTHROPIC_API_KEY"] = anthropic_key

#     st.divider()
#     st.markdown("**Thông tin:**")
#     st.caption("🤖 LangGraph Agentic Workflow")
#     st.caption("📚 OBE / AUN-QA Standard")
#     st.caption("🏫 Khoa CNTT - ĐH Đại Nam")

#     # ── Lịch sử DCCT ─────────────────────────────────────────
#     st.divider()
#     st.markdown("**📋 Lịch sử DCCT đã tạo:**")
#     _history = _load_history()
#     if _history:
#         for _idx, _h in enumerate(_history):
#             _label = (
#                 f"[{_h['timestamp']}]\n"
#                 f"{_h['course_code']} – {_h.get('course_name', '')[:22]}"
#             )
#             if st.button(_label, key=f"hist_{_idx}", use_container_width=True):
#                 st.session_state["result"] = _h["result"]
#                 st.session_state["course_code"] = _h["course_code"]
#                 st.session_state["course_name"] = _h.get("course_name", "")
#                 st.rerun()
#         if st.button("🗑️ Xóa toàn bộ lịch sử", use_container_width=True, key="clear_hist"):
#             if _HISTORY_FILE.exists():
#                 _HISTORY_FILE.unlink()
#             st.rerun()
#     else:
#         st.caption("Chưa có DCCT nào được lưu.")

# # ============================================================
# # MAIN HEADER
# # ============================================================

# st.markdown("""
# <div class="main-header">
#     <h1 style="margin:0">🎓 OBE DCCT Agent</h1>
#     <p style="margin:0.3rem 0 0 0; opacity:0.9">
#         Hệ thống tự động tạo Đề cương Chi tiết Học phần theo chuẩn Outcome-Based Education
#     </p>
# </div>
# """, unsafe_allow_html=True)

# # ============================================================
# # INPUT FORM
# # ============================================================

# st.markdown("## 📝 Nhập thông tin học phần")

# with st.form("course_input_form", clear_on_submit=False):
#     col1, col2 = st.columns([1, 2])

#     with col1:
#         course_code = st.text_input(
#             "Mã học phần *",
#             placeholder="VD: CSC4012",
#             help="Mã học phần theo quy định của trường",
#         )
#         credits = st.selectbox(
#             "Số tín chỉ *",
#             options=["2", "3", "4", "5"],
#             index=1,
#         )

#     with col2:
#         course_name = st.text_input(
#             "Tên học phần *",
#             placeholder="VD: Trí tuệ nhân tạo ứng dụng",
#         )
#         course_type = st.selectbox(
#             "Loại học phần",
#             options=["Lý thuyết + Thực hành", "Lý thuyết", "Thực hành"],
#             index=0,
#         )

#     program_col1, program_col2 = st.columns([1, 3])
#     with program_col1:
#         program = st.selectbox(
#             "Ngành / Chương trình đào tạo *",
#             options=["KHMT", "HTTT", "GENERIC"],
#             index=0,
#             format_func=lambda x: {
#                 "KHMT": "💻 Khoa học Máy tính (KHMT)",
#                 "HTTT": "📊 Hệ thống Thông tin (HTTT)",
#                 "GENERIC": "⚙️ Chung (Khoa CNTT)",
#             }[x],
#             help="Chọn ngành để dùng đúng bộ PLO-PI của ngành đó khi ánh xạ CLO",
#         )
#     with program_col2:
#         _plo_hints = {
#             "KHMT": "PLO-CS01 – CS08 | PI định hướng: Đạo đức AI, Lập luận, Thuật toán, Thực nghiệm, Học máy, Kiến trúc, Giao tiếp, Tự học",
#             "HTTT": "PLO-IS01 – IS08 | PI định hướng: Tuân thủ, Kỹ thuật, Yêu cầu, Quy trình, Dữ liệu, BI/KPI, Tích hợp, Dự án",
#             "GENERIC": "PLO1 – PLO10 | Bộ chuẩn chung cho toàn Khoa CNTT",
#         }
#         st.info(_plo_hints.get(program, ""), icon="🎯")

#     _sc1, _sc2 = st.columns([2, 2])
#     with _sc1:
#         session_structure = st.selectbox(
#             "Cấu trúc mỗi buổi học",
#             options=[
#                 "5 tiết (3 LT + 2 TH)",
#                 "4 tiết (3 LT + 1 TH)",
#                 "4 tiết (2 LT + 2 TH)",
#                 "3 tiết (2 LT + 1 TH)",
#                 "2 tiết (2 LT)",
#             ],
#             index=0,
#             help="Số tiết mỗi buổi — 1 tuần = 1 buổi cho học phần này",
#         )
#     _split_map = {
#         "5 tiết (3 LT + 2 TH)": (5, 3),
#         "4 tiết (3 LT + 1 TH)": (4, 3),
#         "4 tiết (2 LT + 2 TH)": (4, 2),
#         "3 tiết (2 LT + 1 TH)": (3, 2),
#         "2 tiết (2 LT)": (2, 2),
#     }
#     _pps, _tps = _split_map.get(session_structure, (5, 3))
#     with _sc2:
#         st.info(
#             f"📊 {credits} TC × 15 tiết = {int(credits)*15} tiết "
#             f"÷ {_pps} tiết/buổi = **{int(credits)*15//_pps} buổi** ({int(credits)*15//_pps} tuần)",
#             icon="📅",
#         )

#     summary = st.text_area(
#         "Mô tả / Tóm tắt học phần *",
#         placeholder="Nhập mô tả ngắn về nội dung, mục tiêu học phần...",
#         height=120,
#     )

#     outline = st.text_area(
#         "Sườn nội dung buổi học (khuyến nghị mạnh)",
#             placeholder="Dán sườn nội dung các buổi học (outline), hoặc đề cương cũ...",
#             height=100,
#     )

#     col3, col4 = st.columns(2)
#     with col3:
#         submitted = st.form_submit_button(
#             "🚀 Tạo DCCT tự động",
#             type="primary",
#             use_container_width=True,
#         )
#     with col4:
#         demo_btn = st.form_submit_button(
#             "🎯 Chạy Demo",
#             use_container_width=True,
#         )

# # ============================================================
# # RUN AGENT
# # ============================================================

# def run_agent_sync(course_code, course_name, credits, summary, outline=None, program=None,
#                    periods_per_session=5, theory_per_session=3):
#     """Wrapper đồng bộ để chạy async agent trong Streamlit."""
#     from config import validate_config

#     if not validate_config():
#         return None, "Cần cấu hình ít nhất một API Key (Google hoặc Anthropic)"

#     from graph import get_graph

#     initial_state = {
#         "user_input": f"{course_code} - {course_name}\n{summary}",
#         "course_code": course_code,
#         "course_name": course_name,
#         "credits": credits,
#         "summary": summary,
#         "outline": outline,
#         "program": program,          # HTTT | KHMT | GENERIC
#         "periods_per_session": periods_per_session,
#         "theory_per_session":  theory_per_session,
#         "irma_matrix": None,         # giảng viên chưa nhập IRMA tại bước này
#         "extracted_info": {},
#         "clo_list": [],
#         "mapping_matrix": [],
#         "teaching_plan": [],
#         "assessment_plan": [],
#         "rubrics": {},
#         "messages": [],
#         "current_step": "understand",
#         "confidence_score": 0.0,
#         "critic_feedback": [],
#         "retry_counts": {},
#         "preview_data": None,
#         "needs_human_input": False,
#         "human_feedback": None,
#         "final_dcct_data": None,
#         "export_ready": False,
#         "errors": [],
#         "warnings": [],
#     }

#     graph = get_graph()

#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     try:
#         result = loop.run_until_complete(
#             graph.ainvoke(initial_state, config={"configurable": {"thread_id": "1"}})
#         )
#         return result, None
#     except Exception as e:
#         return None, str(e)
#     finally:
#         loop.close()


# if submitted or demo_btn:
#     # Demo values nếu form trống
#     if demo_btn:
#         course_code = course_code or "CSC4012"
#         course_name = course_name or "Trí tuệ nhân tạo ứng dụng"
#         credits = credits or "3"
#         summary = summary or (
#             "Học phần giới thiệu các khái niệm và ứng dụng thực tế của Trí tuệ nhân tạo. "
#             "Sinh viên học về machine learning, deep learning, xử lý ngôn ngữ tự nhiên và "
#             "computer vision, với các bài thực hành sử dụng Python và các thư viện AI phổ biến."
#         )

#     # Validate input — CASE 5: highlight specific missing fields
#     _missing = []
#     if not course_code or not course_code.strip():
#         _missing.append("**Mã học phần**")
#     if not course_name or not course_name.strip():
#         _missing.append("**Tên học phần**")
#     if not summary or not summary.strip():
#         _missing.append("**Mô tả / Tóm tắt học phần**")

#     if _missing:
#         st.error("⚠️ Vui lòng nhập đầy đủ các trường bắt buộc: " + ", ".join(_missing))
#     else:
#         # Progress tracking
#         progress_container = st.empty()
#         status_container = st.empty()

#         with st.spinner("🤖 AI Agent đang xử lý..."):
#             progress_bar = progress_container.progress(0, "Đang khởi động...")

#             steps = [
#                 "Khởi tạo RAG system...",
#                 "Phân tích học phần và sinh CLO...",
#                 "Ánh xạ CLO → PI → PLO...",
#                 "Xây dựng kế hoạch giảng dạy...",
#                 "Thiết kế hệ thống đánh giá...",
#                 "Kiểm chứng và hoàn thiện...",
#             ]

#             # Simulate progress (thực tế sẽ update qua callback)
#             import time
#             for i, step in enumerate(steps):
#                 progress_bar.progress((i + 1) / len(steps), step)
#                 time.sleep(0.2)

#             result, error = run_agent_sync(
#                 course_code, course_name, credits, summary,
#                 outline if outline else None,
#                 program=program,
#                 periods_per_session=_pps,
#                 theory_per_session=_tps,
#             )

#         progress_container.empty()

#         if error:
#             st.error(f"❌ Lỗi: {error}")
#         elif result:
#             st.success("✅ Đã tạo DCCT thành công!")
#             st.session_state["result"] = result
#             st.session_state["course_code"] = course_code
#             st.session_state["course_name"] = course_name
#             _save_to_history(result)


# # ============================================================
# # UPLOAD DCCT CŨ — Tái chuẩn hóa theo OBE
# # ============================================================

# st.divider()
# st.markdown("### 📂 Hoặc: Tải lên DCCT cũ để tái chuẩn hóa theo chuẩn OBE")

# with st.expander(
#     "📤 Mở rộng để tải lên file đề cương cũ (.docx)",
#     expanded=st.session_state.get("_upload_expander_open", False),
# ):
#     st.caption(
#         "Tải lên đề cương chi tiết học phần hiện có (chỉ hỗ trợ **.docx**, tối đa 10 MB). "
#         "Hệ thống sẽ trích xuất thông tin, sau đó bạn chỉnh sửa và nhấn "
#         "**Tái tạo DCCT** để xây dựng lại theo chuẩn OBE/AUN-QA."
#     )

#     # CASE 1: chỉ chấp nhận .docx
#     uploaded_file = st.file_uploader(
#         "Chọn file đề cương (.docx)",
#         type=["docx"],
#         label_visibility="collapsed",
#         key="dcct_upload_widget",
#     )

#     if uploaded_file:
#         # CASE 3: kiểm tra kích thước file > 10 MB
#         _MAX_MB = 10
#         if uploaded_file.size > _MAX_MB * 1024 * 1024:
#             st.error(
#                 f"⚠️ File quá lớn ({uploaded_file.size / 1024 / 1024:.1f} MB). "
#                 f"Giới hạn tối đa là {_MAX_MB} MB. Vui lòng nén hoặc cắt bớt nội dung."
#             )
#         else:
#             parse_col, _ = st.columns([1, 3])
#             with parse_col:
#                 parse_clicked = st.button(
#                     "🔍 Trích xuất thông tin từ file",
#                     use_container_width=True,
#                     key="btn_parse_upload",
#                 )

#             if parse_clicked:
#                 with st.spinner("Đang phân tích file..."):
#                     try:
#                         from utils.dcct_parser import extract_text_from_bytes, parse_dcct_info

#                         # CASE 2: ValueError được raise cho file corrupt
#                         raw_text = extract_text_from_bytes(
#                             uploaded_file.getvalue(), uploaded_file.name
#                         )
#                         if raw_text.strip():
#                             extracted = parse_dcct_info(raw_text)

#                             # CASE 4: cảnh báo nội dung nghèo
#                             if not extracted.get("summary") or len(extracted.get("summary", "")) < 50:
#                                 st.warning(
#                                     "⚠️ Không trích xuất được mô tả học phần. "
#                                     "Vui lòng nhập thủ công vào ô **Mô tả / Mục tiêu** bên dưới."
#                                 )
#                             if not extracted.get("outline"):
#                                 st.info(
#                                     "ℹ️ Không tìm thấy sườn buổi học trong file. "
#                                     "AI sẽ tự sinh lịch giảng dạy từ mô tả."
#                                 )

#                             st.session_state["_upload_extracted"] = extracted
#                             st.session_state["_upload_filename"] = uploaded_file.name
#                             st.session_state["_upload_expander_open"] = True
#                             st.rerun()
#                         else:
#                             st.error(
#                                 "❌ File .docx không có nội dung văn bản. "
#                                 "Vui lòng kiểm tra lại hoặc copy-paste nội dung vào form bên trên."
#                             )
#                     except ValueError as _ve:
#                         # CASE 2: file bị hỏng/corrupt
#                         st.error(
#                             "❌ File không đọc được, vui lòng kiểm tra lại. "
#                             f"Chi tiết: {_ve}"
#                         )
#                     except Exception as _e:
#                         st.error(f"❌ Lỗi khi xử lý file: {_e}")

#     # ── Hiển thị và chỉnh sửa thông tin đã trích xuất ────────────────────────
#     if "_upload_extracted" in st.session_state:
#         _ext = st.session_state["_upload_extracted"]
#         _fname = st.session_state.get("_upload_filename", "")

#         st.success(f"✅ Đã trích xuất từ: **{_fname}**. Kiểm tra và chỉnh sửa trước khi tái tạo.")
#         st.markdown("---")

#         _u_col1, _u_col2, _u_col3 = st.columns([1.2, 3, 0.8])
#         with _u_col1:
#             _u_code = st.text_input(
#                 "Mã học phần",
#                 value=_ext.get("course_code", ""),
#                 key="up_code",
#                 placeholder="VD: CSC4007",
#             )
#         with _u_col2:
#             _u_name = st.text_input(
#                 "Tên học phần",
#                 value=_ext.get("course_name", ""),
#                 key="up_name",
#                 placeholder="VD: Học sâu và Thị giác Máy tính",
#             )
#         with _u_col3:
#             _cred_opts = ["2", "3", "4", "5"]
#             _cred_default = _ext.get("credits", "3")
#             _cred_idx = _cred_opts.index(_cred_default) if _cred_default in _cred_opts else 1
#             _u_credits = st.selectbox("Tín chỉ", options=_cred_opts, index=_cred_idx, key="up_credits")

#         _up_prog_col, _up_type_col, _up_split_col = st.columns(3)
#         with _up_prog_col:
#             _u_program = st.selectbox(
#                 "Ngành / Chương trình đào tạo",
#                 options=["KHMT", "HTTT", "GENERIC"],
#                 index=0,
#                 format_func=lambda x: {
#                     "KHMT": "💻 Khoa học Máy tính (KHMT)",
#                     "HTTT": "📈 Hệ thống Thông tin (HTTT)",
#                     "GENERIC": "⚙️ Chung (Khoa CNTT)",
#                 }[x],
#                 key="up_program",
#             )
#         with _up_type_col:
#             _u_course_type = st.selectbox(
#                 "Loại học phần",
#                 options=["Lý thuyết + Thực hành", "Lý thuyết", "Thực hành"],
#                 index=0,
#                 key="up_course_type",
#             )
#         with _up_split_col:
#             _u_session_structure = st.selectbox(
#                 "Cấu trúc mỗi buổi học",
#                 options=[
#                     "5 tiết (3 LT + 2 TH)",
#                     "4 tiết (3 LT + 1 TH)",
#                     "4 tiết (2 LT + 2 TH)",
#                     "3 tiết (2 LT + 1 TH)",
#                     "2 tiết (2 LT)",
#                 ],
#                 index=0,
#                 key="up_session_structure",
#             )
#         _split_map_up = {
#             "5 tiết (3 LT + 2 TH)": (5, 3),
#             "4 tiết (3 LT + 1 TH)": (4, 3),
#             "4 tiết (2 LT + 2 TH)": (4, 2),
#             "3 tiết (2 LT + 1 TH)": (3, 2),
#             "2 tiết (2 LT)": (2, 2),
#         }
#         _up_pps, _up_tps = _split_map_up.get(_u_session_structure, (5, 3))

#         _u_summary = st.text_area(
#             "Mô tả / Mục tiêu học phần",
#             value=_ext.get("summary", ""),
#             height=120,
#             key="up_summary",
#             help="Chỉnh sửa nếu cần — mô tả này sẽ hướng dẫn AI sinh CLO",
#         )
#         _u_outline = st.text_area(
#             "Sườn nội dung buổi học (từ đề cương cũ)",
#             value=_ext.get("outline", ""),
#             height=180,
#             key="up_outline",
#             help="Agent sẽ GIỮ NGUYÊN sườn này và bổ sung CLO/IRMA theo OBE",
#         )

#         st.markdown("---")
#         _regen_col1, _regen_col2 = st.columns([3, 1])
#         with _regen_col1:
#             _regen_btn = st.button(
#                 "🚀 Tái tạo DCCT theo chuẩn OBE",
#                 type="primary",
#                 use_container_width=True,
#                 key="btn_regenerate_upload",
#             )
#         with _regen_col2:
#             if st.button("🗑️ Xóa dữ liệu upload", use_container_width=True, key="btn_clear_upload"):
#                 for _k in ["_upload_extracted", "_upload_filename", "_upload_expander_open"]:
#                     st.session_state.pop(_k, None)
#                 st.rerun()

#         if _regen_btn:
#             # CASE 5: highlight specific missing fields for re-generate flow
#             _up_missing = []
#             if not _u_code or not _u_code.strip():
#                 _up_missing.append("**Mã học phần**")
#             if not _u_name or not _u_name.strip():
#                 _up_missing.append("**Tên học phần**")
#             if not _u_summary or not _u_summary.strip():
#                 _up_missing.append("**Mô tả / Mục tiêu học phần**")
#             if _up_missing:
#                 st.error("⚠️ Vui lòng nhập đầy đủ: " + ", ".join(_up_missing))
#             else:
#                 _up_progress = st.empty()
#                 with st.spinner("🤖 AI Agent đang tái chuẩn hóa DCCT theo OBE..."):
#                     import time

#                     _up_steps = [
#                         "Khởi tạo RAG system...",
#                         "Phân tích đề cương cũ và sinh CLO OBE...",
#                         "Ánh xạ CLO → PI → PLO...",
#                         "Xây dựng kế hoạch giảng dạy...",
#                         "Thiết kế hệ thống đánh giá...",
#                         "Kiểm chứng và hoàn thiện...",
#                     ]
#                     _up_pb = _up_progress.progress(0, _up_steps[0])
#                     for _i, _s in enumerate(_up_steps):
#                         _up_pb.progress((_i + 1) / len(_up_steps), _s)
#                         time.sleep(0.15)

#                     _up_result, _up_error = run_agent_sync(
#                         _u_code,
#                         _u_name,
#                         _u_credits,
#                         _u_summary,
#                         outline=_u_outline if _u_outline.strip() else None,
#                         program=_u_program,
#                         periods_per_session=_up_pps,
#                         theory_per_session=_up_tps,
#                     )

#                 _up_progress.empty()

#                 if _up_error:
#                     st.error(f"❌ Lỗi: {_up_error}")
#                 elif _up_result:
#                     st.success("✅ Đã tái tạo DCCT theo chuẩn OBE thành công!")
#                     st.session_state["result"] = _up_result
#                     st.session_state["course_code"] = _u_code
#                     st.session_state["course_name"] = _u_name
#                     # Xóa trạng thái upload sau khi xong
#                     for _k in ["_upload_extracted", "_upload_filename", "_upload_expander_open"]:
#                         st.session_state.pop(_k, None)
#                     _save_to_history(_up_result)
#                     st.rerun()


# # ============================================================
# # Q&A HELPER FUNCTIONS
# # ============================================================

# def _auto_index_dcct(state: dict) -> dict:
#     """Index ĐCCT vào knowledge base, lưu trạng thái vào session."""
#     try:
#         from agents.qa_agent import index_dcct_from_state
#         course_code = state.get("course_code", "UNKNOWN")
#         info = index_dcct_from_state(course_code, state)
#         st.session_state["qa_indexed"] = True
#         st.session_state["qa_course_code"] = course_code
#         st.session_state["qa_chunks_count"] = info["chunks_indexed"]
#         return info
#     except Exception as e:
#         st.session_state["qa_indexed"] = False
#         return {}


# def _render_qa_tab(result: dict):
#     """Render toàn bộ giao diện Q&A trong tab."""
#     from agents.qa_agent import (
#         ask_dcct_sync,
#         ask_dcct_dual_sync,
#         get_suggested_questions,
#         get_indexed_courses,
#     )

#     course_code = result.get("course_code", "")
#     course_name = result.get("course_name", "")

#     st.markdown("## 💬 Hỏi đáp về Đề cương Chi tiết Học phần")
#     st.caption(
#         "Đặt câu hỏi về ĐCCT — hệ thống sẽ trả lời theo vai trò Giảng viên hoặc Sinh viên."
#     )

#     # ── Auto-index nếu chưa có ────────────────────────────────────────────────
#     if not st.session_state.get("qa_indexed") or \
#        st.session_state.get("qa_course_code") != course_code:
#         with st.spinner("Đang chuẩn bị knowledge base Q&A..."):
#             info = _auto_index_dcct(result)
#         if info:
#             st.success(
#                 f"✅ Knowledge base sẵn sàng: {info['chunks_indexed']} chunks "
#                 f"({info['clo_count']} CLO, {info['session_count']} buổi học)"
#             )

#     # ── Cài đặt Q&A ──────────────────────────────────────────────────────────
#     st.markdown("---")
#     qa_cfg_col1, qa_cfg_col2 = st.columns([1, 2])

#     with qa_cfg_col1:
#         qa_mode = st.radio(
#             "Chế độ trả lời",
#             options=["dual", "sv", "gv"],
#             format_func=lambda x: {
#                 "dual": "🔀 Đầu ra kép (GV + SV)",
#                 "sv":   "🎓 Sinh viên",
#                 "gv":   "👨‍🏫 Giảng viên",
#             }[x],
#             horizontal=False,
#             key="qa_mode",
#         )

#     with qa_cfg_col2:
#         # Câu hỏi gợi ý
#         suggest_role = "gv" if qa_mode == "gv" else "sv"
#         suggested = get_suggested_questions(course_code, suggest_role)
#         st.markdown("**Câu hỏi gợi ý:**")
#         for i, sq in enumerate(suggested[:3]):
#             if st.button(sq, key=f"sq_{i}", use_container_width=True):
#                 st.session_state["qa_input_prefill"] = sq

#     # ── Input câu hỏi ─────────────────────────────────────────────────────────
#     prefill = st.session_state.pop("qa_input_prefill", "")
#     question = st.text_input(
#         "Nhập câu hỏi của bạn",
#         value=prefill,
#         placeholder="VD: Điểm học phần được tính như thế nào?",
#         key="qa_question_input",
#     )

#     ask_col1, ask_col2 = st.columns([3, 1])
#     with ask_col1:
#         ask_btn = st.button(
#             "🔍 Hỏi",
#             type="primary",
#             use_container_width=True,
#             disabled=not question.strip(),
#         )
#     with ask_col2:
#         clear_btn = st.button(
#             "🗑️ Xóa lịch sử",
#             use_container_width=True,
#         )

#     if clear_btn:
#         st.session_state["qa_history"] = []
#         st.rerun()

#     # ── Xử lý câu hỏi ─────────────────────────────────────────────────────────
#     if ask_btn and question.strip():
#         history = st.session_state.get("qa_history", [])

#         with st.spinner("🤖 Đang tìm kiếm và soạn câu trả lời..."):
#             try:
#                 if qa_mode == "dual":
#                     qa_result = ask_dcct_dual_sync(course_code, question, history)
#                     answer_gv = qa_result.get("answer_gv", "")
#                     answer_sv = qa_result.get("answer_sv", "")
#                     sources   = qa_result.get("sources", [])
#                     warning   = qa_result.get("warning", "")
#                 else:
#                     qa_result = ask_dcct_sync(course_code, question, qa_mode, history)
#                     answer_gv = qa_result.get("answer", "") if qa_mode == "gv" else ""
#                     answer_sv = qa_result.get("answer", "") if qa_mode == "sv" else ""
#                     sources   = qa_result.get("sources", [])
#                     warning   = qa_result.get("warning", "")

#                 if warning and not answer_gv and not answer_sv:
#                     st.error(f"⚠️ {warning}")
#                 else:
#                     # Lưu vào lịch sử
#                     entry = {
#                         "question":  question,
#                         "answer_gv": answer_gv,
#                         "answer_sv": answer_sv,
#                         "mode":      qa_mode,
#                         "sources":   sources,
#                     }
#                     history.append({"role": "user",      "content": question})
#                     history.append({"role": "assistant", "content": answer_gv or answer_sv})
#                     st.session_state["qa_history"] = history[-10:]  # giữ 5 lượt gần nhất

#                     # Hiển thị câu trả lời mới nhất ngay
#                     _display_qa_answer(question, entry, qa_mode)

#             except Exception as e:
#                 st.error(f"Lỗi khi xử lý câu hỏi: {e}")

#     # ── Lịch sử Q&A ───────────────────────────────────────────────────────────
#     history_entries = [
#         e for e in st.session_state.get("qa_history", []) if e.get("role") == "user"
#     ]
#     if len(history_entries) > 1:  # Hiển thị lịch sử nếu có hơn 1 lượt hỏi
#         st.markdown("---")
#         st.markdown("#### 📜 Lịch sử hỏi đáp")
#         # Rebuild full entries from session
#         full_history = st.session_state.get("_qa_full_history", [])
#         for i, entry in enumerate(reversed(full_history[:-1])):  # bỏ lượt gần nhất đã hiển thị
#             with st.expander(f"Q{len(full_history) - i - 1}: {entry['question'][:80]}"):
#                 _display_qa_answer(entry["question"], entry, entry.get("mode", "sv"))


# def _display_qa_answer(question: str, entry: dict, mode: str):
#     """Render một câu trả lời Q&A."""
#     answer_gv = entry.get("answer_gv", "")
#     answer_sv = entry.get("answer_sv", "")
#     sources   = entry.get("sources", [])

#     st.markdown(f"**Q: {question}**")

#     if mode == "dual" and answer_gv and answer_sv:
#         col_gv, col_sv = st.columns(2)
#         with col_gv:
#             st.markdown(
#                 '<div style="background:#e8f4f8;padding:1rem;border-radius:8px;'
#                 'border-left:4px solid #2d6a9f">'
#                 '<strong>👨‍🏫 Câu trả lời cho Giảng viên</strong></div>',
#                 unsafe_allow_html=True,
#             )
#             st.markdown(answer_gv)
#         with col_sv:
#             st.markdown(
#                 '<div style="background:#f0f8f0;padding:1rem;border-radius:8px;'
#                 'border-left:4px solid #28a745">'
#                 '<strong>🎓 Câu trả lời cho Sinh viên</strong></div>',
#                 unsafe_allow_html=True,
#             )
#             st.markdown(answer_sv)
#     elif answer_gv:
#         st.markdown(
#             '<div style="background:#e8f4f8;padding:1rem;border-radius:8px;'
#             'border-left:4px solid #2d6a9f">'
#             '<strong>👨‍🏫 Câu trả lời (Giảng viên)</strong></div>',
#             unsafe_allow_html=True,
#         )
#         st.markdown(answer_gv)
#     elif answer_sv:
#         st.markdown(
#             '<div style="background:#f0f8f0;padding:1rem;border-radius:8px;'
#             'border-left:4px solid #28a745">'
#             '<strong>🎓 Câu trả lời (Sinh viên)</strong></div>',
#             unsafe_allow_html=True,
#         )
#         st.markdown(answer_sv)

#     # Sources
#     if sources:
#         with st.expander(f"📌 Nguồn tham chiếu ({len(sources)} mục)", expanded=False):
#             for s in sources:
#                 section = s.get("section", "")
#                 label = {
#                     "clo": "CLO", "teaching_plan": "Kế hoạch giảng dạy",
#                     "assessment": "Đánh giá", "mapping": "Mapping",
#                     "rubric": "Rubric", "overview": "Tổng quan",
#                 }.get(section, section)
#                 st.markdown(f"**[{label}]** {s.get('content','')[:200]}...")


# # ============================================================
# # DISPLAY RESULTS
# # ============================================================

# if "result" in st.session_state:
#     result = st.session_state["result"]
#     clo_list = result.get("clo_list", [])
#     mapping_matrix = result.get("mapping_matrix", [])
#     teaching_plan = result.get("teaching_plan", [])
#     assessment_plan = result.get("assessment_plan", [])
#     confidence = result.get("confidence_score", 0)
#     errors   = result.get("errors", [])
#     warnings = result.get("warnings", [])

#     st.divider()
#     st.markdown("## 📊 Kết quả DCCT")

#     # Metrics overview
#     col1, col2, col3, col4 = st.columns(4)
#     with col1:
#         st.metric("🎯 Confidence Score", f"{confidence:.1f}%",
#                   delta="Tốt" if confidence >= 70 else "Cần cải thiện")
#     with col2:
#         st.metric("📚 Số CLO", len(clo_list))
#     with col3:
#         st.metric("📅 Số buổi học", len(teaching_plan))
#     with col4:
#         st.metric("📊 Cấu phần đánh giá", len(assessment_plan))

#     # Errors (hard failures) — shown as error boxes
#     if errors:
#         with st.expander(f"❌ Lỗi ({len(errors)})", expanded=True):
#             for e in errors:
#                 st.error(e)

#     # Warnings (soft notices) — shown as warning boxes
#     if warnings:
#         with st.expander(f"⚠️ Lưu ý ({len(warnings)})", expanded=False):
#             for w in warnings:
#                 st.warning(w)

#     # Tabs for different sections
#     tabs = st.tabs(["🎯 CLO", "🗺️ Mapping", "📅 Kế hoạch giảng dạy", "📊 Đánh giá", "📄 Export", "💬 Hỏi đáp ĐCCT"])

#     # ---- Tab 1: CLO ----
#     with tabs[0]:
#         st.markdown("### Chuẩn đầu ra học phần (CLO)")
#         if clo_list:
#             for clo in clo_list:
#                 with st.expander(f"**{clo['code']}** - {clo['description'][:60]}..."):
#                     col_a, col_b = st.columns(2)
#                     with col_a:
#                         st.markdown(f"**Mô tả đầy đủ:** {clo['description']}")
#                         st.markdown(f"**Động từ Bloom:** `{clo.get('bloom_verb', 'N/A')}`")
#                         st.markdown(f"**Mức Bloom:** {clo.get('bloom_level_name', 'N/A')}")
#                     with col_b:
#                         st.markdown(f"**PI liên quan:** {', '.join(clo.get('pi_codes', [])) or 'N/A'}")
#                         st.markdown(f"**Mức IRMA:** `{clo.get('mapping_level', 'N/A')}`")
#         else:
#             st.info("Chưa có CLO")

#     # ---- Tab 2: Mapping ----
#     with tabs[1]:
#         st.markdown("### Ma trận ánh xạ CLO - PI - PLO")
#         if mapping_matrix:
#             import pandas as pd
#             df_data = []
#             for m in mapping_matrix:
#                 df_data.append({
#                     "CLO": m.get("clo_code", ""),
#                     "PI": m.get("pi_code", ""),
#                     "PLO": m.get("plo_code", ""),
#                     "IRMA": m.get("irma_level", ""),
#                     "Bloom Level": m.get("bloom_level", ""),
#                 })
#             df = pd.DataFrame(df_data)
#             st.dataframe(df, use_container_width=True)
#         else:
#             st.info("Chưa có mapping")

#     # ---- Tab 3: Teaching Plan ----
#     with tabs[2]:
#         st.markdown("### Kế hoạch giảng dạy")
#         if teaching_plan:
#             import pandas as pd
#             plan_data = []
#             for s in teaching_plan:
#                 plan_data.append({
#                     "Buổi": s.get("no", ""),
#                     "Tuần": s.get("week", ""),
#                     "Loại": s.get("type", ""),
#                     "Nội dung": s.get("content", ""),
#                     "CLO": ", ".join(s.get("clo_codes", [])),
#                     "IRMA": s.get("irma_level", ""),
#                     "Hoạt động": s.get("activities", ""),
#                 })
#             df = pd.DataFrame(plan_data)
#             st.dataframe(df, use_container_width=True, height=400)
#         else:
#             st.info("Chưa có kế hoạch giảng dạy")

#     # ---- Tab 4: Assessment ----
#     with tabs[3]:
#         st.markdown("### Hệ thống đánh giá")
#         if assessment_plan:
#             for a in assessment_plan:
#                 with st.expander(
#                     f"**{a.get('code', '')}** - {a.get('name', '')} "
#                     f"({a.get('weight', 0) * 100:.0f}%)"
#                 ):
#                     st.markdown(f"**Mô tả:** {a.get('description', '')}")
#                     st.markdown(f"**Hình thức:** {a.get('format', '')}")
#                     st.markdown(f"**Tần suất:** {a.get('frequency', '')}")
#                     st.markdown(f"**CLO đánh giá:** {', '.join(a.get('clo_mapping', []))}")

#             # Pie chart trọng số
#             import pandas as pd

#             weight_data = {
#                 "Cấu phần": [a.get("code", "") for a in assessment_plan],
#                 "Trọng số": [a.get("weight", 0) * 100 for a in assessment_plan],
#             }
#             df_weight = pd.DataFrame(weight_data)
#             st.bar_chart(df_weight.set_index("Cấu phần"))

#         else:
#             st.info("Chưa có hệ thống đánh giá")

#     # ---- Tab 5: Export ----
#     with tabs[4]:
#         st.markdown("### Xuất file DCCT")

#         col_export1, col_export2 = st.columns(2)

#         with col_export1:
#             if st.button("📄 Xuất file Word (.docx)", type="primary", use_container_width=True):
#                 with st.spinner("Đang tạo file Word..."):
#                     loop = asyncio.new_event_loop()
#                     asyncio.set_event_loop(loop)
#                     try:
#                         from export.word_generator import export_node
#                         export_result = loop.run_until_complete(export_node(result))
#                         if export_result.get("export_ready"):
#                             filepath = export_result.get("export_path", "")
#                             st.success(f"✅ Đã xuất: {Path(filepath).name}")
#                             # Auto-index khi xuất thành công (nếu chưa index)
#                             _auto_index_dcct(result)
#                             with open(filepath, "rb") as f:
#                                 st.download_button(
#                                     "⬇️ Tải xuống DCCT.docx",
#                                     f.read(),
#                                     file_name=Path(filepath).name,
#                                     mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
#                                 )
#                         else:
#                             st.error("Lỗi xuất file. Xem logs để biết thêm chi tiết.")
#                     except Exception as e:
#                         st.error(f"Lỗi: {e}")
#                     finally:
#                         loop.close()

#         with col_export2:
#             if st.button("📋 Xuất JSON", use_container_width=True):
#                 import json
#                 final_data = result.get("final_dcct_data") or result
#                 json_str = json.dumps(final_data, ensure_ascii=False, indent=2)
#                 st.download_button(
#                     "⬇️ Tải xuống DCCT.json",
#                     json_str.encode("utf-8"),
#                     file_name=f"DCCT_{st.session_state.get('course_code', 'export')}.json",
#                     mime="application/json",
#                 )

#         # Nút index thủ công
#         st.divider()
#         qa_col1, qa_col2 = st.columns([2, 1])
#         with qa_col1:
#             indexed = st.session_state.get("qa_indexed", False)
#             status_icon = "✅" if indexed else "⭕"
#             st.markdown(f"**Trạng thái Q&A Knowledge Base:** {status_icon} "
#                         f"{'Đã sẵn sàng' if indexed else 'Chưa index'}")
#         with qa_col2:
#             if st.button("🔍 Index vào Q&A KB", use_container_width=True):
#                 info = _auto_index_dcct(result)
#                 if info:
#                     st.success(f"Đã index {info['chunks_indexed']} chunks!")

#         # Feedback section
#         st.divider()
#         st.markdown("### 💬 Phản hồi / Yêu cầu chỉnh sửa")
#         feedback = st.text_area(
#             "Nhập phản hồi để cải thiện DCCT:",
#             placeholder="VD: CLO3 chưa đủ mức độ thực hành, cần thêm bài TH...",
#             height=100,
#         )
#         if st.button("🔄 Cập nhật DCCT với phản hồi", use_container_width=True):
#             if feedback:
#                 st.info("💡 Tính năng revision đang trong quá trình phát triển. "
#                         "Hiện tại, vui lòng chỉnh sửa thông tin đầu vào và chạy lại.")
#             else:
#                 st.warning("Vui lòng nhập phản hồi trước khi cập nhật.")

#     # ---- Tab 6: Q&A ĐCCT ----
#     with tabs[5]:
#         _render_qa_tab(result)

# # ============================================================
# # FOOTER
# # ============================================================

# st.divider()
# st.markdown("""
# <div style="text-align: center; color: #888; font-size: 0.85em;">
#     🎓 OBE DCCT Agent v1.0 | Khoa CNTT - ĐH Đại Nam | 
#     Powered by LangGraph + Gemini/Claude
# </div>
# """, unsafe_allow_html=True)

import sys
import os
from pathlib import Path
import streamlit as st

# ============================================================
# ❗ BƯỚC 1: CẤU HÌNH TRANG (PHẢI LÀ LỆNH STREAMLIT ĐẦU TIÊN)
# ============================================================
st.set_page_config(page_title="LexAI - Trợ lý Pháp lý DNU", layout="wide")

# ============================================================
# 🛠️ BƯỚC 2: CẤU HÌNH ĐƯỜNG DẪN HỆ THỐNG
# ============================================================
current_dir = Path(__file__).parent.absolute()
root_path = current_dir.parent.absolute()

# Thêm thư mục gốc vào sys.path để import được run_multi_md_qa
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

import asyncio
import torch

# Thử import backend, nếu lỗi thì hiện thông báo qua giao diện
backend_loaded = False
try:
    from run_multi_md_qa import chunk_all_md, build_index, ask_with_smart_router
    backend_loaded = True
except ImportError as e:
    st.error(f"❌ Lỗi Import Backend: {e}")

# ============================================================
# 🎨 GIAO DIỆN LEXAI - CSS CUSTOM
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
    .stApp { background-color: #F9F7F2; }
    section[data-testid="stSidebar"] { background-color: #121212 !important; border-right: 1px solid #222; }
    .logo-text { color: #D4AF37; font-family: 'Playfair Display', serif; font-size: 2.2rem; margin-bottom: 0; }
    .logo-subtext { color: #888; font-size: 0.7rem; letter-spacing: 2px; text-transform: uppercase; }
    .stButton>button { width: 100%; background-color: transparent !important; color: #AAA !important; border: none !important; text-align: left !important; padding: 12px 20px !important; border-radius: 10px !important; }
    .stButton>button:hover { color: #D4AF37 !important; background-color: #1E1E1E !important; }
    .active-field { color: #FFF !important; background-color: #1E1E1E !important; border-left: 5px solid #D4AF37 !important; }
    .user-msg { background-color: #121212; color: white; padding: 15px 20px; border-radius: 15px 15px 0 15px; margin: 10px 0 10px auto; max-width: 80%; }
    .bot-msg { background-color: white; color: #121212; padding: 15px 20px; border-radius: 15px 15px 15px 0; border: 1px solid #E0E0E0; margin: 10px auto 10px 0; max-width: 85%; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# ============================================================
# ⚙️ HỆ THỐNG TRUY XUẤT (BACKEND)
# ============================================================
BASE_DATA_PATH = os.path.join(root_path, "data", "TaiLieu_Chatbot")

FIELD_CONFIG = {
    "💼 Hợp đồng Lao động": "HD_Laodong",
    "🤝 Hợp đồng Thương mại": "HD_Thuongmai",
    "🏢 Luật Doanh nghiệp": "Luat_DN",
    "📝 Chính sách HR": "CS_Hr",
    "💰 Thuế & Tài chính": "Thue_Taichinh",
    "⚖️ Tranh chấp & Xử lý": "Tranhchap_xuli"
}

if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_field" not in st.session_state:
    st.session_state.current_field = list(FIELD_CONFIG.keys())[0]
if "vs_cache" not in st.session_state:
    st.session_state.vs_cache = {}

def get_vector_store(field_name):
    if not backend_loaded: return None
    folder = FIELD_CONFIG[field_name]
    if folder not in st.session_state.vs_cache:
        target_dir = os.path.join(BASE_DATA_PATH, folder)
        if not os.path.exists(target_dir):
            st.warning(f"📁 Không tìm thấy dữ liệu tại: {target_dir}")
            return None
        with st.status(f"📚 Đang nạp kiến thức {field_name}...", expanded=False):
            docs = chunk_all_md(target_dir)
            if docs:
                vs = build_index(docs)
                st.session_state.vs_cache[folder] = vs
            else:
                return None
    return st.session_state.vs_cache[folder]

# ============================================================
# 🖥️ GIAO DIỆN NGƯỜI DÙNG
# ============================================================
with st.sidebar:
    st.markdown('<div style="padding-left:10px;"><p class="logo-text">LexAI</p><p class="logo-subtext">DNU Intelligent Assistant</p></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    for field in FIELD_CONFIG.keys():
        is_active = "active-field" if st.session_state.current_field == field else ""
        if st.button(field, key=f"btn_{field}"):
            st.session_state.current_field = field
            st.session_state.messages = []
            st.rerun()
    
    st.divider()
    st.caption(f"📍 Root: `{root_path.name}`")
    st.caption("🚀 Model: Qwen-7B GPU")

# Layout Chat
st.markdown(f"### {st.session_state.current_field}")
current_vs = get_vector_store(st.session_state.current_field)

for msg in st.session_state.messages:
    cls = "user-msg" if msg["role"] == "user" else "bot-msg"
    icon = "👤" if msg["role"] == "user" else "⚖️"
    st.markdown(f'<div class="{cls}">{icon} {msg["content"]}</div>', unsafe_allow_html=True)

if prompt := st.chat_input("Hỏi LexAI về các quy định pháp lý..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# Xử lý Logic sau khi Rerun
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    user_query = st.session_state.messages[-1]["content"]
    if current_vs:
        with st.spinner("LexAI đang tra cứu cơ sở dữ liệu..."):
            try:
                answer, sources, s_type = asyncio.run(ask_with_smart_router(user_query, current_vs))
                full_res = f"{answer}\n\n**Nguồn:** {s_type}"
                st.session_state.messages.append({"role": "assistant", "content": full_res})
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi xử lý AI: {str(e)}")
    else:
        st.error("Hệ thống chưa sẵn sàng hoặc dữ liệu lĩnh vực này đang trống.")

torch.cuda.empty_cache()
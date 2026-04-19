"""
Streamlit Frontend - Giao diện người dùng cho OBE DCCT Agent
"""

import asyncio
import os
import sys
from pathlib import Path

# Đảm bảo có thể import từ project root
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="OBE DCCT Agent - ĐH Đại Nam",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# STYLES
# ============================================================

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .section-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2d6a9f;
        margin: 0.5rem 0;
    }
    .clo-item {
        background: white;
        padding: 0.7rem;
        border-radius: 6px;
        border: 1px solid #dee2e6;
        margin: 0.3rem 0;
    }
    .confidence-high { color: #28a745; font-weight: bold; font-size: 1.2em; }
    .confidence-mid { color: #ffc107; font-weight: bold; font-size: 1.2em; }
    .confidence-low { color: #dc3545; font-weight: bold; font-size: 1.2em; }
    .metric-box {
        text-align: center;
        padding: 1rem;
        background: #e8f4f8;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("### 🎓 DNU - Khoa CNTT")
    st.markdown("### ⚙️ Cài đặt Agent")

    st.markdown("**API Keys:**")
    google_key = st.text_input("Google API Key", type="password",
                               value=os.getenv("GOOGLE_API_KEY", ""),
                               help="Gemini API key từ Google AI Studio")
    anthropic_key = st.text_input("Anthropic API Key", type="password",
                                  value=os.getenv("ANTHROPIC_API_KEY", ""),
                                  help="Claude API key từ Anthropic Console")

    if google_key:
        os.environ["GOOGLE_API_KEY"] = google_key
    if anthropic_key:
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key

    st.divider()
    st.markdown("**Thông tin:**")
    st.caption("🤖 LangGraph Agentic Workflow")
    st.caption("📚 OBE / AUN-QA Standard")
    st.caption("🏫 Khoa CNTT - ĐH Đại Nam")

# ============================================================
# MAIN HEADER
# ============================================================

st.markdown("""
<div class="main-header">
    <h1 style="margin:0">🎓 OBE DCCT Agent</h1>
    <p style="margin:0.3rem 0 0 0; opacity:0.9">
        Hệ thống tự động tạo Đề cương Chi tiết Học phần theo chuẩn Outcome-Based Education
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# INPUT FORM
# ============================================================

st.markdown("## 📝 Nhập thông tin học phần")

with st.form("course_input_form", clear_on_submit=False):
    col1, col2 = st.columns([1, 2])

    with col1:
        course_code = st.text_input(
            "Mã học phần *",
            placeholder="VD: CSC4012",
            help="Mã học phần theo quy định của trường",
        )
        credits = st.selectbox(
            "Số tín chỉ *",
            options=["2", "3", "4", "5"],
            index=1,
        )

    with col2:
        course_name = st.text_input(
            "Tên học phần *",
            placeholder="VD: Trí tuệ nhân tạo ứng dụng",
        )
        course_type = st.selectbox(
            "Loại học phần",
            options=["Lý thuyết + Thực hành", "Lý thuyết", "Thực hành"],
            index=0,
        )

    summary = st.text_area(
        "Mô tả / Tóm tắt học phần *",
        placeholder="Nhập mô tả ngắn về nội dung, mục tiêu học phần...",
        height=120,
    )

    outline = st.text_area(
        "Sườn nội dung buổi học (khuyến nghị mạnh)",
            placeholder="Dán sườn nội dung các buổi học (outline), hoặc đề cương cũ...",
            height=100,
    )

    col3, col4 = st.columns(2)
    with col3:
        submitted = st.form_submit_button(
            "🚀 Tạo DCCT tự động",
            type="primary",
            use_container_width=True,
        )
    with col4:
        demo_btn = st.form_submit_button(
            "🎯 Chạy Demo",
            use_container_width=True,
        )

# ============================================================
# RUN AGENT
# ============================================================

def run_agent_sync(course_code, course_name, credits, summary, outline=None):
    """Wrapper đồng bộ để chạy async agent trong Streamlit."""
    from config import validate_config

    if not validate_config():
        return None, "Cần cấu hình ít nhất một API Key (Google hoặc Anthropic)"

    from graph import get_graph

    initial_state = {
        "user_input": f"{course_code} - {course_name}\n{summary}",
        "course_code": course_code,
        "course_name": course_name,
        "credits": credits,
        "summary": summary,
        "outline": outline,
        "extracted_info": {},
        "clo_list": [],
        "mapping_matrix": [],
        "teaching_plan": [],
        "assessment_plan": [],
        "rubrics": {},
        "messages": [],
        "current_step": "understand",
        "confidence_score": 0.0,
        "critic_feedback": [],
        "retry_counts": {},
        "preview_data": None,
        "needs_human_input": False,
        "human_feedback": None,
        "final_dcct_data": None,
        "export_ready": False,
        "errors": [],
        "warnings": [],
    }

    graph = get_graph()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            graph.ainvoke(initial_state, config={"configurable": {"thread_id": "1"}})
        )
        return result, None
    except Exception as e:
        return None, str(e)
    finally:
        loop.close()


if submitted or demo_btn:
    # Demo values nếu form trống
    if demo_btn:
        course_code = course_code or "CSC4012"
        course_name = course_name or "Trí tuệ nhân tạo ứng dụng"
        credits = credits or "3"
        summary = summary or (
            "Học phần giới thiệu các khái niệm và ứng dụng thực tế của Trí tuệ nhân tạo. "
            "Sinh viên học về machine learning, deep learning, xử lý ngôn ngữ tự nhiên và "
            "computer vision, với các bài thực hành sử dụng Python và các thư viện AI phổ biến."
        )

    # Validate input
    if not course_code or not course_name or not summary:
        st.error("⚠️ Vui lòng nhập đầy đủ: Mã học phần, Tên học phần và Mô tả!")
    else:
        # Progress tracking
        progress_container = st.empty()
        status_container = st.empty()

        with st.spinner("🤖 AI Agent đang xử lý..."):
            progress_bar = progress_container.progress(0, "Đang khởi động...")

            steps = [
                "Khởi tạo RAG system...",
                "Phân tích học phần và sinh CLO...",
                "Ánh xạ CLO → PI → PLO...",
                "Xây dựng kế hoạch giảng dạy...",
                "Thiết kế hệ thống đánh giá...",
                "Kiểm chứng và hoàn thiện...",
            ]

            # Simulate progress (thực tế sẽ update qua callback)
            import time
            for i, step in enumerate(steps):
                progress_bar.progress((i + 1) / len(steps), step)
                time.sleep(0.2)

            result, error = run_agent_sync(
                course_code, course_name, credits, summary,
                outline if outline else None
            )

        progress_container.empty()

        if error:
            st.error(f"❌ Lỗi: {error}")
        elif result:
            st.success("✅ Đã tạo DCCT thành công!")
            st.session_state["result"] = result
            st.session_state["course_code"] = course_code
            st.session_state["course_name"] = course_name


# ============================================================
# DISPLAY RESULTS
# ============================================================

if "result" in st.session_state:
    result = st.session_state["result"]
    clo_list = result.get("clo_list", [])
    mapping_matrix = result.get("mapping_matrix", [])
    teaching_plan = result.get("teaching_plan", [])
    assessment_plan = result.get("assessment_plan", [])
    confidence = result.get("confidence_score", 0)
    errors = result.get("errors", [])

    st.divider()
    st.markdown("## 📊 Kết quả DCCT")

    # Metrics overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🎯 Confidence Score", f"{confidence:.1f}%",
                  delta="Tốt" if confidence >= 70 else "Cần cải thiện")
    with col2:
        st.metric("📚 Số CLO", len(clo_list))
    with col3:
        st.metric("📅 Số buổi học", len(teaching_plan))
    with col4:
        st.metric("📊 Cấu phần đánh giá", len(assessment_plan))

    # Errors/warnings
    if errors:
        with st.expander(f"⚠️ Cảnh báo ({len(errors)})", expanded=False):
            for e in errors:
                st.warning(e)

    # Tabs for different sections
    tabs = st.tabs(["🎯 CLO", "🗺️ Mapping", "📅 Kế hoạch giảng dạy", "📊 Đánh giá", "📄 Export", "💬 Hỏi đáp ĐCCT"])

    # ---- Tab 1: CLO ----
    with tabs[0]:
        st.markdown("### Chuẩn đầu ra học phần (CLO)")
        if clo_list:
            for clo in clo_list:
                with st.expander(f"**{clo['code']}** - {clo['description'][:60]}..."):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"**Mô tả đầy đủ:** {clo['description']}")
                        st.markdown(f"**Động từ Bloom:** `{clo.get('bloom_verb', 'N/A')}`")
                        st.markdown(f"**Mức Bloom:** {clo.get('bloom_level_name', 'N/A')}")
                    with col_b:
                        st.markdown(f"**PI liên quan:** {', '.join(clo.get('pi_codes', [])) or 'N/A'}")
                        st.markdown(f"**Mức IRMA:** `{clo.get('mapping_level', 'N/A')}`")
        else:
            st.info("Chưa có CLO")

    # ---- Tab 2: Mapping ----
    with tabs[1]:
        st.markdown("### Ma trận ánh xạ CLO - PI - PLO")
        if mapping_matrix:
            import pandas as pd
            df_data = []
            for m in mapping_matrix:
                df_data.append({
                    "CLO": m.get("clo_code", ""),
                    "PI": m.get("pi_code", ""),
                    "PLO": m.get("plo_code", ""),
                    "IRMA": m.get("irma_level", ""),
                    "Bloom Level": m.get("bloom_level", ""),
                })
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Chưa có mapping")

    # ---- Tab 3: Teaching Plan ----
    with tabs[2]:
        st.markdown("### Kế hoạch giảng dạy")
        if teaching_plan:
            import pandas as pd
            plan_data = []
            for s in teaching_plan:
                plan_data.append({
                    "Buổi": s.get("no", ""),
                    "Tuần": s.get("week", ""),
                    "Loại": s.get("type", ""),
                    "Nội dung": s.get("content", ""),
                    "CLO": ", ".join(s.get("clo_codes", [])),
                    "IRMA": s.get("irma_level", ""),
                    "Hoạt động": s.get("activities", ""),
                })
            df = pd.DataFrame(plan_data)
            st.dataframe(df, use_container_width=True, height=400)
        else:
            st.info("Chưa có kế hoạch giảng dạy")

    # ---- Tab 4: Assessment ----
    with tabs[3]:
        st.markdown("### Hệ thống đánh giá")
        if assessment_plan:
            for a in assessment_plan:
                with st.expander(
                    f"**{a.get('code', '')}** - {a.get('name', '')} "
                    f"({a.get('weight', 0) * 100:.0f}%)"
                ):
                    st.markdown(f"**Mô tả:** {a.get('description', '')}")
                    st.markdown(f"**Hình thức:** {a.get('format', '')}")
                    st.markdown(f"**Tần suất:** {a.get('frequency', '')}")
                    st.markdown(f"**CLO đánh giá:** {', '.join(a.get('clo_mapping', []))}")

            # Pie chart trọng số
            import pandas as pd

            weight_data = {
                "Cấu phần": [a.get("code", "") for a in assessment_plan],
                "Trọng số": [a.get("weight", 0) * 100 for a in assessment_plan],
            }
            df_weight = pd.DataFrame(weight_data)
            st.bar_chart(df_weight.set_index("Cấu phần"))

        else:
            st.info("Chưa có hệ thống đánh giá")

    # ---- Tab 5: Export ----
    with tabs[4]:
        st.markdown("### Xuất file DCCT")

        col_export1, col_export2 = st.columns(2)

        with col_export1:
            if st.button("📄 Xuất file Word (.docx)", type="primary", use_container_width=True):
                with st.spinner("Đang tạo file Word..."):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        from export.word_generator import export_node
                        export_result = loop.run_until_complete(export_node(result))
                        if export_result.get("export_ready"):
                            filepath = export_result.get("export_path", "")
                            st.success(f"✅ Đã xuất: {Path(filepath).name}")
                            # Auto-index khi xuất thành công (nếu chưa index)
                            _auto_index_dcct(result)
                            with open(filepath, "rb") as f:
                                st.download_button(
                                    "⬇️ Tải xuống DCCT.docx",
                                    f.read(),
                                    file_name=Path(filepath).name,
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                )
                        else:
                            st.error("Lỗi xuất file. Xem logs để biết thêm chi tiết.")
                    except Exception as e:
                        st.error(f"Lỗi: {e}")
                    finally:
                        loop.close()

        with col_export2:
            if st.button("📋 Xuất JSON", use_container_width=True):
                import json
                final_data = result.get("final_dcct_data") or result
                json_str = json.dumps(final_data, ensure_ascii=False, indent=2)
                st.download_button(
                    "⬇️ Tải xuống DCCT.json",
                    json_str.encode("utf-8"),
                    file_name=f"DCCT_{st.session_state.get('course_code', 'export')}.json",
                    mime="application/json",
                )

        # Nút index thủ công
        st.divider()
        qa_col1, qa_col2 = st.columns([2, 1])
        with qa_col1:
            indexed = st.session_state.get("qa_indexed", False)
            status_icon = "✅" if indexed else "⭕"
            st.markdown(f"**Trạng thái Q&A Knowledge Base:** {status_icon} "
                        f"{'Đã sẵn sàng' if indexed else 'Chưa index'}")
        with qa_col2:
            if st.button("🔍 Index vào Q&A KB", use_container_width=True):
                info = _auto_index_dcct(result)
                if info:
                    st.success(f"Đã index {info['chunks_indexed']} chunks!")

        # Feedback section
        st.divider()
        st.markdown("### 💬 Phản hồi / Yêu cầu chỉnh sửa")
        feedback = st.text_area(
            "Nhập phản hồi để cải thiện DCCT:",
            placeholder="VD: CLO3 chưa đủ mức độ thực hành, cần thêm bài TH...",
            height=100,
        )
        if st.button("🔄 Cập nhật DCCT với phản hồi", use_container_width=True):
            if feedback:
                st.info("💡 Tính năng revision đang trong quá trình phát triển. "
                        "Hiện tại, vui lòng chỉnh sửa thông tin đầu vào và chạy lại.")
            else:
                st.warning("Vui lòng nhập phản hồi trước khi cập nhật.")

    # ---- Tab 6: Q&A ĐCCT ----
    with tabs[5]:
        _render_qa_tab(result)

# ============================================================
# Q&A HELPER FUNCTIONS
# ============================================================

def _auto_index_dcct(state: dict) -> dict:
    """Index ĐCCT vào knowledge base, lưu trạng thái vào session."""
    try:
        from agents.qa_agent import index_dcct_from_state
        course_code = state.get("course_code", "UNKNOWN")
        info = index_dcct_from_state(course_code, state)
        st.session_state["qa_indexed"] = True
        st.session_state["qa_course_code"] = course_code
        st.session_state["qa_chunks_count"] = info["chunks_indexed"]
        return info
    except Exception as e:
        st.session_state["qa_indexed"] = False
        return {}


def _render_qa_tab(result: dict):
    """Render toàn bộ giao diện Q&A trong tab."""
    from agents.qa_agent import (
        ask_dcct_sync,
        ask_dcct_dual_sync,
        get_suggested_questions,
        get_indexed_courses,
    )

    course_code = result.get("course_code", "")
    course_name = result.get("course_name", "")

    st.markdown("## 💬 Hỏi đáp về Đề cương Chi tiết Học phần")
    st.caption(
        "Đặt câu hỏi về ĐCCT — hệ thống sẽ trả lời theo vai trò Giảng viên hoặc Sinh viên."
    )

    # ── Auto-index nếu chưa có ────────────────────────────────────────────────
    if not st.session_state.get("qa_indexed") or \
       st.session_state.get("qa_course_code") != course_code:
        with st.spinner("Đang chuẩn bị knowledge base Q&A..."):
            info = _auto_index_dcct(result)
        if info:
            st.success(
                f"✅ Knowledge base sẵn sàng: {info['chunks_indexed']} chunks "
                f"({info['clo_count']} CLO, {info['session_count']} buổi học)"
            )

    # ── Cài đặt Q&A ──────────────────────────────────────────────────────────
    st.markdown("---")
    qa_cfg_col1, qa_cfg_col2 = st.columns([1, 2])

    with qa_cfg_col1:
        qa_mode = st.radio(
            "Chế độ trả lời",
            options=["dual", "sv", "gv"],
            format_func=lambda x: {
                "dual": "🔀 Đầu ra kép (GV + SV)",
                "sv":   "🎓 Sinh viên",
                "gv":   "👨‍🏫 Giảng viên",
            }[x],
            horizontal=False,
            key="qa_mode",
        )

    with qa_cfg_col2:
        # Câu hỏi gợi ý
        suggest_role = "gv" if qa_mode == "gv" else "sv"
        suggested = get_suggested_questions(course_code, suggest_role)
        st.markdown("**Câu hỏi gợi ý:**")
        for i, sq in enumerate(suggested[:3]):
            if st.button(sq, key=f"sq_{i}", use_container_width=True):
                st.session_state["qa_input_prefill"] = sq

    # ── Input câu hỏi ─────────────────────────────────────────────────────────
    prefill = st.session_state.pop("qa_input_prefill", "")
    question = st.text_input(
        "Nhập câu hỏi của bạn",
        value=prefill,
        placeholder="VD: Điểm học phần được tính như thế nào?",
        key="qa_question_input",
    )

    ask_col1, ask_col2 = st.columns([3, 1])
    with ask_col1:
        ask_btn = st.button(
            "🔍 Hỏi",
            type="primary",
            use_container_width=True,
            disabled=not question.strip(),
        )
    with ask_col2:
        clear_btn = st.button(
            "🗑️ Xóa lịch sử",
            use_container_width=True,
        )

    if clear_btn:
        st.session_state["qa_history"] = []
        st.rerun()

    # ── Xử lý câu hỏi ─────────────────────────────────────────────────────────
    if ask_btn and question.strip():
        history = st.session_state.get("qa_history", [])

        with st.spinner("🤖 Đang tìm kiếm và soạn câu trả lời..."):
            try:
                if qa_mode == "dual":
                    qa_result = ask_dcct_dual_sync(course_code, question, history)
                    answer_gv = qa_result.get("answer_gv", "")
                    answer_sv = qa_result.get("answer_sv", "")
                    sources   = qa_result.get("sources", [])
                    warning   = qa_result.get("warning", "")
                else:
                    qa_result = ask_dcct_sync(course_code, question, qa_mode, history)
                    answer_gv = qa_result.get("answer", "") if qa_mode == "gv" else ""
                    answer_sv = qa_result.get("answer", "") if qa_mode == "sv" else ""
                    sources   = qa_result.get("sources", [])
                    warning   = qa_result.get("warning", "")

                if warning and not answer_gv and not answer_sv:
                    st.error(f"⚠️ {warning}")
                else:
                    # Lưu vào lịch sử
                    entry = {
                        "question":  question,
                        "answer_gv": answer_gv,
                        "answer_sv": answer_sv,
                        "mode":      qa_mode,
                        "sources":   sources,
                    }
                    history.append({"role": "user",      "content": question})
                    history.append({"role": "assistant", "content": answer_gv or answer_sv})
                    st.session_state["qa_history"] = history[-10:]  # giữ 5 lượt gần nhất

                    # Hiển thị câu trả lời mới nhất ngay
                    _display_qa_answer(question, entry, qa_mode)

            except Exception as e:
                st.error(f"Lỗi khi xử lý câu hỏi: {e}")

    # ── Lịch sử Q&A ───────────────────────────────────────────────────────────
    history_entries = [
        e for e in st.session_state.get("qa_history", []) if e.get("role") == "user"
    ]
    if len(history_entries) > 1:  # Hiển thị lịch sử nếu có hơn 1 lượt hỏi
        st.markdown("---")
        st.markdown("#### 📜 Lịch sử hỏi đáp")
        # Rebuild full entries from session
        full_history = st.session_state.get("_qa_full_history", [])
        for i, entry in enumerate(reversed(full_history[:-1])):  # bỏ lượt gần nhất đã hiển thị
            with st.expander(f"Q{len(full_history) - i - 1}: {entry['question'][:80]}"):
                _display_qa_answer(entry["question"], entry, entry.get("mode", "sv"))


def _display_qa_answer(question: str, entry: dict, mode: str):
    """Render một câu trả lời Q&A."""
    answer_gv = entry.get("answer_gv", "")
    answer_sv = entry.get("answer_sv", "")
    sources   = entry.get("sources", [])

    st.markdown(f"**Q: {question}**")

    if mode == "dual" and answer_gv and answer_sv:
        col_gv, col_sv = st.columns(2)
        with col_gv:
            st.markdown(
                '<div style="background:#e8f4f8;padding:1rem;border-radius:8px;'
                'border-left:4px solid #2d6a9f">'
                '<strong>👨‍🏫 Câu trả lời cho Giảng viên</strong></div>',
                unsafe_allow_html=True,
            )
            st.markdown(answer_gv)
        with col_sv:
            st.markdown(
                '<div style="background:#f0f8f0;padding:1rem;border-radius:8px;'
                'border-left:4px solid #28a745">'
                '<strong>🎓 Câu trả lời cho Sinh viên</strong></div>',
                unsafe_allow_html=True,
            )
            st.markdown(answer_sv)
    elif answer_gv:
        st.markdown(
            '<div style="background:#e8f4f8;padding:1rem;border-radius:8px;'
            'border-left:4px solid #2d6a9f">'
            '<strong>👨‍🏫 Câu trả lời (Giảng viên)</strong></div>',
            unsafe_allow_html=True,
        )
        st.markdown(answer_gv)
    elif answer_sv:
        st.markdown(
            '<div style="background:#f0f8f0;padding:1rem;border-radius:8px;'
            'border-left:4px solid #28a745">'
            '<strong>🎓 Câu trả lời (Sinh viên)</strong></div>',
            unsafe_allow_html=True,
        )
        st.markdown(answer_sv)

    # Sources
    if sources:
        with st.expander(f"📌 Nguồn tham chiếu ({len(sources)} mục)", expanded=False):
            for s in sources:
                section = s.get("section", "")
                label = {
                    "clo": "CLO", "teaching_plan": "Kế hoạch giảng dạy",
                    "assessment": "Đánh giá", "mapping": "Mapping",
                    "rubric": "Rubric", "overview": "Tổng quan",
                }.get(section, section)
                st.markdown(f"**[{label}]** {s.get('content','')[:200]}...")


# ============================================================
# FOOTER
# ============================================================

st.divider()
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.85em;">
    🎓 OBE DCCT Agent v1.0 | Khoa CNTT - ĐH Đà Nẵng | 
    Powered by LangGraph + Gemini/Claude
</div>
""", unsafe_allow_html=True)

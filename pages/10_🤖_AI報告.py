import streamlit as st
from datetime import date, timedelta
from io import BytesIO

from firebase_utils import db
from nav_utils import apply_global_css
from ai_report import (
    prepare_data_for_ai,
    generate_report_with_gemini,
    export_report_to_docx,
    extract_section,
)
from settings_utils import get_user_profile

# ── 頁面設定 ──────────────────────────────────────────────
st.set_page_config(page_title="AI 報告", page_icon="🤖", layout="wide")
apply_global_css()

st.title("🤖 AI 健康報告")

# ── 登入檢查 ──────────────────────────────────────────────
if "user_id" not in st.session_state:
    st.error("請先登入")
    st.stop()

user_id = st.session_state["user_id"]
user_profile = get_user_profile(user_id)
user_name = user_profile.get("name", "使用者") if user_profile else "使用者"

# ── 日期範圍選擇 ──────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input(
        "開始日期",
        value=date.today() - timedelta(days=90),
        max_value=date.today(),
        key="report_start_date"
    )

with col2:
    end_date = st.date_input(
        "結束日期",
        value=date.today(),
        min_value=start_date,
        max_value=date.today(),
        key="report_end_date"
    )

if start_date >= end_date:
    st.error("開始日期必須早於結束日期")
    st.stop()

# ── 模組選擇 ──────────────────────────────────────────────
st.subheader("選擇要納入報告的模組")

col1, col2, col3, col4 = st.columns(4)

with col1:
    include_drug = st.checkbox("用藥", value=True)
    include_heartrate = st.checkbox("血壓", value=True)
    include_sugar = st.checkbox("血糖", value=True)

with col2:
    include_temp = st.checkbox("體溫", value=True)
    include_weight = st.checkbox("體重", value=True)
    include_symptom = st.checkbox("症狀", value=True)

with col3:
    include_sleep = st.checkbox("睡眠", value=True)
    include_life = st.checkbox("生活", value=True)

selected_modules = []
if include_drug:
    selected_modules.append("drug")
if include_heartrate:
    selected_modules.append("heartrate")
if include_sugar:
    selected_modules.append("sugar")
if include_temp:
    selected_modules.append("temp")
if include_weight:
    selected_modules.append("weight")
if include_symptom:
    selected_modules.append("symptom")
if include_sleep:
    selected_modules.append("sleep")
if include_life:
    selected_modules.append("life")

if not selected_modules:
    st.warning("請至少選擇一個模組")
    st.stop()

# ── 報告生成 ──────────────────────────────────────────────
if st.button("生成報告", type="primary"):
    with st.spinner("正在準備資料..."):
        data_context = prepare_data_for_ai(user_id, start_date, end_date, selected_modules)

    with st.spinner("正在生成報告..."):
        full_report = generate_report_with_gemini(user_name, data_context, start_date, end_date)

    # 儲存到 session state
    st.session_state["full_report"] = full_report
    st.session_state["report_generated"] = True

# ── 報告展示 ──────────────────────────────────────────────
if st.session_state.get("report_generated", False):
    full_report = st.session_state.get("full_report", "")

    # 提取網頁顯示部分（跨週關聯分析 + 整體觀察）
    cross_analysis = extract_section(full_report, "跨週關聯分析")
    overall = extract_section(full_report, "整體觀察")

    # 網頁顯示：只顯示跨週關聯分析和整體觀察
    st.markdown("---")
    st.markdown("## 📋 報告摘要")

    if cross_analysis:
        st.markdown(cross_analysis)

    if overall:
        # 整體觀察標題加粗
        overall_lines = overall.split("\n")
        formatted_overall = []
        for line in overall_lines:
            if line.startswith("## 整體觀察"):
                formatted_overall.append(f"**{line}**")
            else:
                formatted_overall.append(line)
        st.markdown("\n".join(formatted_overall))

    # ── Word 檔下載 ──────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📥 下載完整報告")

    docx_buffer = export_report_to_docx(full_report, user_name, start_date, end_date)
    st.download_button(
        label="下載 Word 報告",
        data=docx_buffer,
        file_name=f"健康報告_{user_name}_{start_date}_{end_date}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    # 可選：顯示完整報告（用 expander 隱藏）
    with st.expander("檢視完整報告（包含各週摘要）"):
        st.markdown(full_report)

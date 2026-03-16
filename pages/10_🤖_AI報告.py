import streamlit as st
from datetime import date, timedelta
from ai_report import prepare_data_for_ai, generate_report_with_gemini, export_report_to_docx
from settings_utils import get_enabled_modules, MODULE_NAMES

st.set_page_config(page_title="AI 健康報告", page_icon="🤖", layout="wide")

# 檢查登入狀態
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ 請先登入")
    st.stop()

user_id = st.session_state.user_id
user_name = st.session_state.user_name

st.title("🤖 AI 健康報告")
st.caption("根據您的健康紀錄，由 AI 產生供醫師參考的完整報告")

# ── 時間範圍 ──
st.subheader("📅 選擇紀錄期間")
today = date.today()
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("開始日期", value=today - timedelta(days=90))
with col2:
    end_date = st.date_input("結束日期", value=today)

if start_date > end_date:
    st.error("開始日期不能晚於結束日期")
    st.stop()

# ── 選擇模組 ──
st.subheader("📋 選擇要納入的項目")
enabled_modules = get_enabled_modules(user_id)

MODULE_EMOJI = {
    "heartrate": "❤️",
    "weight": "⚖️",
    "sugar": "🩸",
    "temp": "🌡️",
    "drug": "💊",
    "life": "🏃",
    "symptom": "🤧",
    "sleep": "😴",
}

if not enabled_modules:
    st.info("尚未啟用任何模組，請至設定頁面開啟。")
    st.stop()

cols = st.columns(4)
selected_modules = []
for i, mod in enumerate(enabled_modules):
    name = MODULE_NAMES.get(mod, mod)
    emoji = MODULE_EMOJI.get(mod, "📝")
    with cols[i % 4]:
        if st.checkbox(f"{emoji} {name}", value=True, key=f"mod_{mod}"):
            selected_modules.append(mod)

st.markdown("---")

# ── 產生報告 ──
if st.button("🤖 產生 AI 報告", type="primary", use_container_width=True):
    if not selected_modules:
        st.warning("請至少選擇一個項目")
    else:
        with st.spinner("正在整理資料並產生報告，請稍候..."):
            try:
                # 準備資料
                data_context = prepare_data_for_ai(user_id, start_date, end_date, selected_modules)

                # 呼叫 Gemini
                report_text = generate_report_with_gemini(user_name, data_context, start_date, end_date)

                st.session_state["ai_report_text"] = report_text
                st.session_state["ai_report_start"] = start_date
                st.session_state["ai_report_end"] = end_date

            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"產生報告時發生錯誤：{e}")

# ── 顯示報告 ──
if "ai_report_text" in st.session_state:
    report_text = st.session_state["ai_report_text"]
    report_start = st.session_state["ai_report_start"]
    report_end = st.session_state["ai_report_end"]

    st.markdown("---")
    st.subheader("📄 報告預覽")
    st.markdown(report_text)

    st.markdown("---")

    # 產生 Word 檔下載
    docx_buffer = export_report_to_docx(report_text, user_name, report_start, report_end)
    filename = f"{user_name}_健康報告_{report_start.strftime('%Y%m%d')}_{report_end.strftime('%Y%m%d')}.docx"

    st.download_button(
        label="⬇️ 下載 Word 報告",
        data=docx_buffer,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
    )

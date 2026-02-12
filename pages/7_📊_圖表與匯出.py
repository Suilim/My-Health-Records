import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from io import BytesIO
from export_records import DATA_TYPES, get_user_records
from settings_utils import get_enabled_modules, MODULE_PATHS, MODULE_NAMES
from plot_utils import (
    CHART_COLUMNS,
    records_to_dataframe,
    get_summary_stats,
    get_drug_compliance_table,
    get_life_emotion_counts,
)

st.set_page_config(
    page_title="圖表與匯出",
    page_icon="📊",
    layout="wide"
)

# 檢查登入狀態
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ 請先登入")
    st.stop()

user_id = st.session_state.user_id
user_name = st.session_state.user_name

st.title("📊 健康趨勢")
st.write(f"**{user_name}** 的健康數據")
st.markdown("---")

# ── 時間範圍選擇 ──
mode = st.radio("時間範圍", ["月份", "自訂範圍"], horizontal=True)

if mode == "月份":
    col1, col2 = st.columns(2)
    now = datetime.now()
    with col1:
        year = st.selectbox("年份", range(now.year, now.year - 5, -1), index=0)
    with col2:
        month = st.selectbox("月份", range(1, 13), index=now.month - 1)
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
else:
    col1, col2 = st.columns(2)
    now = datetime.now()
    with col1:
        start_date = st.date_input("開始日期", value=date(now.year, now.month, 1))
    with col2:
        end_date = st.date_input("結束日期", value=now.date())

st.markdown("---")

# ── 取得啟用模組 ──
enabled_modules = get_enabled_modules(user_id)

if not enabled_modules:
    st.info("尚未啟用任何模組，請至設定頁面開啟。")
    st.stop()

# 模組 emoji 對照
MODULE_EMOJI = {
    "heartrate": "❤️",
    "weight": "⚖️",
    "sugar": "🩸",
    "temp": "🌡️",
    "drug": "💊",
    "life": "🏃",
}

# ── 所有模組圖表堆疊顯示 ──
with st.spinner("載入中..."):
    for mod_key in enabled_modules:
        firebase_node = MODULE_PATHS.get(mod_key)
        if not firebase_node:
            continue

        emoji = MODULE_EMOJI.get(mod_key, "📝")
        name = MODULE_NAMES.get(mod_key, mod_key)

        # 取得記錄
        records = get_user_records(user_id, firebase_node, start_date, end_date)

        if not records:
            st.subheader(f"{emoji} {name}")
            st.info(f"此期間無{name}紀錄")
            st.markdown("---")
            continue

        chart_config = CHART_COLUMNS.get(firebase_node, {})
        chart_type = chart_config.get("chart_type", "line")

        if chart_type == "line":
            # ── 數值型模組：折線圖 ──
            df = records_to_dataframe(records, firebase_node)
            if df is not None and not df.empty:
                st.subheader(f"{emoji} {name}")
                st.line_chart(df)

                # 摘要統計
                stats = get_summary_stats(df)
                if stats:
                    cols = st.columns(len(stats))
                    for j, (col_name, stat) in enumerate(stats.items()):
                        with cols[j]:
                            st.metric(
                                label=col_name,
                                value=f"{stat['平均']}",
                                help=f"最高 {stat['最高']} / 最低 {stat['最低']} / {stat['筆數']}筆",
                            )
                st.markdown("---")

        elif chart_type == "drug":
            # ── 用藥：每日時段遵從表 ──
            st.subheader(f"{emoji} {name}")
            drug_df = get_drug_compliance_table(records, start_date, end_date)
            if drug_df is not None:
                # 用 dataframe 顯示，V 表示有吃
                st.dataframe(
                    drug_df.style.map(
                        lambda v: "background-color: #c8e6c9; color: #2e7d32; font-weight: bold"
                        if v == "V" else "color: #ccc"
                    ),
                    use_container_width=True,
                )
                st.write(f"期間共 **{len(records)}** 筆用藥紀錄")
            else:
                st.info("無法統計用藥紀錄")
            st.markdown("---")

        elif chart_type == "life":
            # ── 生活：情緒分布 ──
            st.subheader(f"{emoji} {name}")
            emotion_df = get_life_emotion_counts(records)
            if emotion_df is not None:
                st.bar_chart(emotion_df)
                st.write(f"期間共 **{len(records)}** 筆生活紀錄")
            else:
                st.info("無法統計情緒分布")
            st.markdown("---")

# ── 匯出區塊 ──
st.subheader("📥 匯出 Excel")

if st.button("產生 Excel 檔案"):
    buffer = BytesIO()
    has_data = False

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for data_type, config in DATA_TYPES.items():
            records = get_user_records(user_id, data_type, start_date, end_date)
            if records:
                df = pd.DataFrame(records)
                columns = [col for col in config["columns"] if col in df.columns]
                df = df[columns]
                sheet_name = config["display_name"]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                has_data = True

        if not has_data:
            pd.DataFrame().to_excel(writer, sheet_name="無資料", index=False)

    buffer.seek(0)

    filename = f"{user_id}_健康紀錄_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"

    st.download_button(
        label="⬇️ 下載 Excel",
        data=buffer,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

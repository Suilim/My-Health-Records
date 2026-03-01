import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from io import BytesIO
from export_records import DATA_TYPES, get_user_records, export_all_to_excel
from settings_utils import get_enabled_modules, MODULE_PATHS, MODULE_NAMES
from plot_utils import (
    CHART_COLUMNS,
    records_to_dataframe,
    get_summary_stats,
    create_plotly_line_chart,
    create_drug_heatmap_chart,
    create_emotion_bar_chart,
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

st.title("📊 健康儀表板")

# ── 建立分頁 ──
tab1, tab2 = st.tabs(["📈 趨勢儀表板", "📥 資料匯出"])

# ==========================================
# Tab 1: 儀表板
# ==========================================
with tab1:
    # ── 時間範圍選擇 ──
    with st.expander("📅 時間範圍設定", expanded=True):
        mode = st.radio("時間模式", ["月份", "自訂範圍"], horizontal=True, label_visibility="collapsed")
        
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
    with st.spinner("載入分析數據..."):
        for mod_key in enabled_modules:
            firebase_node = MODULE_PATHS.get(mod_key)
            if not firebase_node:
                continue

            emoji = MODULE_EMOJI.get(mod_key, "📝")
            name = MODULE_NAMES.get(mod_key, mod_key)
            
            # 取得記錄
            records = get_user_records(user_id, firebase_node, start_date, end_date)
            
            if not records:
                continue

            chart_config = CHART_COLUMNS.get(firebase_node, {})
            chart_type = chart_config.get("chart_type", "line")

            st.subheader(f"{emoji} {name}")

            if chart_type == "line":
                # ── 數值型模組：整合式圖表 (上方折線 + 下方用藥) ──
                df = records_to_dataframe(records, firebase_node)
                
                if df is not None and not df.empty:
                    # 抓取同時期的用藥紀錄作為對照
                    drug_node = MODULE_PATHS.get("drug")
                    drug_records = []
                    if drug_node:
                        drug_records = get_user_records(user_id, drug_node, start_date, end_date)

                    # 顯示 KPI 指標
                    stats = get_summary_stats(df)
                    if stats:
                        cols = st.columns(len(stats) + 1)
                        idx = 0
                        for col_name, stat in stats.items():
                            with cols[idx]:
                                delta = None
                                if stat['最新'] > 0:
                                    diff = stat['最新'] - stat['平均']
                                    delta = f"{diff:+.1f}"
                                
                                st.metric(
                                    label=f"{col_name} (最新)",
                                    value=str(stat['最新']),
                                    delta=delta,
                                    help=f"平均: {stat['平均']} / 最高: {stat['最高']} / 最低: {stat['最低']}"
                                )
                            idx += 1
                            if idx >= 4: idx = 0
                    
                    # 繪製整合式圖表：數值 + 用藥背景 + 詳細用藥
                    from plot_utils import create_combined_chart
                    fig = create_combined_chart(df, firebase_node, drug_records)
                    
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                        st.caption("💡 背景顏色代表當日用藥達成率：🟩 完全達成 / 🟨 部分達成 / 🟥 未服用")

            elif chart_type == "drug":
                # ── 用藥：熱力圖 ──
                # 為了避免重複，如果已經在上方整合圖表中看過，這裡可以只顯示純熱力圖供詳細檢查
                fig = create_drug_heatmap_chart(records, start_date, end_date)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("此期間無用藥紀錄")

            elif chart_type == "life":
                # ── 生活：情緒分布 ──
                fig = create_emotion_bar_chart(records)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("此期間無情緒紀錄")
            
            st.markdown("---")

# ==========================================
# Tab 2: 資料匯出
# ==========================================
with tab2:
    st.header("📥 匯出 Excel 報表")
    st.info("將您所有的健康紀錄匯出成 Excel 檔案，方便保存或提供給醫師參考。")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.write("### 選擇匯出範圍")
        export_mode = st.radio("匯出範圍", ["所有紀錄", "依目前儀表板設定範圍"], key="export_mode")
    
    with col2:
        st.write("### 產生檔案")
        if st.button("🚀 立即產生匯出檔", type="primary"):
            
            target_start = start_date if export_mode == "依目前儀表板設定範圍" else None
            target_end = end_date if export_mode == "依目前儀表板設定範圍" else None
            
            with st.spinner("正在整理資料並產生 Excel..."):
                buffer = BytesIO()
                has_data = False

                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    for data_type, config in DATA_TYPES.items():
                        # 根據選擇決定是否傳入日期
                        records = get_user_records(user_id, data_type, target_start, target_end)
                        
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
                
                # 檔名設定
                if target_start and target_end:
                    date_range_str = f"{target_start.strftime('%Y%m%d')}_{target_end.strftime('%Y%m%d')}"
                else:
                    date_range_str = "All"
                    
                filename = f"{user_id}_健康紀錄_{date_range_str}.xlsx"

                st.success("檔案已產生！請點擊下方按鈕下載。")
                st.download_button(
                    label="⬇️ 下載 Excel 檔案",
                    data=buffer,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

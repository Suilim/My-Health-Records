"""
歷史紀錄總覽頁面
提供日曆檢視,快速查看特定日期的所有健康記錄
"""

import streamlit as st
from datetime import datetime, date, timedelta
from calendar_utils import (
    get_month_recorded_dates,
    get_day_all_records,
    format_record_for_display,
    get_module_display_name,
    get_module_emoji,
    get_calendar_matrix
)

# 頁面設定
st.set_page_config(
    page_title="歷史總覽",
    page_icon="📅",
    layout="wide"
)

# 檢查登入狀態
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ 請先登入")
    st.stop()

user_id = st.session_state.user_id
user_name = st.session_state.user_name

# 初始化 session state
if "calendar_year" not in st.session_state:
    st.session_state.calendar_year = datetime.now().year
if "calendar_month" not in st.session_state:
    st.session_state.calendar_month = datetime.now().month
if "selected_date" not in st.session_state:
    st.session_state.selected_date = None

# 標題
st.title("📅 健康紀錄歷史總覽")
st.write(f"**{user_name}** 的健康記錄")

# 月份導航
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if st.button("◀ 上月", use_container_width=True):
        if st.session_state.calendar_month == 1:
            st.session_state.calendar_month = 12
            st.session_state.calendar_year -= 1
        else:
            st.session_state.calendar_month -= 1
        st.session_state.selected_date = None  # 清除選擇
        st.rerun()

with col2:
    st.markdown(f"<h3 style='text-align: center'>{st.session_state.calendar_year}年 {st.session_state.calendar_month}月</h3>", unsafe_allow_html=True)

with col3:
    if st.button("下月 ▶", use_container_width=True):
        if st.session_state.calendar_month == 12:
            st.session_state.calendar_month = 1
            st.session_state.calendar_year += 1
        else:
            st.session_state.calendar_month += 1
        st.session_state.selected_date = None  # 清除選擇
        st.rerun()

# 今日按鈕
col_spacer1, col_today, col_spacer2 = st.columns([2, 1, 2])
with col_today:
    if st.button("📍 回到今日", use_container_width=True):
        st.session_state.calendar_year = datetime.now().year
        st.session_state.calendar_month = datetime.now().month
        st.session_state.selected_date = date.today()
        st.rerun()

st.markdown("---")

# 取得該月有記錄的日期
with st.spinner("載入日曆..."):
    recorded_dates = get_month_recorded_dates(
        user_id,
        st.session_state.calendar_year,
        st.session_state.calendar_month
    )

# 取得月曆矩陣
calendar_matrix = get_calendar_matrix(
    st.session_state.calendar_year,
    st.session_state.calendar_month
)

# 自訂 CSS
st.markdown("""
<style>
/* 日期按鈕樣式 */
div[data-testid="column"] button {
    width: 100%;
    height: 50px;
    font-size: 16px;
}

/* 有記錄的日期 - 綠色背景 */
.date-with-record {
    background-color: #4CAF50 !important;
    color: white !important;
}

/* 今日日期 - 藍色邊框 */
.date-today {
    border: 2px solid #2196F3 !important;
}

/* 被選中的日期 - 橘色背景 */
.date-selected {
    background-color: #FF9800 !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# 顯示星期標題
st.markdown("### 📅 月曆")
week_header = st.columns(7)
weekdays = ["日", "一", "二", "三", "四", "五", "六"]
for i, day_name in enumerate(weekdays):
    with week_header[i]:
        st.markdown(f"<div style='text-align: center; font-weight: bold; padding: 10px;'>{day_name}</div>", unsafe_allow_html=True)

# 顯示日曆
today = date.today()

for week in calendar_matrix:
    week_cols = st.columns(7)
    for i, day_date in enumerate(week):
        with week_cols[i]:
            if day_date is None:
                # 空白日期
                st.write("")
            else:
                # 判斷按鈕樣式
                has_record = day_date in recorded_dates
                is_today = day_date == today
                is_selected = day_date == st.session_state.selected_date

                # 按鈕文字
                day_num = day_date.day
                if has_record:
                    button_label = f"🟢 {day_num}"
                else:
                    button_label = f"⚪ {day_num}"

                # 點擊按鈕
                if st.button(
                    button_label,
                    key=f"date_{day_date.strftime('%Y%m%d')}",
                    use_container_width=True
                ):
                    st.session_state.selected_date = day_date
                    st.rerun()

# 顯示選中日期的詳細記錄
st.markdown("---")

if st.session_state.selected_date:
    selected_date = st.session_state.selected_date
    st.markdown(f"## 📋 {selected_date.strftime('%Y年%m月%d日')} 的健康記錄")

    # 載入該日的所有記錄
    with st.spinner(f"載入 {selected_date.strftime('%Y-%m-%d')} 的記錄..."):
        day_records = get_day_all_records(user_id, selected_date)

    if not day_records:
        st.info("💡 當天無健康紀錄")
    else:
        # 按模組顯示記錄
        for module_type, records in day_records.items():
            module_name = get_module_display_name(module_type)
            module_emoji = get_module_emoji(module_type)

            with st.expander(f"{module_emoji} {module_name} ({len(records)}筆)", expanded=True):
                for record in records:
                    formatted_text = format_record_for_display(record, module_type)
                    st.markdown(f"- {formatted_text}")

else:
    # 未選擇日期時的提示
    st.info("💡 請點擊日曆上的日期查看當天的健康記錄")

    # 顯示本月統計
    if recorded_dates:
        st.markdown(f"### 📊 {st.session_state.calendar_month}月統計")
        st.write(f"本月共有 **{len(recorded_dates)}** 天有健康記錄")

        # 顯示記錄日期列表
        sorted_dates = sorted(recorded_dates, reverse=True)
        date_list = ", ".join([d.strftime('%m/%d') for d in sorted_dates[:10]])
        if len(sorted_dates) > 10:
            date_list += f" ... (共 {len(sorted_dates)} 天)"
        st.write(f"記錄日期: {date_list}")
    else:
        st.write(f"本月尚無健康記錄")

# 頁尾說明
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 14px;'>
    <p>💡 使用說明</p>
    <ul style='list-style: none; padding: 0;'>
        <li>🟢 綠色標記表示當天有健康記錄</li>
        <li>⚪ 白色表示當天無記錄</li>
        <li>點擊日期即可查看當天的詳細記錄</li>
        <li>各健康數據頁面的「歷史紀錄」分頁仍可正常使用</li>
    </ul>
</div>
""", unsafe_allow_html=True)

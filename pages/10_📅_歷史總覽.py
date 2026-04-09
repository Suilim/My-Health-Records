"""
歷史紀錄總覽頁面
提供日曆檢視,快速查看特定日期的所有健康記錄
使用 streamlit-calendar 套件提供專業的日曆介面
"""

import streamlit as st
from datetime import datetime
from streamlit_calendar import calendar
from calendar_utils import (
    get_month_module_dates,
    MODULE_COLORS,
    MODULE_EMOJIS,
    get_day_all_records,
    format_record_for_display,
    get_module_display_name,
    get_module_emoji
)
from settings_utils import MODULE_NAMES

# 頁面設定
st.set_page_config(
    page_title="歷史總覽",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 檢查登入狀態
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ 請先登入")
    st.stop()

user_id = st.session_state.user_id
user_name = st.session_state.user_name

# 初始化 session state
if "selected_calendar_date" not in st.session_state:
    st.session_state.selected_calendar_date = None
if "last_calendar_state" not in st.session_state:
    st.session_state.last_calendar_state = None
if "hist_cal_year" not in st.session_state:
    st.session_state.hist_cal_year = datetime.now().year
if "hist_cal_month" not in st.session_state:
    st.session_state.hist_cal_month = datetime.now().month

# 標題
st.title("📅 健康紀錄歷史總覽")
st.write(f"**{user_name}** 的健康記錄")
st.markdown("---")

cal_year = st.session_state.hist_cal_year
cal_month = st.session_state.hist_cal_month

# 取得該月各模組有記錄的日期
if st.button("🔄 重新載入日曆", key="reload_calendar"):
    get_month_module_dates.clear()
    st.rerun()

with st.spinner("載入日曆..."):
    module_dates = get_month_module_dates(user_id, cal_year, cal_month)

# 建立日曆事件列表（按模組分列）
calendar_events = []
for module_key, dates in module_dates.items():
    color = MODULE_COLORS.get(module_key, "#888888")
    emoji = MODULE_EMOJIS.get(module_key, "📝")
    name = MODULE_NAMES.get(module_key, module_key)
    for d in dates:
        calendar_events.append({
            "title": f"{emoji} {name}",
            "start": d.strftime('%Y-%m-%d'),
            "backgroundColor": color,
            "borderColor": color,
            "textColor": "white",
        })

# 日曆選項配置
calendar_options = {
    "editable": False,
    "selectable": True,
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,dayGridWeek,dayGridDay"
    },
    "initialView": "dayGridMonth",
    "initialDate": f"{cal_year}-{cal_month:02d}-01",
    "locale": "zh-tw",
    "buttonText": {
        "today": "今天",
        "month": "月",
        "week": "週",
        "day": "日"
    }
}

# 自訂 CSS
custom_css = """
    .fc-event-title {
        font-size: 0.8em;
    }
    .fc-daygrid-day-number {
        font-size: 1.1em;
    }
    .fc-toolbar-title {
        font-size: 1.5em !important;
    }
"""

# 顯示日曆
st.markdown("### 📆 月曆檢視")
st.info("💡 點擊日期可查看當天的詳細健康記錄")

calendar_state = calendar(
    events=calendar_events,
    options=calendar_options,
    custom_css=custom_css,
    key="health_calendar"
)

# 偵錯:顯示 calendar_state 的內容
with st.expander("🔍 Debug 資訊", expanded=False):
    st.write("calendar_state:", calendar_state)
    st.write("selected_calendar_date:", st.session_state.selected_calendar_date)
    st.write("last_calendar_state:", st.session_state.last_calendar_state)
    st.write(f"目前顯示月份: {cal_year}-{cal_month:02d}")
    st.write("module_dates（各模組日期）:", {k: [str(d) for d in v] for k, v in module_dates.items()})
    st.write("calendar_events 數量:", len(calendar_events))
    # 直接查一個模組的原始資料確認格式
    from firebase_utils import db
    from settings_utils import MODULE_PATHS, get_enabled_modules
    enabled = get_enabled_modules(user_id)
    st.write("啟用模組:", enabled)
    # 直接查詢不經過快取，確認原始資料
    from datetime import date as date_cls
    test_month_start = date_cls(cal_year, cal_month, 1)
    test_month_end = date_cls(cal_year + (1 if cal_month == 12 else 0), (cal_month % 12) + 1, 1)
    for mod in enabled:
        node = MODULE_PATHS.get(mod)
        if node:
            raw = db.reference(f'{node}/{user_id}').get()
            if raw:
                found = []
                for record in raw.values():
                    if isinstance(record, dict):
                        ft = record.get("filltime", "")
                        if ft and ft[:7] == f"{cal_year}-{cal_month:02d}":
                            found.append(ft[:10])
                st.write(f"**{mod}**: 本月有 {len(found)} 筆 → {found[:5]}")
            else:
                st.write(f"**{mod}**: 無資料")

# 偵測月份切換（從 eventsSet 或 datesSet 的 view.currentStart 讀取）
if calendar_state:
    view = None
    if calendar_state.get("eventsSet"):
        view = calendar_state["eventsSet"].get("view", {})
    elif calendar_state.get("datesSet"):
        view = calendar_state["datesSet"].get("view", {})
    if view:
        current_start = view.get("currentStart", "")
        if current_start:
            from datetime import timedelta
            mid_date = datetime.strptime(current_start[:10], "%Y-%m-%d") + timedelta(days=7)
            new_year, new_month = mid_date.year, mid_date.month
            if (new_year, new_month) != (cal_year, cal_month):
                st.session_state.hist_cal_year = new_year
                st.session_state.hist_cal_month = new_month
                st.rerun()

# 處理日曆點擊事件
# 關鍵:只有當 calendar_state 發生變化時才處理(避免重複觸發)
if calendar_state and calendar_state != st.session_state.last_calendar_state:
    new_clicked_date = None

    # 檢查是否有 dateClick 事件
    if calendar_state.get("dateClick"):
        try:
            clicked_date_str = calendar_state["dateClick"]["date"]
            # 只取日期部分 YYYY-MM-DD,忽略時間和時區
            # 可能的格式: "2025-02-01T00:00:00", "2025-02-01T00:00:00+08:00", "2025-02-01"
            date_part = clicked_date_str.split('T')[0]  # 取 T 之前的部分
            new_clicked_date = datetime.strptime(date_part, '%Y-%m-%d').date()

            # Debug 輸出
            st.write(f"🔍 解析 dateClick: {clicked_date_str} → {new_clicked_date}")
        except Exception as e:
            st.error(f"解析日期時發生錯誤: {clicked_date_str} - {e}")

    # 檢查是否點擊了事件 (綠色的記錄標記)
    elif calendar_state.get("eventClick"):
        try:
            event_start = calendar_state["eventClick"]["event"]["start"]
            # 只取日期部分
            date_part = event_start.split('T')[0] if 'T' in event_start else event_start
            new_clicked_date = datetime.strptime(date_part, '%Y-%m-%d').date()

            # Debug 輸出
            st.write(f"🔍 解析 eventClick: {event_start} → {new_clicked_date}")
        except Exception as e:
            st.error(f"解析事件日期時發生錯誤: {event_start} - {e}")

    # 更新選中的日期和上次的狀態
    if new_clicked_date:
        st.session_state.selected_calendar_date = new_clicked_date
        st.session_state.last_calendar_state = calendar_state
        st.rerun()  # 重新載入頁面顯示詳情

# 顯示選中日期的詳細記錄
st.markdown("---")

if st.session_state.selected_calendar_date:
    selected_date = st.session_state.selected_calendar_date

    # 標題和清除按鈕
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"## 📋 {selected_date.strftime('%Y年%m月%d日')} 的健康記錄")
    with col2:
        if st.button("✖️ 關閉", key="close_detail"):
            st.session_state.selected_calendar_date = None
            st.rerun()

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
    # 未選擇日期時的統計資訊
    st.markdown("### 📊 本月統計")

    # 從 module_dates 合併出所有有記錄的日期
    all_recorded_dates = set()
    for dates in module_dates.values():
        all_recorded_dates.update(dates)

    if all_recorded_dates:
        st.write(f"本月共有 **{len(all_recorded_dates)}** 天有健康記錄")

        # 顯示記錄日期列表
        sorted_dates = sorted(all_recorded_dates, reverse=True)
        date_list = ", ".join([d.strftime('%m/%d') for d in sorted_dates[:15]])
        if len(sorted_dates) > 15:
            date_list += f" ... (共 {len(sorted_dates)} 天)"
        st.write(f"記錄日期: {date_list}")

        # 計算連續記錄天數
        sorted_dates_asc = sorted(all_recorded_dates)
        max_streak = 1
        current_streak = 1

        for i in range(1, len(sorted_dates_asc)):
            if (sorted_dates_asc[i] - sorted_dates_asc[i-1]).days == 1:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1

        st.write(f"最長連續記錄: **{max_streak}** 天 🔥")
    else:
        st.write(f"本月尚無健康記錄")

# 頁尾說明
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 14px;'>
    <p>💡 使用說明</p>
    <ul style='list-style: none; padding: 0;'>
        <li>📝 綠色標記表示當天有健康記錄</li>
        <li>👆 點擊任意日期即可查看當天的詳細記錄</li>
        <li>🔄 使用上方按鈕可切換月/週/日檢視模式</li>
        <li>📱 各健康數據頁面的「歷史紀錄」分頁仍可正常使用</li>
    </ul>
</div>
""", unsafe_allow_html=True)

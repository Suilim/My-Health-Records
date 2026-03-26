import streamlit as st
from datetime import datetime, timedelta, time
from write_records import add_sleep_record, delete_sleep_record
from nav_utils import bottom_nav
from export_records import get_user_records

st.set_page_config(page_title="睡眠紀錄", page_icon="😴", layout="wide")

# 檢查登入狀態
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("請先登入！")
    st.page_link("app.py", label="🔙 返回登入頁面")
    st.stop()

user_id = st.session_state.user_id

# 檢查是否為補填模式
backfill_date = st.session_state.get("backfill_date", None)
if backfill_date:
    is_backfill = True
    fill_date = backfill_date
else:
    is_backfill = False
    fill_date = datetime.now().strftime("%Y-%m-%d")

# 睡眠品質選項（表情符號 → 數字）
QUALITY_OPTIONS = ["😫", "😕", "😐", "😊", "😄"]
QUALITY_VALUES = {emoji: i + 1 for i, emoji in enumerate(QUALITY_OPTIONS)}
QUALITY_LABELS = {str(i + 1): emoji for i, emoji in enumerate(QUALITY_OPTIONS)}

# 快速標籤
SLEEP_TAGS = ["一直做夢", "睡很多次", "很難入睡", "半夜醒來", "早醒", "一直起床上廁所"]


def calc_duration(sleep_t, wake_t):
    """計算睡眠時數（支援跨夜）"""
    sleep_minutes = sleep_t.hour * 60 + sleep_t.minute
    wake_minutes = wake_t.hour * 60 + wake_t.minute
    if wake_minutes >= sleep_minutes:
        diff = wake_minutes - sleep_minutes
    else:
        diff = (24 * 60 - sleep_minutes) + wake_minutes
    return round(diff / 60, 1)


st.title("😴 睡眠紀錄")
if is_backfill:
    st.warning(f"📝 補填日期：**{fill_date}**")
st.markdown(f"**學員編號：** {user_id}")

# ===== Tab 切換 =====
tab1, tab2 = st.tabs(["📝 新增紀錄", "📋 歷史紀錄"])

# ==================== Tab 1: 新增紀錄 ====================
with tab1:
    st.subheader("新增睡眠紀錄")

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            sleep_time = st.time_input("睡覺時間", value=time(23, 0), key="sleep_time")
        with col2:
            wake_time = st.time_input("起床時間", value=time(7, 0), key="wake_time")

        duration = calc_duration(sleep_time, wake_time)
        st.info(f"🕐 睡眠時數：**{duration} 小時**")

    st.markdown("---")

    with st.container(border=True):
        st.markdown("**這次的睡眠品質如何？**")
        quality_emoji = st.radio(
            "睡眠品質",
            QUALITY_OPTIONS,
            index=2,
            horizontal=True,
            label_visibility="collapsed"
        )

    st.markdown("---")

    with st.container(border=True):
        st.markdown("**睡眠狀況（可複選）**")
        selected_tags = []
        tag_cols_1 = st.columns(3)
        tag_cols_2 = st.columns(3)
        for j, tag in enumerate(SLEEP_TAGS[:3]):
            with tag_cols_1[j]:
                if st.checkbox(tag, key=f"tag_{tag}"):
                    selected_tags.append(tag)
        for j, tag in enumerate(SLEEP_TAGS[3:]):
            with tag_cols_2[j]:
                if st.checkbox(tag, key=f"tag_{tag}"):
                    selected_tags.append(tag)

    st.markdown("---")

    if st.button("✅ 儲存紀錄", width='stretch', type="primary"):
        if is_backfill:
            save_filltime = f"{fill_date} 12:00"
        else:
            save_filltime = datetime.now().strftime("%Y-%m-%d %H:%M")

        add_sleep_record(
            user_id,
            sleep_time=sleep_time.strftime("%H:%M"),
            wake_time=wake_time.strftime("%H:%M"),
            duration=duration,
            quality=QUALITY_VALUES[quality_emoji],
            tags=", ".join(selected_tags),
            filltime=save_filltime
        )

        if "backfill_date" in st.session_state:
            del st.session_state.backfill_date
        if "backfill_slot" in st.session_state:
            del st.session_state.backfill_slot
        st.switch_page("app.py")

# ==================== Tab 2: 歷史紀錄 ====================
with tab2:
    st.subheader("歷史睡眠紀錄")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("開始日期", value=datetime.now().date() - timedelta(days=7), key="sl_start")
    with col2:
        end_date = st.date_input("結束日期", value=datetime.now().date(), key="sl_end")

    records = get_user_records(user_id, "Sleep", start_date=start_date, end_date=end_date)

    if not records:
        st.info("這段期間沒有睡眠紀錄")
    else:
        st.markdown(f"共 **{len(records)}** 筆紀錄")

        for r in reversed(records):
            filltime = r.get("filltime", "")
            sleep_t = r.get("sleeptime", "—")
            wake_t = r.get("waketime", "—")
            dur = r.get("duration", "—")
            quality_val = r.get("quality", "")
            quality_display = QUALITY_LABELS.get(str(quality_val), quality_val)
            tags_val = r.get("tags", "")

            date_part = filltime.split(" ")[0] if " " in filltime else filltime

            with st.container(border=True):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"**{date_part}**　{quality_display}")
                    st.caption(f"😴 {sleep_t} → ☀️ {wake_t}　共 {dur} 小時")
                    if tags_val:
                        st.caption(f"狀況：{tags_val}")
                with col2:
                    if st.button("🗑️", key=f"del_sl_{filltime}", width='stretch'):
                        delete_sleep_record(user_id, filltime)
                        st.success("刪除成功！")
                        st.rerun()

bottom_nav("app")

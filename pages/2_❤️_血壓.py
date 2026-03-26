import streamlit as st
from firebase_utils import db
from datetime import datetime, timedelta
from write_records import add_heartrate_record
from nav_utils import bottom_nav, apply_global_css
from export_records import get_user_records

st.set_page_config(page_title="血壓心率紀錄", page_icon="❤️", layout="wide", initial_sidebar_state="collapsed")
apply_global_css()
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

st.title("❤️ 血壓心率紀錄")
if is_backfill:
    st.warning(f"📝 補填日期：**{fill_date}**")
st.markdown(f"**學員編號：** {user_id}")

# ===== Tab 切換 =====
tab1, tab2 = st.tabs(["📝 新增紀錄", "📋 歷史紀錄"])

# ==================== Tab 1: 新增紀錄 ====================
with tab1:
    st.subheader("新增血壓心率紀錄")

    # 輸入欄位
    col1, col2, col3 = st.columns(3)

    with col1:
        mmHg1 = st.number_input("收縮壓 (mmHg)", min_value=50, max_value=250, value=None, step=1, placeholder="請輸入")
    with col2:
        mmHg2 = st.number_input("舒張壓 (mmHg)", min_value=30, max_value=150, value=None, step=1, placeholder="請輸入")
    with col3:
        bpm = st.number_input("心跳 (bpm)", min_value=30, max_value=200, value=None, step=1, placeholder="請輸入")

    # 血壓判讀提示
    st.markdown("---")
    if mmHg1 is not None and mmHg2 is not None:
        if mmHg1 < 90 or mmHg2 < 60:
            st.info("💙 血壓偏低（建議諮詢醫師）")
        elif mmHg1 < 120 and mmHg2 < 80:
            st.success("💚 血壓正常")
        elif mmHg1 < 140 or mmHg2 < 90:
            st.warning("💛 血壓偏高（注意）")
        else:
            st.error("❤️ 血壓過高（請諮詢醫師）")

    # 儲存按鈕
    st.markdown("---")
    if st.button("✅ 儲存紀錄", width='stretch', type="primary"):
        if mmHg1 is None or mmHg2 is None or bpm is None:
            st.warning("請填寫所有欄位")
        else:
            # 補填模式用指定日期 + 12:00，否則用當前時間
            if is_backfill:
                save_filltime = f"{fill_date} 12:00"
            else:
                save_filltime = datetime.now().strftime("%Y-%m-%d %H:%M")
            add_heartrate_record(user_id, mmHg1, mmHg2, bpm, filltime=save_filltime)
            
            if "backfill_date" in st.session_state:
                del st.session_state.backfill_date

            st.switch_page("app.py")

# ==================== Tab 2: 歷史紀錄 ====================
with tab2:
    st.subheader("歷史血壓心率紀錄")

    # 日期篩選
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("開始日期", value=datetime.now().date() - timedelta(days=7), key="hr_start")
    with col2:
        end_date = st.date_input("結束日期", value=datetime.now().date(), key="hr_end")

    # 取得紀錄
    records = get_user_records(user_id, "HeartRate", start_date=start_date, end_date=end_date)

    if not records:
        st.info("這段期間沒有血壓心率紀錄")
    else:
        st.markdown(f"共 **{len(records)}** 筆紀錄")

        # 顯示紀錄
        for r in reversed(records):  # 最新的在上面
            filltime = r.get("filltime", "")
            mmHg1 = r.get("mmHg1", "")
            mmHg2 = r.get("mmHg2", "")
            bpm = r.get("bpm", "")

            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                st.write(f"📅 {filltime}")
            with col2:
                st.write(f"🩺 {mmHg1}/{mmHg2} mmHg")
            with col3:
                st.write(f"💓 {bpm} bpm")
            with col4:
                if st.button("🗑️", key=f"del_hr_{filltime}"):
                    db.reference(f"HeartRate/{user_id}/{filltime}").delete()
                    st.success("已刪除")
                    st.rerun()

bottom_nav("2_❤️_血壓")

import streamlit as st
from firebase_utils import db
from datetime import datetime, timedelta
from write_records import add_weight_record
from export_records import get_user_records

st.set_page_config(page_title="體重紀錄", page_icon="⚖️", layout="wide")

# 檢查登入狀態
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("請先登入！")
    st.page_link("app.py", label="🔙 返回登入頁面")
    st.stop()

user_id = st.session_state.user_id

st.title("⚖️ 體重紀錄")
st.markdown(f"**學員編號：** {user_id}")

# ===== Tab 切換 =====
tab1, tab2 = st.tabs(["📝 新增紀錄", "📋 歷史紀錄"])

# ==================== Tab 1: 新增紀錄 ====================
with tab1:
    st.subheader("新增體重紀錄")

    # 輸入欄位
    col1, col2 = st.columns(2)

    with col1:
        weight = st.number_input("體重 (kg)", min_value=20.0, max_value=200.0, value=60.0, step=0.1, format="%.1f")
    with col2:
        waist = st.number_input("腰圍 (cm)", min_value=30.0, max_value=200.0, value=70.0, step=0.5, format="%.1f")

    # 儲存按鈕
    st.markdown("---")
    if st.button("✅ 儲存紀錄", use_container_width=True, type="primary"):
        add_weight_record(user_id, weight, waist)
        st.success(f"已儲存！體重 {weight} kg，腰圍 {waist} cm")
        st.rerun()

# ==================== Tab 2: 歷史紀錄 ====================
with tab2:
    st.subheader("歷史體重紀錄")

    # 日期篩選
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("開始日期", value=datetime.now().date() - timedelta(days=30), key="wt_start")
    with col2:
        end_date = st.date_input("結束日期", value=datetime.now().date(), key="wt_end")

    # 取得紀錄
    records = get_user_records(user_id, "Weight", start_date=start_date, end_date=end_date)

    if not records:
        st.info("這段期間沒有體重紀錄")
    else:
        st.markdown(f"共 **{len(records)}** 筆紀錄")

        # 顯示紀錄
        for r in reversed(records):
            filltime = r.get("filltime", "")
            wei = r.get("wei", "")
            wai = r.get("wai", "")

            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                st.write(f"📅 {filltime}")
            with col2:
                st.write(f"⚖️ {wei} kg")
            with col3:
                st.write(f"📏 腰圍 {wai} cm")
            with col4:
                if st.button("🗑️", key=f"del_wt_{filltime}"):
                    db.reference(f"Weight/{user_id}/{filltime}").delete()
                    st.success("已刪除")
                    st.rerun()

# ===== 返回首頁 =====
st.markdown("---")
st.page_link("app.py", label="🏠 返回首頁")

import streamlit as st
from firebase_utils import db
from datetime import datetime, timedelta
from write_records import add_sugar_record
from export_records import get_user_records

st.set_page_config(page_title="血糖紀錄", page_icon="🩸", layout="wide")

# 檢查登入狀態
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("請先登入！")
    st.page_link("app.py", label="🔙 返回登入頁面")
    st.stop()

user_id = st.session_state.user_id

st.title("🩸 血糖紀錄")
st.markdown(f"**學員編號：** {user_id}")

# ===== Tab 切換 =====
tab1, tab2 = st.tabs(["📝 新增紀錄", "📋 歷史紀錄"])

# ==================== Tab 1: 新增紀錄 ====================
with tab1:
    st.subheader("新增血糖紀錄")

    # 輸入欄位
    sugar_level = st.number_input("血糖值 (mg/dL)", min_value=20, max_value=600, value=100, step=1)

    # 血糖判讀提示
    st.markdown("---")
    if sugar_level < 70:
        st.error("⚠️ 血糖過低（請注意低血糖症狀）")
    elif sugar_level < 100:
        st.success("💚 空腹血糖正常")
    elif sugar_level < 126:
        st.warning("💛 空腹血糖偏高（糖尿病前期）")
    else:
        st.error("❤️ 血糖過高（請諮詢醫師）")

    st.caption("※ 以上為空腹血糖參考值，飯後血糖標準不同")

    # 儲存按鈕
    st.markdown("---")
    if st.button("✅ 儲存紀錄", use_container_width=True, type="primary"):
        add_sugar_record(user_id, sugar_level)
        st.success(f"已儲存！血糖 {sugar_level} mg/dL")
        st.rerun()

# ==================== Tab 2: 歷史紀錄 ====================
with tab2:
    st.subheader("歷史血糖紀錄")

    # 日期篩選
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("開始日期", value=datetime.now().date() - timedelta(days=7), key="sg_start")
    with col2:
        end_date = st.date_input("結束日期", value=datetime.now().date(), key="sg_end")

    # 取得紀錄
    records = get_user_records(user_id, "Sugar", start_date=start_date, end_date=end_date)

    if not records:
        st.info("這段期間沒有血糖紀錄")
    else:
        st.markdown(f"共 **{len(records)}** 筆紀錄")

        # 顯示紀錄
        for r in reversed(records):
            filltime = r.get("filltime", "")
            sugar = r.get("sugarlevel", "")

            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"📅 {filltime}")
            with col2:
                # 根據數值顯示顏色
                try:
                    val = int(sugar)
                    if val < 70:
                        st.error(f"🩸 {sugar} mg/dL")
                    elif val < 100:
                        st.success(f"🩸 {sugar} mg/dL")
                    elif val < 126:
                        st.warning(f"🩸 {sugar} mg/dL")
                    else:
                        st.error(f"🩸 {sugar} mg/dL")
                except:
                    st.write(f"🩸 {sugar} mg/dL")
            with col3:
                if st.button("🗑️", key=f"del_sg_{filltime}"):
                    db.reference(f"Sugar/{user_id}/{filltime}").delete()
                    st.success("已刪除")
                    st.rerun()

# ===== 返回首頁 =====
st.markdown("---")
st.page_link("app.py", label="🏠 返回首頁")

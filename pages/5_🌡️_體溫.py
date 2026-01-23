import streamlit as st
from firebase_utils import db
from datetime import datetime, timedelta
from write_records import add_temp_record
from export_records import get_user_records

st.set_page_config(page_title="體溫紀錄", page_icon="🌡️", layout="wide")

# 檢查登入狀態
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("請先登入！")
    st.page_link("app.py", label="🔙 返回登入頁面")
    st.stop()

user_id = st.session_state.user_id

st.title("🌡️ 體溫紀錄")
st.markdown(f"**學員編號：** {user_id}")

# ===== Tab 切換 =====
tab1, tab2 = st.tabs(["📝 新增紀錄", "📋 歷史紀錄"])

# ==================== Tab 1: 新增紀錄 ====================
with tab1:
    st.subheader("新增體溫紀錄")

    # 輸入欄位
    temp = st.number_input("體溫 (°C)", min_value=34.0, max_value=42.0, value=36.5, step=0.1, format="%.1f")

    # 體溫判讀提示
    st.markdown("---")
    if temp < 35.0:
        st.error("🥶 體溫過低（請注意保暖）")
    elif temp < 37.5:
        st.success("💚 體溫正常")
    elif temp < 38.0:
        st.warning("💛 微燒")
    elif temp < 39.0:
        st.error("🔥 發燒（建議休息觀察）")
    else:
        st.error("🔥 高燒（請就醫）")

    # 儲存按鈕
    st.markdown("---")
    if st.button("✅ 儲存紀錄", use_container_width=True, type="primary"):
        add_temp_record(user_id, temp)
        st.success(f"已儲存！體溫 {temp}°C")
        st.rerun()

# ==================== Tab 2: 歷史紀錄 ====================
with tab2:
    st.subheader("歷史體溫紀錄")

    # 日期篩選
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("開始日期", value=datetime.now().date() - timedelta(days=7), key="tp_start")
    with col2:
        end_date = st.date_input("結束日期", value=datetime.now().date(), key="tp_end")

    # 取得紀錄
    records = get_user_records(user_id, "Temp", start_date=start_date, end_date=end_date)

    if not records:
        st.info("這段期間沒有體溫紀錄")
    else:
        st.markdown(f"共 **{len(records)}** 筆紀錄")

        # 顯示紀錄
        for r in reversed(records):
            filltime = r.get("filltime", "")
            temp_val = r.get("temp", "")

            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"📅 {filltime}")
            with col2:
                # 根據數值顯示顏色
                try:
                    val = float(temp_val)
                    if val < 35.0:
                        st.error(f"🌡️ {temp_val}°C")
                    elif val < 37.5:
                        st.success(f"🌡️ {temp_val}°C")
                    elif val < 38.0:
                        st.warning(f"🌡️ {temp_val}°C")
                    else:
                        st.error(f"🌡️ {temp_val}°C")
                except:
                    st.write(f"🌡️ {temp_val}°C")
            with col3:
                if st.button("🗑️", key=f"del_tp_{filltime}"):
                    db.reference(f"Temp/{user_id}/{filltime}").delete()
                    st.success("已刪除")
                    st.rerun()

# ===== 返回首頁 =====
st.markdown("---")
st.page_link("app.py", label="🏠 返回首頁")

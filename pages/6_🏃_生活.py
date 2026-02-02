import streamlit as st
from firebase_utils import db
from datetime import datetime, timedelta
from write_records import add_life_record
from export_records import get_user_records

st.set_page_config(page_title="生活紀錄", page_icon="🏃", layout="wide")

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

st.title("🏃 生活紀錄")
if is_backfill:
    st.warning(f"📝 補填日期：**{fill_date}**")
st.markdown(f"**學員編號：** {user_id}")

# ===== Tab 切換 =====
tab1, tab2 = st.tabs(["📝 新增紀錄", "📋 歷史紀錄"])

# ==================== Tab 1: 新增紀錄 ====================
with tab1:
    st.subheader("新增生活紀錄")

    # 情緒選擇
    st.markdown("**今天的心情如何？**")
    emotion_options = ["😊 開心", "😐 普通", "😢 難過", "😠 生氣", "😰 焦慮", "😴 疲倦"]
    emotion = st.radio(
        "選擇情緒",
        emotion_options,
        horizontal=True,
        label_visibility="collapsed"
    )

    # 生活紀錄內容
    st.markdown("---")
    st.markdown("**今天做了什麼？**")
    life_record = st.text_area(
        "生活紀錄",
        placeholder="例如：今天早上去公園散步30分鐘，下午和朋友喝下午茶...",
        height=150,
        label_visibility="collapsed"
    )

    # 快速標籤
    st.markdown("**快速標籤：**")
    col1, col2, col3, col4 = st.columns(4)
    tags = []
    with col1:
        if st.checkbox("🚶 散步"):
            tags.append("散步")
        if st.checkbox("🏃 運動"):
            tags.append("運動")
    with col2:
        if st.checkbox("👥 社交"):
            tags.append("社交")
        if st.checkbox("📖 閱讀"):
            tags.append("閱讀")
    with col3:
        if st.checkbox("🎵 聽音樂"):
            tags.append("聽音樂")
        if st.checkbox("📺 看電視"):
            tags.append("看電視")
    with col4:
        if st.checkbox("🛒 購物"):
            tags.append("購物")
        if st.checkbox("🏠 在家休息"):
            tags.append("在家休息")

    # 組合紀錄內容
    full_record = life_record
    if tags:
        full_record = f"[{', '.join(tags)}] {life_record}" if life_record else f"[{', '.join(tags)}]"

    # 儲存按鈕
    st.markdown("---")
    if st.button("✅ 儲存紀錄", use_container_width=True, type="primary"):
        if full_record.strip():
            # 取得情緒文字（去掉 emoji）
            emotion_text = emotion.split(" ")[1] if " " in emotion else emotion
            # 補填模式用指定日期 + 12:00，否則用當前時間
            if is_backfill:
                save_filltime = f"{fill_date} 12:00"
            else:
                save_filltime = datetime.now().strftime("%Y-%m-%d %H:%M")
            add_life_record(user_id, full_record, emotion_text, filltime=save_filltime)
            if "backfill_date" in st.session_state:
                del st.session_state.backfill_date
            st.switch_page("app.py")
        else:
            st.warning("請輸入生活紀錄內容或選擇標籤")

# ==================== Tab 2: 歷史紀錄 ====================
with tab2:
    st.subheader("歷史生活紀錄")

    # 日期篩選
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("開始日期", value=datetime.now().date() - timedelta(days=7), key="lf_start")
    with col2:
        end_date = st.date_input("結束日期", value=datetime.now().date(), key="lf_end")

    # 取得紀錄
    records = get_user_records(user_id, "Life", start_date=start_date, end_date=end_date)

    if not records:
        st.info("這段期間沒有生活紀錄")
    else:
        st.markdown(f"共 **{len(records)}** 筆紀錄")

        # 顯示紀錄
        for r in reversed(records):
            filltime = r.get("filltime", "")
            life_content = r.get("liferecord", "")
            emotion_val = r.get("emotion", "")

            # 情緒對應 emoji
            emotion_emoji = {
                "開心": "😊",
                "普通": "😐",
                "難過": "😢",
                "生氣": "😠",
                "焦慮": "😰",
                "疲倦": "😴"
            }.get(emotion_val, "📝")

            with st.expander(f"📅 {filltime} {emotion_emoji} {emotion_val}"):
                st.write(life_content)
                if st.button("🗑️ 刪除", key=f"del_lf_{filltime}"):
                    db.reference(f"Life/{user_id}/{filltime}").delete()
                    st.success("已刪除")
                    st.rerun()

# ===== 返回首頁 =====
st.markdown("---")
st.page_link("app.py", label="🏠 返回首頁")

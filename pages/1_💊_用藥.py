import streamlit as st
from firebase_utils import db
from datetime import datetime, timedelta
from write_records import add_drug_records_batch, update_drug_record, delete_drug_record
from export_records import get_user_records

st.set_page_config(page_title="用藥紀錄", page_icon="💊", layout="wide")

# 檢查登入狀態
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("請先登入！")
    st.page_link("app.py", label="🔙 返回登入頁面")
    st.stop()

user_id = st.session_state.user_id

# 初始化 session state
if "drug_list" not in st.session_state:
    st.session_state.drug_list = []  # 待新增的藥物清單
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = None  # 編輯中的紀錄 filltime

st.title("💊 用藥紀錄")
st.markdown(f"**學員編號：** {user_id}")

# ===== Tab 切換 =====
tab1, tab2 = st.tabs(["📝 新增紀錄", "📋 歷史紀錄"])

# ==================== Tab 1: 新增紀錄 ====================
with tab1:
    st.subheader("新增用藥紀錄")

    # ----- 拷貝前一天資料 -----
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_time = st.selectbox(
            "服藥時段",
            ["早", "午", "晚", "睡前"],
            key="new_eat_time"
        )
    with col2:
        if st.button("📋 拷貝前一天", use_container_width=True):
            # 取得昨天的紀錄
            yesterday = (datetime.now() - timedelta(days=1)).date()
            records = get_user_records(user_id, "Drug", start_date=yesterday, end_date=yesterday)

            # 篩選同時段的藥物
            same_time_drugs = [r for r in records if r.get("eattime") == selected_time]

            if same_time_drugs:
                st.session_state.drug_list = [
                    {"name": r["drugname"], "pieces": r["drugpieces"], "eattime": selected_time}
                    for r in same_time_drugs
                ]
                st.success(f"已帶入昨天 {selected_time} 的 {len(same_time_drugs)} 筆藥物紀錄")
                st.rerun()
            else:
                st.warning(f"昨天 {selected_time} 沒有用藥紀錄")

    st.markdown("---")

    # ----- 藥物清單編輯區 -----
    st.markdown("**藥物清單：**")

    # 顯示目前的藥物清單
    if st.session_state.drug_list:
        for i, drug in enumerate(st.session_state.drug_list):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                new_name = st.text_input(
                    "藥名",
                    value=drug["name"],
                    key=f"drug_name_{i}",
                    label_visibility="collapsed"
                )
                st.session_state.drug_list[i]["name"] = new_name
            with col2:
                new_pieces = st.number_input(
                    "數量",
                    value=int(drug["pieces"]) if str(drug["pieces"]).isdigit() else 1,
                    min_value=1,
                    key=f"drug_pieces_{i}",
                    label_visibility="collapsed"
                )
                st.session_state.drug_list[i]["pieces"] = new_pieces
            with col3:
                st.write(f"({drug['eattime']})")
            with col4:
                if st.button("🗑️", key=f"delete_new_{i}"):
                    st.session_state.drug_list.pop(i)
                    st.rerun()
    else:
        st.info("尚未新增藥物，請點擊下方按鈕新增")

    # ----- 新增一筆藥物 -----
    st.markdown("---")
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        new_drug_name = st.text_input("新增藥物名稱", key="new_drug_name", placeholder="輸入藥名...")
    with col2:
        new_drug_pieces = st.number_input("數量", value=1, min_value=1, key="new_drug_pieces")
    with col3:
        st.write("")  # 空白占位
        st.write("")
        if st.button("➕ 加入", use_container_width=True):
            if new_drug_name:
                st.session_state.drug_list.append({
                    "name": new_drug_name,
                    "pieces": new_drug_pieces,
                    "eattime": selected_time
                })
                st.rerun()
            else:
                st.warning("請輸入藥物名稱")

    # ----- 送出全部 -----
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 儲存全部", use_container_width=True, type="primary", disabled=len(st.session_state.drug_list) == 0):
            if st.session_state.drug_list:
                add_drug_records_batch(user_id, st.session_state.drug_list)
                st.success(f"已儲存 {len(st.session_state.drug_list)} 筆用藥紀錄！")
                st.session_state.drug_list = []  # 清空清單
                st.rerun()
    with col2:
        if st.button("🗑️ 清空清單", use_container_width=True, disabled=len(st.session_state.drug_list) == 0):
            st.session_state.drug_list = []
            st.rerun()


# ==================== Tab 2: 歷史紀錄 ====================
with tab2:
    st.subheader("歷史用藥紀錄")

    # ----- 日期篩選 -----
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("開始日期", value=datetime.now().date() - timedelta(days=7))
    with col2:
        end_date = st.date_input("結束日期", value=datetime.now().date())

    # ----- 取得紀錄 -----
    records = get_user_records(user_id, "Drug", start_date=start_date, end_date=end_date)

    if not records:
        st.info("這段期間沒有用藥紀錄")
    else:
        st.markdown(f"共 **{len(records)}** 筆紀錄")

        # 按日期分組顯示
        records_by_date = {}
        for r in records:
            date_part = r["filltime"].split(" ")[0]
            if date_part not in records_by_date:
                records_by_date[date_part] = []
            records_by_date[date_part].append(r)

        # 依日期降序排列
        for date in sorted(records_by_date.keys(), reverse=True):
            with st.expander(f"📅 {date} ({len(records_by_date[date])} 筆)", expanded=(date == datetime.now().strftime("%Y-%m-%d"))):
                for r in records_by_date[date]:
                    filltime = r["filltime"]

                    # 判斷是否在編輯模式
                    if st.session_state.edit_mode == filltime:
                        # 編輯模式
                        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                        with col1:
                            edit_name = st.text_input("藥名", value=r["drugname"], key=f"edit_name_{filltime}", label_visibility="collapsed")
                        with col2:
                            edit_pieces = st.number_input("數量", value=int(r["drugpieces"]) if str(r["drugpieces"]).isdigit() else 1, min_value=1, key=f"edit_pieces_{filltime}", label_visibility="collapsed")
                        with col3:
                            edit_eattime = st.selectbox("時段", ["早", "午", "晚", "睡前"], index=["早", "午", "晚", "睡前"].index(r["eattime"]) if r["eattime"] in ["早", "午", "晚", "睡前"] else 0, key=f"edit_eattime_{filltime}", label_visibility="collapsed")
                        with col4:
                            if st.button("💾", key=f"save_{filltime}"):
                                update_drug_record(user_id, filltime, edit_name, edit_pieces, edit_eattime)
                                st.session_state.edit_mode = None
                                st.success("更新成功！")
                                st.rerun()
                        with col5:
                            if st.button("❌", key=f"cancel_{filltime}"):
                                st.session_state.edit_mode = None
                                st.rerun()
                    else:
                        # 顯示模式
                        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                        with col1:
                            st.write(f"💊 **{r['drugname']}**")
                        with col2:
                            st.write(f"x {r['drugpieces']}")
                        with col3:
                            st.write(f"({r['eattime']})")
                        with col4:
                            if st.button("✏️", key=f"edit_{filltime}"):
                                st.session_state.edit_mode = filltime
                                st.rerun()
                        with col5:
                            if st.button("🗑️", key=f"del_{filltime}"):
                                delete_drug_record(user_id, filltime)
                                st.success("刪除成功！")
                                st.rerun()

# ===== 返回首頁 =====
st.markdown("---")
st.page_link("app.py", label="🏠 返回首頁")

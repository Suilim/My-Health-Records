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

# 檢查是否為補填模式
backfill_date = st.session_state.get("backfill_date", None)
backfill_slot = st.session_state.get("backfill_slot", None)
if backfill_date:
    is_backfill = True
    fill_date = backfill_date
    prefill_slot = backfill_slot  # 可能是 None 或 "早"/"午"/"晚"/"睡前"
else:
    is_backfill = False
    fill_date = datetime.now().strftime("%Y-%m-%d")
    prefill_slot = None

# 初始化 session state
if "drug_list" not in st.session_state:
    st.session_state.drug_list = []  # 待新增的藥物清單
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = None  # 編輯中的紀錄 filltime
if "last_loaded_time" not in st.session_state:
    st.session_state.last_loaded_time = None  # 記錄上次自動帶入的時段
if "last_loaded_date" not in st.session_state:
    st.session_state.last_loaded_date = None  # 記錄上次自動帶入的日期


def get_latest_drugs_by_eattime(user_id, eattime, before_date=None):
    """取得最近一次同時段的用藥紀錄

    參數:
        before_date: 只取這個日期「之前」的紀錄（不含當天），用於補填時避免帶入當天或未來的紀錄
    """
    # 取得所有用藥紀錄（不限日期範圍，確保能找到最近的）
    records = get_user_records(user_id, "Drug")

    if not records:
        return []

    # 篩選同時段的藥物，並排除指定日期及之後的紀錄
    same_time_drugs = []
    for r in records:
        # 比對時段時，去除可能的空白
        record_eattime = r.get("eattime", "").strip()
        if record_eattime != eattime:
            continue
        record_date = r["filltime"].split(" ")[0]
        # 只保留 before_date 之前的紀錄
        if before_date and record_date >= before_date:
            continue
        same_time_drugs.append(r)

    if not same_time_drugs:
        return []

    # 找到最近一天的日期
    latest_date = max(r["filltime"].split(" ")[0] for r in same_time_drugs)

    # 取出該天同時段的所有藥物
    latest_drugs = [
        {"name": r["drugname"], "pieces": r["drugpieces"], "eattime": eattime}
        for r in same_time_drugs
        if r["filltime"].split(" ")[0] == latest_date
    ]

    return latest_drugs

st.title("💊 用藥紀錄")
if is_backfill:
    if prefill_slot:
        st.warning(f"📝 補填日期：**{fill_date}** 時段：**{prefill_slot}**")
    else:
        st.warning(f"📝 補填日期：**{fill_date}**")
st.markdown(f"**學員編號：** {user_id}")

# ===== Tab 切換 =====
tab1, tab2 = st.tabs(["📝 新增紀錄", "📋 歷史紀錄"])

# ==================== Tab 1: 新增紀錄 ====================
with tab1:
    st.subheader("新增用藥紀錄")

    # ----- 選擇時段（自動帶入最近同時段紀錄）-----
    slot_options = ["早", "午", "晚", "睡前", "需要時"]
    default_index = 0
    if prefill_slot and prefill_slot in slot_options:
        default_index = slot_options.index(prefill_slot)

    selected_time = st.selectbox(
        "服藥時段",
        slot_options,
        index=default_index,
        key="new_eat_time",
        disabled=(prefill_slot is not None)
    )

    # 當時段或日期改變時，自動帶入最近一次同時段的藥物（只取填寫日期之前的紀錄）
    time_changed = selected_time != st.session_state.last_loaded_time
    date_changed = fill_date != st.session_state.last_loaded_date

    if time_changed or date_changed:
        latest_drugs = get_latest_drugs_by_eattime(user_id, selected_time, before_date=fill_date)
        if latest_drugs:
            st.session_state.drug_list = latest_drugs
        else:
            st.session_state.drug_list = []
        st.session_state.last_loaded_time = selected_time
        st.session_state.last_loaded_date = fill_date
        if time_changed or date_changed:
            st.rerun()

    st.markdown("---")

    # ----- 藥物清單編輯區 -----
    st.markdown("**藥物清單：**")

    # 初始化編輯模式
    if "editing_drug_index" not in st.session_state:
        st.session_state.editing_drug_index = None

    # 顯示目前的藥物清單
    if st.session_state.drug_list:
        for i, drug in enumerate(st.session_state.drug_list):
            is_editing = (st.session_state.editing_drug_index == i)
            with st.expander(f"💊 **{drug['name']}**　x {drug['pieces']}", expanded=is_editing):
                if is_editing:
                    # 編輯模式
                    edit_name = st.text_input("藥名", value=drug["name"], key=f"edit_drug_name_{i}")
                    edit_pieces = st.number_input("數量", value=float(drug["pieces"]) if drug["pieces"] else 1.0, min_value=0.5, step=0.5, format="%.1f", key=f"edit_drug_pieces_{i}")
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("💾 儲存", key=f"save_drug_{i}", width='stretch', type="primary"):
                            st.session_state.drug_list[i]["name"] = edit_name
                            st.session_state.drug_list[i]["pieces"] = edit_pieces
                            st.session_state.editing_drug_index = None
                            st.rerun()
                    with col_cancel:
                        if st.button("❌ 取消", key=f"cancel_drug_{i}", width='stretch'):
                            st.session_state.editing_drug_index = None
                            st.rerun()
                else:
                    # 顯示模式
                    col_edit, col_del = st.columns(2)
                    with col_edit:
                        if st.button("✏️ 修改", key=f"edit_drug_{i}", width='stretch'):
                            st.session_state.editing_drug_index = i
                            st.rerun()
                    with col_del:
                        if st.button("🗑️ 刪除", key=f"delete_drug_{i}", width='stretch'):
                            st.session_state.drug_list.pop(i)
                            st.session_state.editing_drug_index = None
                            st.rerun()
    else:
        st.info("尚未新增藥物，請點擊下方按鈕新增")

    # ----- 新增一筆藥物 -----
    st.markdown("---")
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        new_drug_name = st.text_input("新增藥物名稱", key="new_drug_name", placeholder="輸入藥名...")
    with col2:
        new_drug_pieces = st.number_input("數量", value=1.0, min_value=0.5, step=0.5, format="%.1f", key="new_drug_pieces")
    with col3:
        st.write("")  # 空白占位
        st.write("")
        if st.button("➕ 加入", width='stretch'):
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
        if st.button("✅ 儲存全部", width='stretch', type="primary", disabled=len(st.session_state.drug_list) == 0):
            if st.session_state.drug_list:
                # 補填模式用指定日期 + 12:00，否則用當前時間
                if is_backfill:
                    save_filltime = f"{fill_date} 12:00"
                else:
                    save_filltime = datetime.now().strftime("%Y-%m-%d %H:%M")
                add_drug_records_batch(user_id, st.session_state.drug_list, filltime=save_filltime)
                st.session_state.drug_list = []  # 清空清單
                if "backfill_date" in st.session_state:
                    del st.session_state.backfill_date
                if "backfill_slot" in st.session_state:
                    del st.session_state.backfill_slot
                st.switch_page("app.py")
    with col2:
        if st.button("🗑️ 清空清單", width='stretch', disabled=len(st.session_state.drug_list) == 0):
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
                    is_editing = (st.session_state.edit_mode == filltime)
                    expander_label = f"💊 **{r['drugname']}**　x {r['drugpieces']}　({r['eattime']})"
                    with st.expander(expander_label, expanded=is_editing):
                        if is_editing:
                            # 編輯模式
                            edit_name = st.text_input("藥名", value=r["drugname"], key=f"edit_name_{filltime}", label_visibility="collapsed")
                            edit_pieces = st.number_input("數量", value=float(r["drugpieces"]) if r["drugpieces"] else 1.0, min_value=0.5, step=0.5, format="%.1f", key=f"edit_pieces_{filltime}", label_visibility="collapsed")
                            edit_eattime = st.selectbox("時段", ["早", "午", "晚", "睡前", "需要時"], index=["早", "午", "晚", "睡前", "需要時"].index(r["eattime"]) if r["eattime"] in ["早", "午", "晚", "睡前", "需要時"] else 0, key=f"edit_eattime_{filltime}", label_visibility="collapsed")
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.button("💾 儲存", key=f"save_{filltime}", width='stretch', type="primary"):
                                    update_drug_record(user_id, filltime, edit_name, edit_pieces, edit_eattime)
                                    st.session_state.edit_mode = None
                                    st.success("更新成功！")
                                    st.rerun()
                            with col_cancel:
                                if st.button("❌ 取消", key=f"cancel_{filltime}", width='stretch'):
                                    st.session_state.edit_mode = None
                                    st.rerun()
                        else:
                            # 顯示模式
                            col_edit, col_del = st.columns(2)
                            with col_edit:
                                if st.button("✏️ 修改", key=f"edit_{filltime}", width='stretch'):
                                    st.session_state.edit_mode = filltime
                                    st.rerun()
                            with col_del:
                                if st.button("🗑️ 刪除", key=f"del_{filltime}", width='stretch'):
                                    delete_drug_record(user_id, filltime)
                                    st.success("刪除成功！")
                                    st.rerun()

# ===== 返回首頁 =====
st.markdown("---")
st.page_link("app.py", label="🏠 返回首頁")

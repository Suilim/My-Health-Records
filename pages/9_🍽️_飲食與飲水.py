import streamlit as st
from firebase_utils import db
from datetime import datetime, timedelta
from write_records import add_food_records_batch, update_food_record, delete_food_record, add_drink_records_batch, update_drink_record, delete_drink_record
from nav_utils import bottom_nav, apply_global_css
from export_records import get_user_records

st.set_page_config(page_title="飲食與飲水", page_icon="🍽️", layout="wide", initial_sidebar_state="collapsed")
apply_global_css()

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
    prefill_slot = backfill_slot  # 可能是 None 或 "早"/"午"/"晚"/"點心"
else:
    is_backfill = False
    fill_date = datetime.now().strftime("%Y-%m-%d")
    prefill_slot = None

# 初始化 session state
if "food_list" not in st.session_state:
    st.session_state.food_list = []
if "drink_list" not in st.session_state:
    st.session_state.drink_list = []
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = None  # 編輯中的紀錄 filltime
if "last_loaded_time" not in st.session_state:
    st.session_state.last_loaded_time = None
if "last_loaded_date" not in st.session_state:
    st.session_state.last_loaded_date = None

st.title("🍽️ 飲食與飲水")
if is_backfill:
    if prefill_slot:
        st.warning(f"📝 補填日期：**{fill_date}** 時段：**{prefill_slot}**")
    else:
        st.warning(f"📝 補填日期：**{fill_date}**")
st.markdown(f"**學員編號：** {user_id}")

# ===== Tab 切換 =====
tab1, tab2 = st.tabs(["📝 新增飲食與飲品", "📋 歷史紀錄"])

# ==================== Tab 1: 新增飲食與飲品 ====================
with tab1:
    st.subheader("新增飲食與飲品紀錄")

    # ----- 選擇時段 -----
    slot_options = ["早", "午", "晚", "點心"]
    default_index = 0
    if prefill_slot and prefill_slot in slot_options:
        default_index = slot_options.index(prefill_slot)

    selected_time = st.selectbox(
        "時段",
        slot_options,
        index=default_index,
        key="new_eat_time",
        disabled=(prefill_slot is not None)
    )

    st.markdown("---")

    # ===== 食物區塊 =====
    st.markdown("**🍚 食物清單：**")

    # 初始化編輯模式
    if "editing_food_index" not in st.session_state:
        st.session_state.editing_food_index = None

    # 顯示目前的食物清單
    if st.session_state.food_list:
        for i, food in enumerate(st.session_state.food_list):
            is_editing = (st.session_state.editing_food_index == i)
            with st.expander(f"🍚 **{food['name']}**　x {food['pieces']} 份", expanded=is_editing):
                if is_editing:
                    # 編輯模式
                    edit_name = st.text_input("食物名稱", value=food["name"], key=f"edit_food_name_{i}")
                    edit_pieces = st.number_input("份量", value=float(food["pieces"]) if food["pieces"] else 1.0, min_value=0.5, step=0.5, format="%.1f", key=f"edit_food_pieces_{i}")
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("💾 儲存", key=f"save_food_{i}", width='stretch', type="primary"):
                            st.session_state.food_list[i]["name"] = edit_name
                            st.session_state.food_list[i]["pieces"] = edit_pieces
                            st.session_state.editing_food_index = None
                            st.rerun()
                    with col_cancel:
                        if st.button("❌ 取消", key=f"cancel_food_{i}", width='stretch'):
                            st.session_state.editing_food_index = None
                            st.rerun()
                else:
                    # 顯示模式
                    col_edit, col_del = st.columns(2)
                    with col_edit:
                        if st.button("✏️ 修改", key=f"edit_food_{i}", width='stretch'):
                            st.session_state.editing_food_index = i
                            st.rerun()
                    with col_del:
                        if st.button("🗑️ 刪除", key=f"delete_food_{i}", width='stretch'):
                            st.session_state.food_list.pop(i)
                            st.session_state.editing_food_index = None
                            st.rerun()
    else:
        st.info("尚未新增食物")

    # ----- 新增一筆食物 -----
    st.markdown("---")
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        new_food_name = st.text_input("食物名稱", key="new_food_name", placeholder="輸入食物...")
    with col2:
        new_food_pieces = st.number_input("份量", value=1.0, min_value=0.5, step=0.5, format="%.1f", key="new_food_pieces")
    with col3:
        st.write("")
        st.write("")
        if st.button("➕ 加入", width='stretch'):
            if new_food_name:
                st.session_state.food_list.append({
                    "name": new_food_name,
                    "pieces": new_food_pieces,
                    "eattime": selected_time
                })
                st.rerun()
            else:
                st.warning("請輸入食物名稱")

    st.markdown("---")

    # ===== 飲品區塊 =====
    st.markdown("**🥤 飲品清單：**")

    # 初始化編輯模式
    if "editing_drink_index" not in st.session_state:
        st.session_state.editing_drink_index = None

    # 顯示目前的飲品清單
    if st.session_state.drink_list:
        for i, drink in enumerate(st.session_state.drink_list):
            is_editing = (st.session_state.editing_drink_index == i)
            with st.expander(f"🥤 **{drink['name']}**　x {drink['cups']} 杯", expanded=is_editing):
                if is_editing:
                    # 編輯模式
                    edit_name = st.text_input("飲品名稱", value=drink["name"], key=f"edit_drink_name_{i}")
                    edit_cups = st.number_input("杯數", value=float(drink["cups"]) if drink["cups"] else 1.0, min_value=0.5, step=0.5, format="%.1f", key=f"edit_drink_cups_{i}")
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("💾 儲存", key=f"save_drink_{i}", width='stretch', type="primary"):
                            st.session_state.drink_list[i]["name"] = edit_name
                            st.session_state.drink_list[i]["cups"] = edit_cups
                            st.session_state.editing_drink_index = None
                            st.rerun()
                    with col_cancel:
                        if st.button("❌ 取消", key=f"cancel_drink_{i}", width='stretch'):
                            st.session_state.editing_drink_index = None
                            st.rerun()
                else:
                    # 顯示模式
                    col_edit, col_del = st.columns(2)
                    with col_edit:
                        if st.button("✏️ 修改", key=f"edit_drink_{i}", width='stretch'):
                            st.session_state.editing_drink_index = i
                            st.rerun()
                    with col_del:
                        if st.button("🗑️ 刪除", key=f"delete_drink_{i}", width='stretch'):
                            st.session_state.drink_list.pop(i)
                            st.session_state.editing_drink_index = None
                            st.rerun()
    else:
        st.info("尚未新增飲品")

    # ----- 新增一筆飲品 -----
    st.markdown("---")
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        new_drink_name = st.text_input("飲品名稱", key="new_drink_name", placeholder="例如：白開水、咖啡...")
    with col2:
        new_drink_cups = st.number_input("杯數", value=1.0, min_value=0.5, step=0.5, format="%.1f", key="new_drink_cups")
    with col3:
        st.write("")
        st.write("")
        if st.button("➕ 加入飲品", width='stretch'):
            if new_drink_name:
                st.session_state.drink_list.append({
                    "name": new_drink_name,
                    "cups": new_drink_cups,
                    "eattime": selected_time
                })
                st.rerun()
            else:
                st.warning("請輸入飲品名稱")

    # ----- 送出全部 -----
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        save_disabled = len(st.session_state.food_list) == 0 and len(st.session_state.drink_list) == 0
        if st.button("✅ 儲存全部", width='stretch', type="primary", disabled=save_disabled):
            if st.session_state.food_list or st.session_state.drink_list:
                # 補填模式用指定日期 + 12:00，否則用當前時間
                if is_backfill:
                    save_filltime = f"{fill_date} 12:00"
                else:
                    save_filltime = datetime.now().strftime("%Y-%m-%d %H:%M")

                # 分別儲存食物和飲品
                if st.session_state.food_list:
                    add_food_records_batch(user_id, st.session_state.food_list, filltime=save_filltime)
                if st.session_state.drink_list:
                    add_drink_records_batch(user_id, st.session_state.drink_list, filltime=save_filltime)

                st.session_state.food_list = []
                st.session_state.drink_list = []
                if "backfill_date" in st.session_state:
                    del st.session_state.backfill_date
                if "backfill_slot" in st.session_state:
                    del st.session_state.backfill_slot
                st.switch_page("app.py")
    with col2:
        clear_disabled = len(st.session_state.food_list) == 0 and len(st.session_state.drink_list) == 0
        if st.button("🗑️ 清空清單", width='stretch', disabled=clear_disabled):
            st.session_state.food_list = []
            st.session_state.drink_list = []
            st.rerun()


# ==================== Tab 2: 歷史紀錄 ====================
with tab2:
    st.subheader("歷史飲食與飲品紀錄")

    # ----- 日期篩選 -----
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("開始日期", value=datetime.now().date() - timedelta(days=7))
    with col2:
        end_date = st.date_input("結束日期", value=datetime.now().date())

    # ----- 取得食物紀錄 -----
    food_records = get_user_records(user_id, "Food", start_date=start_date, end_date=end_date)
    drink_records = get_user_records(user_id, "Drink", start_date=start_date, end_date=end_date)

    if not food_records and not drink_records:
        st.info("這段期間沒有飲食或飲品紀錄")
    else:
        total_records = len(food_records) + len(drink_records)
        st.markdown(f"共 **{total_records}** 筆紀錄")

        # 合併並按日期分組
        all_records = []
        for r in food_records:
            r["record_type"] = "food"
            all_records.append(r)
        for r in drink_records:
            r["record_type"] = "drink"
            all_records.append(r)

        records_by_date = {}
        for r in all_records:
            date_part = r["filltime"].split(" ")[0]
            if date_part not in records_by_date:
                records_by_date[date_part] = []
            records_by_date[date_part].append(r)

        # 依日期降序排列
        for date in sorted(records_by_date.keys(), reverse=True):
            with st.expander(f"📅 {date} ({len(records_by_date[date])} 筆)", expanded=(date == datetime.now().strftime("%Y-%m-%d"))):
                for idx, r in enumerate(records_by_date[date]):
                    filltime = r["filltime"]
                    rtype = r["record_type"]
                    uid = f"{rtype}_{filltime}_{idx}"
                    is_editing = (st.session_state.edit_mode == uid)

                    if rtype == "food":
                        expander_label = f"🍚 **{r['foodname']}**　x {r['foodpieces']} 份　({r['eattime']})"
                    else:
                        expander_label = f"🥤 **{r['drinkname']}**　x {r['cups']} 杯　({r['eattime']})"

                    with st.expander(expander_label, expanded=is_editing):
                        if is_editing:
                            # 編輯模式
                            if rtype == "food":
                                edit_name = st.text_input("食物名稱", value=r["foodname"], key=f"edit_fname_{uid}", label_visibility="collapsed")
                                edit_pieces = st.number_input("份量", value=float(r["foodpieces"]) if r["foodpieces"] else 1.0, min_value=0.5, step=0.5, format="%.1f", key=f"edit_fpieces_{uid}", label_visibility="collapsed")
                                edit_eattime = st.selectbox("時段", ["早", "午", "晚", "點心"], index=["早", "午", "晚", "點心"].index(r["eattime"]) if r["eattime"] in ["早", "午", "晚", "點心"] else 0, key=f"edit_fetime_{uid}", label_visibility="collapsed")
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.button("💾 儲存", key=f"save_food_{uid}", width='stretch', type="primary"):
                                        update_food_record(user_id, filltime, edit_name, edit_pieces, edit_eattime)
                                        st.session_state.edit_mode = None
                                        st.success("更新成功！")
                                        st.rerun()
                                with col_cancel:
                                    if st.button("❌ 取消", key=f"cancel_food_{uid}", width='stretch'):
                                        st.session_state.edit_mode = None
                                        st.rerun()
                            else:
                                edit_name = st.text_input("飲品名稱", value=r["drinkname"], key=f"edit_dname_{uid}", label_visibility="collapsed")
                                edit_cups = st.number_input("杯數", value=float(r["cups"]) if r["cups"] else 1.0, min_value=0.5, step=0.5, format="%.1f", key=f"edit_dcups_{uid}", label_visibility="collapsed")
                                edit_eattime = st.selectbox("時段", ["早", "午", "晚", "點心"], index=["早", "午", "晚", "點心"].index(r["eattime"]) if r["eattime"] in ["早", "午", "晚", "點心"] else 0, key=f"edit_detime_{uid}", label_visibility="collapsed")
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.button("💾 儲存", key=f"save_drink_{uid}", width='stretch', type="primary"):
                                        update_drink_record(user_id, filltime, edit_name, edit_cups, edit_eattime)
                                        st.session_state.edit_mode = None
                                        st.success("更新成功！")
                                        st.rerun()
                                with col_cancel:
                                    if st.button("❌ 取消", key=f"cancel_drink_{uid}", width='stretch'):
                                        st.session_state.edit_mode = None
                                        st.rerun()
                        else:
                            # 顯示模式
                            col_edit, col_del = st.columns(2)
                            with col_edit:
                                if st.button("✏️ 修改", key=f"edit_{uid}", width='stretch'):
                                    st.session_state.edit_mode = uid
                                    st.rerun()
                            with col_del:
                                if st.button("🗑️ 刪除", key=f"del_{uid}", width='stretch'):
                                    if rtype == "food":
                                        delete_food_record(user_id, filltime)
                                    else:
                                        delete_drink_record(user_id, filltime)
                                    st.success("刪除成功！")
                                    st.rerun()

bottom_nav("9_🍽️_飲食與飲水")

import streamlit as st
from firebase_utils import db
from write_records import update_user_name, update_user_nickname, delete_user_all_data
from nav_utils import bottom_nav, apply_global_css
from settings_utils import (
    MODULE_NAMES,
    DRUG_SLOT_OPTIONS,
    FOOD_DRINK_SLOT_OPTIONS,
    get_user_settings,
    update_module_setting,
    get_reminder_settings,
    update_reminder_setting,
    get_drug_slots,
    save_drug_slots,
    get_food_slots,
    save_food_slots,
    get_drink_slots,
    save_drink_slots,
    get_calendar_enabled,
    set_calendar_enabled
)

st.set_page_config(page_title="設定", page_icon="⚙️", initial_sidebar_state="collapsed")
apply_global_css()
# 檢查登入狀態
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("請先登入！")
    st.page_link("app.py", label="🔙 返回登入頁面")
    st.stop()

user_id = st.session_state.user_id

st.title("⚙️ 設定")
st.markdown(f"**學員編號：** {user_id}")
st.markdown("---")

# ===== 啟用模組設定 =====
st.subheader("📋 啟用模組")
st.caption("開啟的模組會在首頁顯示今日填寫狀態。")

settings = get_user_settings(user_id)
modules = settings.get("modules", {})

# 確保所有模組 key 都存在於 Firebase（修補舊帳號缺少 food/drink 等 key）
for key in MODULE_NAMES.keys():
    if key not in modules:
        update_module_setting(user_id, key, True)
        modules[key] = True

# 用 columns 排列開關
col1, col2 = st.columns(2)

module_keys = list(MODULE_NAMES.keys())
for i, module_key in enumerate(module_keys):
    module_name = MODULE_NAMES[module_key]
    current_state = modules.get(module_key, True)

    with col1 if i % 2 == 0 else col2:
        new_state = st.toggle(
            module_name,
            value=current_state,
            key=f"toggle_{module_key}"
        )
        # 如果狀態改變，更新 Firebase
        if new_state != current_state:
            update_module_setting(user_id, module_key, new_state)
            st.rerun()

# ===== 額外功能 =====
st.markdown("---")
st.subheader("📅 額外功能")
calendar_enabled = get_calendar_enabled(user_id)
new_cal = st.toggle("日曆總覽（在首頁顯示月曆）", value=calendar_enabled, key="toggle_calendar")
if new_cal != calendar_enabled:
    set_calendar_enabled(user_id, new_cal)
    st.rerun()

# ===== 提醒設定 =====
st.markdown("---")
st.subheader("🔔 提醒設定")

reminder = get_reminder_settings(user_id)
reminder_enabled = reminder.get("enabled", True)
reminder_days = reminder.get("days_to_check", 30)

new_enabled = st.toggle("啟用待補填提醒", value=reminder_enabled, key="toggle_reminder")
if new_enabled != reminder_enabled:
    update_reminder_setting(user_id, "enabled", new_enabled)
    st.rerun()

if new_enabled:
    new_days = st.slider("檢查天數", min_value=1, max_value=30, value=min(reminder_days, 30), step=1, help="從幾天前開始檢查漏填紀錄")
    if new_days != reminder_days:
        update_reminder_setting(user_id, "days_to_check", new_days)
        st.rerun()

# ===== 用藥時段設定 =====
if modules.get("drug", True):
    st.markdown("---")
    st.subheader("💊 用藥時段設定")
    st.caption("勾選您每天應服藥的時段，系統會據此偵測哪個時段漏填。")
    st.caption("如果不勾選，系統只會偵測「整天有沒有填」。")

    current_drug_slots = get_drug_slots(user_id)

    col1, col2, col3, col4 = st.columns(4)
    new_slots = []

    for i, slot in enumerate(DRUG_SLOT_OPTIONS):
        with [col1, col2, col3, col4][i]:
            checked = st.checkbox(
                slot,
                value=(slot in current_drug_slots),
                key=f"drug_slot_{slot}"
            )
            if checked:
                new_slots.append(slot)

    if sorted(new_slots) != sorted(current_drug_slots):
        save_drug_slots(user_id, new_slots)
        st.rerun()

# ===== 飲食時段設定 =====
if modules.get("food", True):
    st.markdown("---")
    st.subheader("🍚 飲食時段設定")
    st.caption("勾選您每天應記錄飲食的時段，系統會據此偵測哪個時段漏填。")
    st.caption("如果不勾選，系統只會偵測「整天有沒有填」。")

    current_food_slots = get_food_slots(user_id)

    col1, col2, col3, col4 = st.columns(4)
    new_food_slots = []

    for i, slot in enumerate(FOOD_DRINK_SLOT_OPTIONS):
        with [col1, col2, col3, col4][i]:
            checked = st.checkbox(
                slot,
                value=(slot in current_food_slots),
                key=f"food_slot_{slot}"
            )
            if checked:
                new_food_slots.append(slot)

    if sorted(new_food_slots) != sorted(current_food_slots):
        save_food_slots(user_id, new_food_slots)
        st.rerun()

# ===== 飲品時段設定 =====
if modules.get("drink", True):
    st.markdown("---")
    st.subheader("🥤 飲品時段設定")
    st.caption("勾選您每天應記錄飲品的時段，系統會據此偵測哪個時段漏填。")
    st.caption("如果不勾選，系統只會偵測「整天有沒有填」。")

    current_drink_slots = get_drink_slots(user_id)

    col1, col2, col3, col4 = st.columns(4)
    new_drink_slots = []

    for i, slot in enumerate(FOOD_DRINK_SLOT_OPTIONS):
        with [col1, col2, col3, col4][i]:
            checked = st.checkbox(
                slot,
                value=(slot in current_drink_slots),
                key=f"drink_slot_{slot}"
            )
            if checked:
                new_drink_slots.append(slot)

    if sorted(new_drink_slots) != sorted(current_drink_slots):
        save_drink_slots(user_id, new_drink_slots)
        st.rerun()

# ===== 帳號管理 =====
st.markdown("---")
st.subheader("👤 帳號管理")

# 取得目前姓名與暱稱
user_info = db.reference(f'User/{user_id}').get() or {}
current_name = user_info.get("name", "")
current_nickname = user_info.get("nickname", "")

# ----- 修改暱稱 -----
with st.expander("✏️ 修改暱稱（顯示於登入按鈕）"):
    new_nickname = st.text_input("暱稱", value=current_nickname, key="new_nickname_input", placeholder="例如：🐻 小熊")
    if st.button("儲存暱稱", width="stretch", type="primary"):
        update_user_nickname(user_id, new_nickname.strip())
        st.session_state.user_nickname = new_nickname.strip()
        st.success("暱稱已更新！")
        st.rerun()

# ----- 修改姓名 -----
with st.expander("✏️ 修改姓名"):
    new_name = st.text_input("新姓名", value=current_name, key="new_name_input")
    if st.button("儲存姓名", width="stretch", type="primary"):
        if new_name.strip():
            update_user_name(user_id, new_name.strip())
            st.session_state.user_name = new_name.strip()
            st.success("姓名已更新！")
            st.rerun()
        else:
            st.warning("姓名不可為空")

# ----- 刪除全部資料 -----
with st.expander("🗑️ 刪除帳號"):
    st.warning("刪除後無法復原！帳號與所有健康紀錄將永久刪除。")
    confirm_delete = st.text_input(
        f'請輸入您的學員編號「{user_id}」確認刪除',
        key="confirm_delete_input"
    )
    if st.button("確認刪除帳號", type="primary", width="stretch"):
        if confirm_delete == str(user_id):
            delete_user_all_data(user_id)
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.switch_page("app.py")
        else:
            st.error("學員編號輸入錯誤，請重新確認")


st.markdown("---")
st.subheader("運動紀錄")
st.info("功能開發中...")



bottom_nav("0_⚙️_設定")

import streamlit as st
from firebase_utils import db
from settings_utils import (
    MODULE_NAMES,
    get_user_settings,
    update_module_setting,
    get_reminder_settings,
    update_reminder_setting
)

st.set_page_config(page_title="設定", page_icon="⚙️")

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

st.markdown("---")
st.subheader("🏃 運動清單管理")
st.info("運動清單管理功能開發中...")

# 返回首頁
st.markdown("---")
st.page_link("app.py", label="🏠 返回首頁")

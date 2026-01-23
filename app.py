import streamlit as st
from firebase_utils import db
from write_records import create_user
from settings_utils import (
    MODULE_NAMES,
    get_user_settings,
    get_enabled_modules,
    update_module_setting,
    check_today_records,
    get_all_missing_records
)

# 頁面設定
st.set_page_config(
    page_title="健康管理系統",
    page_icon="🏥",
    layout="centered"
)

# 初始化 session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "selected_user" not in st.session_state:
    st.session_state.selected_user = None  # 記錄選擇的使用者
if "show_add_user" not in st.session_state:
    st.session_state.show_add_user = False  # 是否顯示新增使用者表單

def get_all_users():
    """從 Firebase 取得所有使用者"""
    ref = db.reference("User")
    users = ref.get()
    if users:
        user_list = []
        for user_id, user_data in users.items():
            user_list.append({
                "id": user_id,
                "name": user_data.get("name", "未知")
            })
        return user_list
    return []

def verify_password(user_id: str, password: str) -> bool:
    """驗證使用者密碼"""
    ref = db.reference(f"User/{user_id}/password")
    actual_password = ref.get()
    return actual_password == password

def login_page():
    """登入頁面 - 整合選擇使用者和密碼輸入"""
    st.title("🏥 健康管理系統")
    st.markdown("---")

    # 取得使用者列表
    users = get_all_users()

    if not users and not st.session_state.show_add_user:
        st.warning("目前沒有任何使用者，請先新增使用者。")
        if st.button("➕ 新增使用者", use_container_width=True, type="primary"):
            st.session_state.show_add_user = True
            st.rerun()
        return

    if not users:
        users = []  # 確保 users 是空列表而不是 None

    # 如果還沒選擇使用者，顯示使用者列表
    if st.session_state.selected_user is None and not st.session_state.show_add_user:
        st.subheader("👤 請點選您的名字")

        # 用大按鈕列出所有使用者，方便老人點選
        for user in users:
            if st.button(
                f"👤 {user['name']}",
                key=f"user_{user['id']}",
                use_container_width=True,
                type="primary"
            ):
                st.session_state.selected_user = user
                st.rerun()

        # 新增使用者按鈕
        st.markdown("---")
        if st.button("新增使用者", icon=":material/add:", use_container_width=True):
            st.session_state.show_add_user = True
            st.rerun()

    # 顯示新增使用者表單
    elif st.session_state.show_add_user:
        st.subheader("➕ 新增使用者")

        new_id = st.text_input("學員編號：", key="new_user_id")
        new_name = st.text_input("姓名：", key="new_user_name")
        new_password = st.text_input("密碼：", type="password", key="new_user_password")
        new_password_confirm = st.text_input("確認密碼：", type="password", key="new_user_password_confirm")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ 確認新增", use_container_width=True, type="primary"):
                if not new_id or not new_name or not new_password:
                    st.error("請填寫所有欄位！")
                elif new_password != new_password_confirm:
                    st.error("兩次密碼輸入不一致！")
                else:
                    # 檢查 ID 是否已存在
                    existing_ids = [u['id'] for u in users]
                    if new_id in existing_ids:
                        st.error(f"學員編號 {new_id} 已存在！")
                    else:
                        create_user(new_id, new_name, new_password)
                        st.success(f"使用者 {new_name} 新增成功！")
                        st.session_state.show_add_user = False
                        st.rerun()

        with col2:
            if st.button("🔙 取消", use_container_width=True):
                st.session_state.show_add_user = False
                st.rerun()

    # 已選擇使用者，顯示密碼輸入
    else:
        selected_user = st.session_state.selected_user
        selected_id = selected_user['id']

        st.subheader(f"🔐 {selected_user['name']}，請輸入密碼")
        st.markdown(f"**學員編號：** {selected_id}")

        password = st.text_input(
            "請輸入密碼：",
            type="password",
            key="password_input"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ 登入", use_container_width=True, type="primary"):
                if password:
                    if verify_password(selected_id, password):
                        st.session_state.logged_in = True
                        st.session_state.user_id = selected_id
                        st.session_state.user_name = selected_user['name']
                        st.session_state.selected_user = None  # 清除選擇
                        st.success("登入成功！")
                        st.rerun()
                    else:
                        st.error("密碼錯誤！")
                else:
                    st.warning("請輸入密碼")

        with col2:
            if st.button("🔙 重新選擇", use_container_width=True):
                st.session_state.selected_user = None
                st.rerun()

def main_menu():
    """主選單頁面 (登入後的首頁)"""
    user_id = st.session_state.user_id

    # ===== 待補填通知 (最上方，像未讀郵件) =====
    missing_records = get_all_missing_records(user_id, days_to_check=30)
    total_missing = sum(len(dates) for dates in missing_records.values())

    if total_missing > 0:
        # 紅色通知欄
        st.error(f"🔔 您有 **{total_missing}** 筆待補填紀錄")

        # 顯示各模組缺少數量
        cols = st.columns(len(missing_records))
        for i, (module_key, missing_dates) in enumerate(missing_records.items()):
            with cols[i]:
                module_name = MODULE_NAMES.get(module_key, module_key)
                if st.button(
                    f"📝 {module_name}\n缺 {len(missing_dates)} 天",
                    key=f"notify_{module_key}",
                    use_container_width=True
                ):
                    # TODO: 跳轉到對應補填頁面
                    st.session_state.show_missing_detail = module_key

        # 如果點擊了某個模組，顯示詳細日期
        if "show_missing_detail" in st.session_state and st.session_state.show_missing_detail:
            module_key = st.session_state.show_missing_detail
            if module_key in missing_records:
                module_name = MODULE_NAMES.get(module_key, module_key)
                with st.container():
                    st.markdown(f"**{module_name} 待補填日期：**")
                    for date in missing_records[module_key][:7]:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"📆 {date}")
                        with col2:
                            if st.button("補填", key=f"fill_{module_key}_{date}"):
                                st.info(f"補填 {module_name} - {date}")

                    if len(missing_records[module_key]) > 7:
                        st.caption(f"...還有 {len(missing_records[module_key]) - 7} 天")

                    if st.button("關閉", key="close_missing_detail"):
                        st.session_state.show_missing_detail = None
                        st.rerun()

        st.markdown("---")

    # ===== 標題 =====
    st.title("🏥 健康管理系統")
    st.markdown(f"### 歡迎，{st.session_state.user_name}！")
    st.markdown(f"**學員編號：** {user_id}")

    # ===== 今日填寫狀態 =====
    st.markdown("---")
    st.subheader("📅 今日填寫狀態（點擊進入填寫）")

    # 模組對應的頁面路徑
    MODULE_PAGES = {
        "heartrate": "pages/2_❤️_心率.py",
        "weight": "pages/3_⚖️_體重.py",
        "sugar": "pages/4_🩸_血糖.py",
        "temp": "pages/5_🌡️_體溫.py",
        "drug": "pages/1_💊_用藥.py",
        "life": "pages/6_🏃_生活.py"
    }

    # 模組對應的 emoji
    MODULE_ICONS = {
        "heartrate": "❤️",
        "weight": "⚖️",
        "sugar": "🩸",
        "temp": "🌡️",
        "drug": "💊",
        "life": "🏃"
    }

    today_status = check_today_records(user_id)

    if not today_status:
        st.info("尚未啟用任何模組，請前往設定頁面開啟。")
        st.page_link("pages/0_⚙️_設定.py", label="⚙️ 前往設定", use_container_width=True)
    else:
        cols = st.columns(len(today_status))
        for i, (module_key, is_filled) in enumerate(today_status.items()):
            with cols[i]:
                module_name = MODULE_NAMES.get(module_key, module_key)
                icon = MODULE_ICONS.get(module_key, "📝")
                page_path = MODULE_PAGES.get(module_key)

                if is_filled:
                    # 已填寫 - 綠色按鈕
                    st.page_link(
                        page_path,
                        label=f"✅ {icon}\n{module_name}",
                        use_container_width=True
                    )
                else:
                    # 未填寫 - 用按鈕讓它更明顯
                    st.page_link(
                        page_path,
                        label=f"⏳ {icon}\n{module_name}",
                        use_container_width=True
                    )

    # ===== 底部按鈕 =====
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.page_link("pages/0_⚙️_設定.py", label="⚙️ 設定", use_container_width=True)
    with col2:
        if st.button("🚪 登出", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.user_name = None
            st.rerun()

# 主程式邏輯
if st.session_state.logged_in:
    main_menu()
else:
    login_page()

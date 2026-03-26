import streamlit as st
from datetime import datetime
from firebase_utils import db
from write_records import create_user
from settings_utils import (
    MODULE_NAMES,
    get_user_settings,
    get_enabled_modules,
    update_module_setting,
    check_today_records,
    get_all_missing_records,
    get_reminder_settings
)

# 頁面設定
from PIL import Image
_page_icon = Image.open("logo.png")
st.set_page_config(
    page_title="我的健康紀錄",
    page_icon=_page_icon,
    layout="centered"
)

# 載入全域樣式
def load_css(file_path: str):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("style.css")

# 日期格式化工具
_WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

def format_date_tw(date_str: str) -> str:
    """將 YYYY-MM-DD 格式轉為「M月D日（星期X）」"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{dt.month}月{dt.day}日（{_WEEKDAYS[dt.weekday()]}）"

# 初始化 session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "user_nickname" not in st.session_state:
    st.session_state.user_nickname = None
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
                "name": user_data.get("name", "未知"),
                "nickname": user_data.get("nickname", "")
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
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("logo.png", width="stretch")
    st.markdown("---")

    # 取得使用者列表
    users = get_all_users()

    if not users and not st.session_state.show_add_user:
        st.info("目前還沒有使用者，請先新增。")
        if st.button("新增使用者", icon=":material/add:", width='stretch', type="primary"):
            st.session_state.show_add_user = True
            st.rerun()
        return

    if not users:
        users = []  # 確保 users 是空列表而不是 None

    # 如果還沒選擇使用者，顯示使用者列表
    if st.session_state.selected_user is None and not st.session_state.show_add_user:
        st.subheader("👤 請點選您的ID與綽號")

        # 用大按鈕列出所有使用者，方便點選
        for user in users:
            label = user["id"] if not user["nickname"] else f"{user['id']} · {user['nickname']}"
            if st.button(
                label,
                key=f"user_{user['id']}",
                width='stretch',
                type="primary"
            ):
                st.session_state.selected_user = user
                st.rerun()

        # 新增使用者按鈕
        st.markdown("---")
        if st.button("新增使用者", icon=":material/add:", width='stretch'):
            st.session_state.show_add_user = True
            st.rerun()

    # 顯示新增使用者表單
    elif st.session_state.show_add_user:
        st.subheader("➕ 新增使用者")

        new_id = st.text_input("學員編號：", key="new_user_id")
        new_name = st.text_input("真實姓名：", key="new_user_name")
        new_nickname = st.text_input("暱稱（選填，顯示於登入按鈕）：", key="new_user_nickname", placeholder="例如：🐻 小熊")
        new_password = st.text_input("密碼：", type="password", key="new_user_password")
        new_password_confirm = st.text_input("確認密碼：", type="password", key="new_user_password_confirm")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ 確認新增", width='stretch', type="primary"):
                if not new_id or not new_name or not new_password:
                    st.warning("請填寫所有欄位後再送出。")
                elif new_password != new_password_confirm:
                    st.warning("兩次輸入的密碼不一樣，請重新確認。")
                else:
                    # 檢查 ID 是否已存在
                    existing_ids = [u['id'] for u in users]
                    if new_id in existing_ids:
                        st.warning(f"學員編號 {new_id} 已被使用，請換一個編號。")
                    else:
                        create_user(new_id, new_name, new_password)
                        if new_nickname.strip():
                            db.reference(f'User/{new_id}').update({"nickname": new_nickname.strip()})
                        st.success(f"使用者 {new_name} 新增成功！")
                        st.session_state.show_add_user = False
                        st.rerun()

        with col2:
            if st.button("🔙 取消", width='stretch'):
                st.session_state.show_add_user = False
                st.rerun()

    # 已選擇使用者，顯示密碼輸入
    else:
        selected_user = st.session_state.selected_user
        selected_id = selected_user['id']

        display_name = selected_user["nickname"] if selected_user["nickname"] else selected_id
        st.subheader(f"🔐 {display_name}，請輸入密碼")
        st.markdown(f"**學員編號：** {selected_id}")

        password = st.text_input(
            "請輸入密碼：",
            type="password",
            key="password_input"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ 登入", width='stretch', type="primary"):
                if password:
                    if verify_password(selected_id, password):
                        st.session_state.logged_in = True
                        st.session_state.user_id = selected_id
                        st.session_state.user_name = selected_user['name']
                        st.session_state.user_nickname = selected_user['nickname']
                        st.session_state.selected_user = None  # 清除選擇
                        st.success("登入成功！")
                        st.rerun()
                    else:
                        st.warning("密碼不正確，請再試一次。")
                else:
                    st.warning("請輸入密碼後再登入。")

        with col2:
            if st.button("🔙 重新選擇", width='stretch'):
                st.session_state.selected_user = None
                st.rerun()

def main_menu():
    """主選單頁面 (登入後的首頁)"""
    user_id = st.session_state.user_id

    # 模組對應的頁面路徑
    MODULE_PAGES = {
        "heartrate": "pages/2_❤️_血壓.py",
        "weight": "pages/3_⚖️_體重.py",
        "sugar": "pages/4_🩸_血糖.py",
        "temp": "pages/5_🌡️_體溫.py",
        "drug": "pages/1_💊_用藥.py",
        "life": "pages/6_🏃_生活.py",
        "symptom": "pages/7_🤧_不舒服的地方.py",
        "sleep": "pages/8_😴_睡眠.py",
    }

    # 模組對應的 emoji
    MODULE_ICONS = {
        "heartrate": "❤️",
        "weight": "⚖️",
        "sugar": "🩸",
        "temp": "🌡️",
        "drug": "💊",
        "life": "🏃",
        "symptom": "🤧",
        "sleep": "😴",
    }

    # ===== 待補填通知 (最上方) =====
    reminder = get_reminder_settings(user_id)
    reminder_enabled = reminder.get("enabled", True)
    reminder_days = reminder.get("days_to_check", 30)

    missing_records = {}
    total_missing = 0
    if reminder_enabled:
        missing_records = get_all_missing_records(user_id, days_to_check=reminder_days)
        total_missing = sum(len(dates) for dates in missing_records.values())

    if total_missing > 0:
        st.markdown(
            f'<div class="notice-box">🔔 您有 <strong>{total_missing}</strong> 筆待補填的紀錄</div>',
            unsafe_allow_html=True
        )

        # 把所有待補填項目整理成列表，按日期排序
        all_missing = []
        for module_key, dates_or_slots in missing_records.items():
            if module_key == "drug" and dates_or_slots and isinstance(dates_or_slots[0], dict):
                # 時段級別的用藥漏填
                for item in dates_or_slots:
                    all_missing.append({
                        "date": item["date"],
                        "module_key": "drug",
                        "module_name": f"用藥 {item['slot']}",
                        "slot": item["slot"]
                    })
            else:
                # 其他模組（或無時段設定的 drug）
                for date in dates_or_slots:
                    all_missing.append({
                        "date": date,
                        "module_key": module_key,
                        "module_name": MODULE_NAMES.get(module_key, module_key),
                        "slot": None
                    })

        # 按日期降序排列（最近的在前）
        all_missing.sort(key=lambda x: x["date"], reverse=True)

        # 只顯示前 10 筆，避免太長
        display_limit = 10
        for item in all_missing[:display_limit]:
            btn_key = f"backfill_{item['module_key']}_{item['date']}"
            if item["slot"]:
                btn_key += f"_{item['slot']}"
            if st.button(
                f"補填 {format_date_tw(item['date'])} 的{item['module_name']}",
                key=btn_key,
                width='stretch'
            ):
                # 儲存補填日期到 session state，然後跳轉
                st.session_state.backfill_date = item["date"]
                if item["slot"]:
                    st.session_state.backfill_slot = item["slot"]
                page_path = MODULE_PAGES.get(item["module_key"])
                if page_path:
                    st.switch_page(page_path)

        if len(all_missing) > display_limit:
            remaining = len(all_missing) - display_limit
            st.markdown(
                f'<p class="soft-hint">還有 {remaining} 筆待補填紀錄</p>',
                unsafe_allow_html=True
            )

        st.markdown("---")

    # ===== 今日填寫狀態 =====
    today = datetime.now()
    today_label = f"{today.month}月{today.day}日（{_WEEKDAYS[today.weekday()]}）"
    st.header(f"📅 {st.session_state.user_name} 今日紀錄")
    st.markdown(
        f'<p class="soft-hint">{today_label}</p>',
        unsafe_allow_html=True
    )

    today_status = check_today_records(user_id)

    if not today_status:
        st.info("尚未啟用任何模組，請前往設定頁面開啟。")
        st.page_link("pages/0_⚙️_設定.py", label="⚙️ 前往設定", width='stretch')
    else:
        # 固定 2 欄排列，避免手機上欄位過擠
        module_items = list(today_status.items())
        rows = [module_items[i:i+2] for i in range(0, len(module_items), 2)]

        for row in rows:
            cols = st.columns(2)
            for col_idx, (module_key, status) in enumerate(row):
                with cols[col_idx]:
                    module_name = MODULE_NAMES.get(module_key, module_key)
                    icon = MODULE_ICONS.get(module_key, "📝")
                    page_path = MODULE_PAGES.get(module_key)

                    if module_key == "drug" and isinstance(status, dict):
                        # 用藥有時段設定，部分填寫
                        missing = status["missing"]
                        missing_text = "、".join(missing)
                        st.page_link(
                            page_path,
                            label=f"{icon} {module_name}\n尚未填寫：{missing_text}",
                            width='stretch'
                        )
                    elif status is True:
                        # 已填寫
                        st.page_link(
                            page_path,
                            label=f"✅ {icon} {module_name}\n今日已完成",
                            width='stretch'
                        )
                    else:
                        # 未填寫
                        st.page_link(
                            page_path,
                            label=f"○ {icon} {module_name}\n今日尚未填寫",
                            width='stretch'
                        )

    # ===== 底部按鈕 =====
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.page_link("pages/0_⚙️_設定.py", label="⚙️ 設定", width='stretch')
    with col2:
        st.page_link("pages/9_📊_圖表與匯出.py", label="📊 圖表與匯出", width='stretch')

    # ==== 登出 ====
    st.write("")
    if st.button("🚪 登出", width='stretch'):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.session_state.user_nickname = None
        st.rerun()

# 主程式邏輯
if st.session_state.logged_in:
    main_menu()
else:
    login_page()

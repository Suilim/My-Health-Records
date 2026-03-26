import streamlit as st
from streamlit_option_menu import option_menu

# 對應每個頁面應選中的 index
# 0 = 設定, 1 = 首頁, 2 = 圖表
PAGE_NAV_INDEX = {
    "app": 1,
    "0_⚙️_設定": 0,
    "9_📊_圖表與匯出": 2,
}

def apply_global_css():
    """
    在頁面頂部呼叫，立即隱藏側欄並套用全域樣式。
    各頁面在 set_page_config 之後馬上呼叫此函數。
    """
    try:
        with open("style.css") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

    st.markdown("""
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        </style>
    """, unsafe_allow_html=True)


def bottom_nav(current_page: str = "app"):
    """
    顯示固定在底部的導覽列。
    current_page: 對應 PAGE_NAV_INDEX 的 key，用來標記目前選中哪個 tab。
                  紀錄頁面傳入自己的頁面名稱（如 "1_💊_用藥"），非三個主頁面時預設選中「首頁」。
    """
    default_index = PAGE_NAV_INDEX.get(current_page, 1)

    st.markdown("""
        <style>
        div[data-testid="stBottom"] { display: none; }
        .bottom-nav-container {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 999;
            background-color: #FFFFFF;
            border-top: 1px solid #E0E0E0;
            padding: 4px 0 env(safe-area-inset-bottom) 0;
        }
        .main .block-container {
            padding-bottom: 80px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="bottom-nav-container">', unsafe_allow_html=True)

    nav_key = f"bottom_nav_{current_page}"
    prev_key = f"_bottom_nav_prev_{current_page}"

    # 初始化：記錄本頁面對應的預設選項，避免初始 render 誤觸跳轉
    options = ["⚙️ 設定", "🏠 首頁", "📊 圖表"]
    if prev_key not in st.session_state:
        st.session_state[prev_key] = options[default_index]

    selected = option_menu(
        menu_title=None,
        options=options,
        icons=["", "", ""],
        default_index=default_index,
        orientation="horizontal",
        key=nav_key,
        styles={
            "container": {
                "padding": "0",
                "background-color": "#FFFFFF",
                "margin": "0",
            },
            "nav": {
                "justify-content": "space-around",
            },
            "nav-item": {
                "flex": "1",
            },
            "nav-link": {
                "font-size": "16px",
                "text-align": "center",
                "padding": "8px 0",
                "color": "#5A6A8A",
                "border-radius": "0",
            },
            "nav-link-selected": {
                "background-color": "#FFFFFF",
                "color": "#020B5C",
                "font-weight": "bold",
                "border-top": "2px solid #7A99C4",
            },
            "icon": {
                "display": "none",
            },
        }
    )

    st.markdown('</div>', unsafe_allow_html=True)

    # 只有使用者主動切換（與上次不同）才跳轉
    if selected != st.session_state[prev_key]:
        st.session_state[prev_key] = selected
        if selected == "⚙️ 設定":
            st.switch_page("pages/0_⚙️_設定.py")
        elif selected == "🏠 首頁":
            st.switch_page("app.py")
        elif selected == "📊 圖表":
            st.switch_page("pages/9_📊_圖表與匯出.py")

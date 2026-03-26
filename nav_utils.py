import streamlit as st
from streamlit_option_menu import option_menu

# 對應每個頁面應選中的 index
# 0 = 設定, 1 = 首頁, 2 = 圖表
PAGE_NAV_INDEX = {
    "app": 1,
    "0_⚙️_設定": 0,
    "9_📊_圖表與匯出": 2,
}

def bottom_nav(current_page: str = "app"):
    """
    顯示固定在底部的導覽列。
    current_page: 對應 PAGE_NAV_INDEX 的 key，用來標記目前選中哪個 tab。
    """
    default_index = PAGE_NAV_INDEX.get(current_page, 1)

    # 固定在底部的 CSS
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
        /* 讓頁面底部留出空間，避免內容被導覽列蓋住 */
        .main .block-container {
            padding-bottom: 80px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="bottom-nav-container">', unsafe_allow_html=True)

    selected = option_menu(
        menu_title=None,
        options=["⚙️ 設定", "🏠 首頁", "📊 圖表"],
        icons=["", "", ""],
        default_index=default_index,
        orientation="horizontal",
        key=f"bottom_nav_{current_page}",
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

    # 頁面跳轉
    if selected == "⚙️ 設定" and current_page != "0_⚙️_設定":
        st.switch_page("pages/0_⚙️_設定.py")
    elif selected == "🏠 首頁" and current_page != "app":
        st.switch_page("app.py")
    elif selected == "📊 圖表" and current_page != "9_📊_圖表與匯出":
        st.switch_page("pages/9_📊_圖表與匯出.py")

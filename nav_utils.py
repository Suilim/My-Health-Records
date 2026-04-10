import streamlit as st


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
    顯示固定在底部的導覽列，三個按鈕：設定、首頁、圖表。
    current_page 用來標記目前在哪個頁面（該頁按鈕高亮但仍可點）。
    """
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
            padding: 6px 0 env(safe-area-inset-bottom) 0;
        }
        .main .block-container {
            padding-bottom: 80px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="bottom-nav-container">', unsafe_allow_html=True)

    NAV_ITEMS = [
        ("⚙️ 設定", "0_⚙️_設定",     "pages/0_⚙️_設定.py"),
        ("🏠 首頁", "app",            "app.py"),
        ("📊 圖表", "9_📊_圖表與匯出", "pages/9_📊_圖表與匯出.py"),
    ]

    cols = st.columns(3)
    for col, (label, page_key, path) in zip(cols, NAV_ITEMS):
        is_active = (current_page == page_key)
        with col:
            if is_active:
                # 目前頁面：高亮顯示，點了不跳轉
                st.markdown(
                    f'<div style="text-align:center;font-size:15px;font-weight:bold;'
                    f'color:#7A99C4;border-top:2px solid #7A99C4;padding:6px 0;">'
                    f'{label}</div>',
                    unsafe_allow_html=True
                )
            else:
                if st.button(label, key=f"_bnav_{page_key}", use_container_width=True):
                    st.switch_page(path)

    st.markdown('</div>', unsafe_allow_html=True)

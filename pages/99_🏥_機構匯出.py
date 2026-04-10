import streamlit as st
import pandas as pd
from datetime import date, datetime
from io import BytesIO
from firebase_utils import db
from export_records import DATA_TYPES
from nav_utils import apply_global_css

st.set_page_config(page_title="機構資料匯出", page_icon="🏥", layout="centered")
apply_global_css()

# ── 密碼驗證（從 Firebase 讀取）────────────────────────────────
def get_institution_password() -> str:
    ref = db.reference("Settings/institution/password")
    return ref.get() or ""

if "inst_auth" not in st.session_state:
    st.session_state.inst_auth = False

if not st.session_state.inst_auth:
    st.title("🏥 機構資料匯出")
    st.markdown("請輸入機構密碼以繼續。")
    pwd = st.text_input("密碼", type="password", key="inst_pwd_input")
    if st.button("登入", use_container_width=True):
        if pwd == get_institution_password():
            st.session_state.inst_auth = True
            st.rerun()
        else:
            st.error("密碼錯誤，請重新輸入。")
    st.stop()


# ── 取得所有使用者 ─────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_all_users():
    ref = db.reference("User")
    data = ref.get()
    if not data:
        return []
    users = []
    for uid, info in data.items():
        users.append({
            "id": uid,
            "name": info.get("name", uid),
            "nickname": info.get("nickname", ""),
        })
    return sorted(users, key=lambda u: u["id"])


# ── 從 Firebase 取得單一節點所有使用者的資料 ───────────────────
def fetch_node_all_users(node: str, user_map: dict) -> list[dict]:
    """
    取得指定 Firebase 節點下所有使用者的資料，並附加 user_id / 姓名欄位。
    user_map: {user_id: name}
    """
    ref = db.reference(node)
    data = ref.get()
    if not data:
        return []

    rows = []
    for uid, records in data.items():
        if not isinstance(records, dict):
            continue
        name = user_map.get(uid, uid)
        for record in records.values():
            if not isinstance(record, dict):
                continue
            row = {"使用者ID": uid, "姓名": name}
            row.update(record)
            rows.append(row)
    return rows


# ── 產生 Excel bytes ──────────────────────────────────────────
def build_excel(users: list[dict], start_date: date | None, end_date: date | None) -> bytes:
    user_map = {u["id"]: u["name"] for u in users}

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        has_data = False

        for data_type, config in DATA_TYPES.items():
            node = config["node"]
            display_name = config["display_name"]
            base_columns = config["columns"]

            rows = fetch_node_all_users(node, user_map)
            if not rows:
                continue

            df = pd.DataFrame(rows)

            # 日期篩選
            if start_date or end_date:
                def in_range(ft):
                    try:
                        d = datetime.strptime(str(ft)[:10], "%Y-%m-%d").date()
                        if start_date and d < start_date:
                            return False
                        if end_date and d > end_date:
                            return False
                        return True
                    except Exception:
                        return False

                if "filltime" in df.columns:
                    df = df[df["filltime"].apply(in_range)]

            if df.empty:
                continue

            # 欄位排序：使用者ID、姓名在最前面
            front = ["使用者ID", "姓名"]
            rest = [c for c in base_columns if c != "id" and c in df.columns]
            final_cols = front + rest
            # 補上 df 裡有但 base_columns 沒列到的欄位（如 id）
            extra = [c for c in df.columns if c not in final_cols]
            df = df[final_cols + extra]

            # 按 filltime 排序
            if "filltime" in df.columns:
                df = df.sort_values("filltime")

            df.to_excel(writer, sheet_name=display_name, index=False)
            has_data = True

        if not has_data:
            pd.DataFrame({"訊息": ["所選範圍內無任何資料"]}).to_excel(
                writer, sheet_name="無資料", index=False
            )

    return output.getvalue()


# ── 主頁面 ────────────────────────────────────────────────────
st.title("🏥 機構資料匯出")

users = get_all_users()
if not users:
    st.warning("目前資料庫中沒有任何使用者。")
    st.stop()

st.markdown(f"目前共有 **{len(users)}** 位使用者。")

with st.expander("使用者清單", expanded=False):
    for u in users:
        label = f"{u['id']}　{u['name']}"
        if u["nickname"]:
            label += f"（{u['nickname']}）"
        st.write(label)

st.markdown("---")

# 日期範圍
st.subheader("匯出範圍")
col1, col2 = st.columns(2)
with col1:
    start = st.date_input("開始日期", value=None, key="inst_start")
with col2:
    end = st.date_input("結束日期", value=None, key="inst_end")

if start and end and start > end:
    st.error("開始日期不能晚於結束日期。")
    st.stop()

# 確認匯出
st.markdown("---")
if st.button("📥 產生並下載 Excel", use_container_width=True, type="primary"):
    with st.spinner("資料整理中，請稍候…"):
        excel_bytes = build_excel(users, start or None, end or None)

    start_str = start.strftime("%Y%m%d") if start else "start"
    end_str = end.strftime("%Y%m%d") if end else "end"
    filename = f"機構健康紀錄_{start_str}_{end_str}.xlsx"

    st.download_button(
        label="💾 下載 Excel",
        data=excel_bytes,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    st.success("Excel 已產生，請點上方按鈕下載。")

# 登出
st.markdown("---")
if st.button("🔒 登出機構帳號", use_container_width=True):
    st.session_state.inst_auth = False
    st.rerun()

import streamlit as st
from firebase_utils import db
from datetime import datetime, timedelta
from write_records import add_weight_record, add_bodyfat_record, add_muscle_record, add_bmi_record
from nav_utils import bottom_nav, apply_global_css
from export_records import get_user_records

st.set_page_config(page_title="體重紀錄", page_icon="⚖️", layout="wide", initial_sidebar_state="collapsed")
apply_global_css()
# 檢查登入狀態
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("請先登入！")
    st.page_link("app.py", label="🔙 返回登入頁面")
    st.stop()

user_id = st.session_state.user_id

# 檢查是否為補填模式
backfill_date = st.session_state.get("backfill_date", None)
if backfill_date:
    is_backfill = True
    fill_date = backfill_date
else:
    is_backfill = False
    fill_date = datetime.now().strftime("%Y-%m-%d")


def get_latest_record(user_id, node_name):
    """取得某節點最近一筆紀錄"""
    records = get_user_records(user_id, node_name)
    if not records:
        return None
    # records 已按 filltime 排序，取最後一筆
    return records[-1]


# 讀取上次紀錄
last_weight = get_latest_record(user_id, "Weight")
last_bodyfat = get_latest_record(user_id, "BodyFat")
last_muscle = get_latest_record(user_id, "Muscle")
last_bmi = get_latest_record(user_id, "BMI")

# 上次的值（用來帶入）
prev_wei = float(last_weight["wei"]) if last_weight else None
prev_wai = float(last_weight["wai"]) if last_weight and last_weight.get("wai") else None
prev_bodyfat = float(last_bodyfat["bodyfat"]) if last_bodyfat else None
prev_muscle = float(last_muscle["muscle"]) if last_muscle else None
prev_bmi = float(last_bmi["bmi"]) if last_bmi else None

st.title("⚖️ 體重紀錄")
if is_backfill:
    st.warning(f"📝 補填日期：**{fill_date}**")
st.markdown(f"**學員編號：** {user_id}")

# ===== Tab 切換 =====
tab1, tab2 = st.tabs(["📝 新增紀錄", "📋 歷史紀錄"])

# ==================== Tab 1: 新增紀錄 ====================
with tab1:
    st.subheader("新增體重紀錄")

    # ----- 體重（必填）-----
    st.markdown("**體重（必填）**")
    weight = st.number_input(
        "體重 (kg)", min_value=20.0, max_value=200.0,
        value=prev_wei, step=0.1, format="%.1f",
        placeholder="請輸入",
        label_visibility="collapsed"
    )

    # ----- 選填項目 -----
    st.markdown("---")
    st.markdown("**選填項目**（勾選要記錄的）")

    # 腰圍
    save_waist = st.checkbox("📏 腰圍", value=prev_wai is not None)
    if save_waist:
        waist = st.number_input(
            "腰圍 (cm)", min_value=30.0, max_value=200.0,
            value=prev_wai if prev_wai else 70.0,
            step=0.5, format="%.1f"
        )

    # 體脂
    save_bodyfat = st.checkbox("🔥 體脂率", value=prev_bodyfat is not None)
    if save_bodyfat:
        bodyfat = st.number_input(
            "體脂率 (%)", min_value=1.0, max_value=60.0,
            value=prev_bodyfat if prev_bodyfat else 20.0,
            step=0.1, format="%.1f"
        )

    # 骨骼肌
    save_muscle = st.checkbox("💪 骨骼肌率", value=prev_muscle is not None)
    if save_muscle:
        muscle = st.number_input(
            "骨骼肌率 (%)", min_value=1.0, max_value=60.0,
            value=prev_muscle if prev_muscle else 30.0,
            step=0.1, format="%.1f"
        )

    # BMI
    save_bmi = st.checkbox("📊 BMI", value=prev_bmi is not None)
    if save_bmi:
        bmi = st.number_input(
            "BMI", min_value=10.0, max_value=50.0,
            value=prev_bmi if prev_bmi else 22.0,
            step=0.1, format="%.1f"
        )

    # ----- 儲存 -----
    st.markdown("---")
    if st.button("✅ 儲存紀錄", width='stretch', type="primary"):
        if weight is None:
            st.warning("請填寫體重")
        else:
            # 決定 filltime
            if is_backfill:
                save_filltime = f"{fill_date} 12:00"
            else:
                save_filltime = datetime.now().strftime("%Y-%m-%d %H:%M")

            # 體重（必存），腰圍看有沒有勾選
            wai_value = waist if save_waist else ""
            add_weight_record(user_id, weight, wai_value, filltime=save_filltime)

            # 選填項目
            if save_bodyfat:
                add_bodyfat_record(user_id, bodyfat, filltime=save_filltime)
            if save_muscle:
                add_muscle_record(user_id, muscle, filltime=save_filltime)
            if save_bmi:
                add_bmi_record(user_id, bmi, filltime=save_filltime)

            if "backfill_date" in st.session_state:
                del st.session_state.backfill_date
            st.switch_page("app.py")

# ==================== Tab 2: 歷史紀錄 ====================
with tab2:
    st.subheader("歷史體重紀錄")

    # 日期篩選
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("開始日期", value=datetime.now().date() - timedelta(days=30), key="wt_start")
    with col2:
        end_date = st.date_input("結束日期", value=datetime.now().date(), key="wt_end")

    # 取得各節點紀錄，以 filltime 為 key 建立查找表
    bf_lookup = {r["filltime"]: r for r in get_user_records(user_id, "BodyFat", start_date=start_date, end_date=end_date)}
    mu_lookup = {r["filltime"]: r for r in get_user_records(user_id, "Muscle", start_date=start_date, end_date=end_date)}
    bmi_lookup = {r["filltime"]: r for r in get_user_records(user_id, "BMI", start_date=start_date, end_date=end_date)}

    # 以 Weight 為主紀錄
    records = get_user_records(user_id, "Weight", start_date=start_date, end_date=end_date)

    if not records:
        st.info("這段期間沒有體重紀錄")
    else:
        st.markdown(f"共 **{len(records)}** 筆紀錄")

        for r in reversed(records):
            filltime = r.get("filltime", "")
            wei = r.get("wei", "")
            wai = r.get("wai", "")
            bf = bf_lookup.get(filltime, {}).get("bodyfat", "")
            mu = mu_lookup.get(filltime, {}).get("muscle", "")
            bmi = bmi_lookup.get(filltime, {}).get("bmi", "")

            with st.expander(f"📅 {filltime}　⚖️ {wei} kg"):
                editing_key = f"editing_wt_{filltime}"
                if st.session_state.get(editing_key, False):
                    # 編輯表單
                    new_wei = st.number_input("體重 (kg)", min_value=20.0, max_value=200.0,
                        value=float(wei) if wei else 50.0, step=0.1, format="%.1f", key=f"edit_wei_{filltime}")

                    edit_wai = st.checkbox("📏 腰圍", value=bool(wai), key=f"ck_wai_{filltime}")
                    if edit_wai:
                        new_wai = st.number_input("腰圍 (cm)", min_value=30.0, max_value=200.0,
                            value=float(wai) if wai else 70.0, step=0.5, format="%.1f", key=f"edit_wai_{filltime}")

                    edit_bf = st.checkbox("🔥 體脂率", value=bool(bf), key=f"ck_bf_{filltime}")
                    if edit_bf:
                        new_bf = st.number_input("體脂率 (%)", min_value=1.0, max_value=60.0,
                            value=float(bf) if bf else 20.0, step=0.1, format="%.1f", key=f"edit_bf_{filltime}")

                    edit_mu = st.checkbox("💪 骨骼肌率", value=bool(mu), key=f"ck_mu_{filltime}")
                    if edit_mu:
                        new_mu = st.number_input("骨骼肌率 (%)", min_value=1.0, max_value=60.0,
                            value=float(mu) if mu else 30.0, step=0.1, format="%.1f", key=f"edit_mu_{filltime}")

                    edit_bmi = st.checkbox("📊 BMI", value=bool(bmi), key=f"ck_bmi_{filltime}")
                    if edit_bmi:
                        new_bmi = st.number_input("BMI", min_value=10.0, max_value=50.0,
                            value=float(bmi) if bmi else 22.0, step=0.1, format="%.1f", key=f"edit_bmi_{filltime}")

                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("💾 儲存", key=f"save_wt_{filltime}", type="primary", use_container_width=True):
                            db.reference(f"Weight/{user_id}/{filltime}").update({
                                "wei": str(new_wei),
                                "wai": str(new_wai) if edit_wai else ""
                            })
                            if edit_bf:
                                db.reference(f"BodyFat/{user_id}/{filltime}").set({"id": user_id, "bodyfat": str(new_bf), "filltime": filltime})
                            elif bf:
                                db.reference(f"BodyFat/{user_id}/{filltime}").delete()
                            if edit_mu:
                                db.reference(f"Muscle/{user_id}/{filltime}").set({"id": user_id, "muscle": str(new_mu), "filltime": filltime})
                            elif mu:
                                db.reference(f"Muscle/{user_id}/{filltime}").delete()
                            if edit_bmi:
                                db.reference(f"BMI/{user_id}/{filltime}").set({"id": user_id, "bmi": str(new_bmi), "filltime": filltime})
                            elif bmi:
                                db.reference(f"BMI/{user_id}/{filltime}").delete()
                            st.session_state[editing_key] = False
                            st.rerun()
                    with col_cancel:
                        if st.button("✖️ 取消", key=f"cancel_wt_{filltime}", use_container_width=True):
                            st.session_state[editing_key] = False
                            st.rerun()
                else:
                    # 顯示模式
                    items = [f"⚖️ 體重 **{wei} kg**"]
                    if wai:
                        items.append(f"📏 腰圍 **{wai} cm**")
                    if bf:
                        items.append(f"🔥 體脂率 **{bf}%**")
                    if mu:
                        items.append(f"💪 骨骼肌率 **{mu}%**")
                    if bmi:
                        items.append(f"📊 BMI **{bmi}**")
                    st.markdown("　".join(items))

                    col_edit, col_del = st.columns(2)
                    with col_edit:
                        if st.button("✏️ 修改", key=f"edit_wt_{filltime}", use_container_width=True):
                            st.session_state[editing_key] = True
                            st.rerun()
                    with col_del:
                        if st.button("🗑️ 刪除", key=f"del_wt_{filltime}", use_container_width=True):
                            db.reference(f"Weight/{user_id}/{filltime}").delete()
                            if bf:
                                db.reference(f"BodyFat/{user_id}/{filltime}").delete()
                            if mu:
                                db.reference(f"Muscle/{user_id}/{filltime}").delete()
                            if bmi:
                                db.reference(f"BMI/{user_id}/{filltime}").delete()
                            st.success("已刪除")
                            st.rerun()

bottom_nav("3_⚖️_體重")

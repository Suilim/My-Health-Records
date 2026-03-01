import streamlit as st
from firebase_utils import db
from datetime import datetime, timedelta
from write_records import add_symptom_records_batch, update_symptom_record, delete_symptom_record
from export_records import get_user_records

st.set_page_config(page_title="症狀紀錄", page_icon="🤧", layout="wide")

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

# 持續時間選項
DURATION_OPTIONS = ["很快就過了（幾分鐘內）", "一段時間（幾十分鐘）", "很久（超過一小時）", "不確定"]

# 初始化 session state
if "symptom_list" not in st.session_state:
    st.session_state.symptom_list = []
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = None
if "editing_symptom_index" not in st.session_state:
    st.session_state.editing_symptom_index = None


NO_SYMPTOM_MARKER = "（無症狀）"


def get_latest_symptoms(user_id, before_date=None):
    """取得最近一次的症狀清單（不含指定日期當天及之後，不含「無症狀」紀錄）"""
    records = get_user_records(user_id, "Symptom")
    if not records:
        return [], None

    # 篩掉 before_date 當天及之後的紀錄，以及「無症狀」標記
    if before_date:
        records = [r for r in records if r["filltime"].split(" ")[0] < before_date]
    records = [r for r in records if r.get("symptomname") != NO_SYMPTOM_MARKER]

    if not records:
        return [], None

    # 找到最近一次填寫的日期
    latest_date = max(r["filltime"].split(" ")[0] for r in records)
    latest_symptoms = [
        {"name": r["symptomname"], "duration": r["duration"], "symptomtime": r.get("symptomtime", latest_date)}
        for r in records
        if r["filltime"].split(" ")[0] == latest_date
    ]
    return latest_symptoms, latest_date


def save_no_symptom(user_id, fill_date, is_backfill):
    """儲存「今日無症狀」紀錄"""
    if is_backfill:
        save_filltime = f"{fill_date} 12:00"
    else:
        save_filltime = datetime.now().strftime("%Y-%m-%d %H:%M")
    from write_records import add_symptom_records_batch
    add_symptom_records_batch(user_id, [{
        "name": NO_SYMPTOM_MARKER,
        "duration": "—",
        "symptomtime": fill_date
    }], filltime=save_filltime)

st.title("🤧 症狀紀錄")
if is_backfill:
    st.warning(f"📝 補填日期：**{fill_date}**")
st.markdown(f"**學員編號：** {user_id}")

# ===== Tab 切換 =====
tab1, tab2 = st.tabs(["📝 新增紀錄", "📋 歷史紀錄"])

# ==================== Tab 1: 新增紀錄 ====================
with tab1:
    st.subheader("新增症狀紀錄")
    st.caption("可一次新增多筆症狀，填完後統一儲存")

    st.markdown("---")

    # ----- 今日無症狀 -----
    today_records = get_user_records(user_id, "Symptom", start_date=datetime.strptime(fill_date, "%Y-%m-%d").date(), end_date=datetime.strptime(fill_date, "%Y-%m-%d").date())
    already_no_symptom = any(r.get("symptomname") == NO_SYMPTOM_MARKER for r in today_records)
    already_has_symptom = any(r.get("symptomname") != NO_SYMPTOM_MARKER for r in today_records)

    if already_no_symptom:
        st.success(f"✅ **{fill_date}** 已記錄「今日無症狀」")
    elif already_has_symptom:
        st.info(f"ℹ️ **{fill_date}** 已有症狀紀錄，如需記錄「無症狀」請先刪除現有紀錄")
    else:
        if st.button("✅ 今日無症狀", use_container_width=True, type="primary"):
            save_no_symptom(user_id, fill_date, is_backfill)
            if "backfill_date" in st.session_state:
                del st.session_state.backfill_date
            if "backfill_slot" in st.session_state:
                del st.session_state.backfill_slot
            st.switch_page("app.py")

    st.markdown("---")

    # ----- 套用上次紀錄 -----
    prev_symptoms, prev_date = get_latest_symptoms(user_id, before_date=fill_date)
    if prev_symptoms:
        with st.container(border=True):
            st.caption(f"📋 上次紀錄（{prev_date}）：" + "、".join(s["name"] for s in prev_symptoms))
            if st.button("套用上次症狀清單", use_container_width=True):
                # 套用時將發生時間更新為今天（保留原時間的 HH:MM）
                updated = []
                for s in prev_symptoms:
                    old_time = s["symptomtime"].split(" ")[1] if " " in s["symptomtime"] else "00:00"
                    updated.append({
                        "name": s["name"],
                        "duration": s["duration"],
                        "symptomtime": f"{fill_date} {old_time}"
                    })
                st.session_state.symptom_list = updated
                st.rerun()

    # ----- 症狀清單編輯區 -----
    st.markdown("**症狀清單：**")

    if st.session_state.symptom_list:
        for i, symptom in enumerate(st.session_state.symptom_list):
            if st.session_state.editing_symptom_index == i:
                # 編輯模式
                with st.container(border=True):
                    edit_name = st.text_input(
                        "症狀名稱",
                        value=symptom["name"],
                        key=f"edit_symptom_name_{i}"
                    )
                    # 解析已存的時間
                    try:
                        existing_time = datetime.strptime(symptom["symptomtime"], "%Y-%m-%d %H:%M").time()
                    except Exception:
                        existing_time = datetime.now().time()
                    edit_time = st.time_input(
                        "發生時間",
                        value=existing_time,
                        key=f"edit_symptom_time_{i}"
                    )
                    edit_duration = st.selectbox(
                        "持續多久？",
                        DURATION_OPTIONS,
                        index=DURATION_OPTIONS.index(symptom["duration"]) if symptom["duration"] in DURATION_OPTIONS else 3,
                        key=f"edit_symptom_duration_{i}"
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 儲存", key=f"save_symptom_{i}", use_container_width=True):
                            st.session_state.symptom_list[i]["name"] = edit_name
                            st.session_state.symptom_list[i]["symptomtime"] = f"{fill_date} {edit_time.strftime('%H:%M')}"
                            st.session_state.symptom_list[i]["duration"] = edit_duration
                            st.session_state.editing_symptom_index = None
                            st.rerun()
                    with col2:
                        if st.button("取消", key=f"cancel_symptom_{i}", use_container_width=True):
                            st.session_state.editing_symptom_index = None
                            st.rerun()
            else:
                # 顯示模式
                with st.container(border=True):
                    col1, col2 = st.columns([5, 2])
                    with col1:
                        st.markdown(f"🤧 **{symptom['name']}**")
                        time_display = symptom['symptomtime'].split(' ')[1] if ' ' in symptom['symptomtime'] else symptom['symptomtime']
                        st.caption(f"發生時間：{time_display}　持續：{symptom['duration']}")
                    with col2:
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("✏️", key=f"edit_symptom_{i}", use_container_width=True):
                                st.session_state.editing_symptom_index = i
                                st.rerun()
                        with btn_col2:
                            if st.button("🗑️", key=f"delete_symptom_{i}", use_container_width=True):
                                st.session_state.symptom_list.pop(i)
                                st.session_state.editing_symptom_index = None
                                st.rerun()
    else:
        st.info("尚未新增症狀，請填寫下方表單後點擊「加入」")

    # ----- 新增一筆症狀 -----
    st.markdown("---")
    st.markdown("**新增一筆症狀**")
    with st.container(border=True):
        new_symptom_name = st.text_input("症狀名稱", key="new_symptom_name", placeholder="例如：頭痛、噁心、心悸...")
        new_symptom_time = st.time_input(
            "發生時間",
            value=datetime.now().time(),
            key="new_symptom_time",
            help="症狀大約是幾點發生的？"
        )
        new_symptom_duration = st.selectbox(
            "這次症狀持續多久？",
            DURATION_OPTIONS,
            key="new_symptom_duration"
        )
        if st.button("➕ 加入清單", use_container_width=True, type="secondary"):
            if new_symptom_name.strip():
                symptom_time_str = f"{fill_date} {new_symptom_time.strftime('%H:%M')}"
                st.session_state.symptom_list.append({
                    "name": new_symptom_name.strip(),
                    "duration": new_symptom_duration,
                    "symptomtime": symptom_time_str
                })
                st.rerun()
            else:
                st.warning("請輸入症狀名稱")

    # ----- 送出全部 -----
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 儲存全部", use_container_width=True, type="primary", disabled=len(st.session_state.symptom_list) == 0):
            if st.session_state.symptom_list:
                if is_backfill:
                    save_filltime = f"{fill_date} 12:00"
                else:
                    save_filltime = datetime.now().strftime("%Y-%m-%d %H:%M")

                # 補上 symptomtime（使用日期）
                symptoms_to_save = []
                for s in st.session_state.symptom_list:
                    symptoms_to_save.append({
                        "name": s["name"],
                        "duration": s["duration"],
                        "symptomtime": fill_date
                    })

                add_symptom_records_batch(user_id, symptoms_to_save, filltime=save_filltime)
                st.session_state.symptom_list = []
                if "backfill_date" in st.session_state:
                    del st.session_state.backfill_date
                if "backfill_slot" in st.session_state:
                    del st.session_state.backfill_slot
                st.success("儲存成功！")
                st.switch_page("app.py")
    with col2:
        if st.button("🗑️ 清空清單", use_container_width=True, disabled=len(st.session_state.symptom_list) == 0):
            st.session_state.symptom_list = []
            st.rerun()


# ==================== Tab 2: 歷史紀錄 ====================
with tab2:
    st.subheader("歷史症狀紀錄")

    # ----- 日期篩選 -----
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("開始日期", value=datetime.now().date() - timedelta(days=7))
    with col2:
        end_date = st.date_input("結束日期", value=datetime.now().date())

    # ----- 取得紀錄 -----
    records = get_user_records(user_id, "Symptom", start_date=start_date, end_date=end_date)

    if not records:
        st.info("這段期間沒有症狀紀錄")
    else:
        st.markdown(f"共 **{len(records)}** 筆紀錄")

        # 按日期分組顯示
        records_by_date = {}
        for r in records:
            date_part = r["filltime"].split(" ")[0]
            if date_part not in records_by_date:
                records_by_date[date_part] = []
            records_by_date[date_part].append(r)

        # 依日期降序排列
        for date in sorted(records_by_date.keys(), reverse=True):
            with st.expander(f"📅 {date} ({len(records_by_date[date])} 筆)", expanded=(date == datetime.now().strftime("%Y-%m-%d"))):
                for r in records_by_date[date]:
                    filltime = r["filltime"]
                    is_no_symptom = r.get("symptomname") == NO_SYMPTOM_MARKER

                    # 「無症狀」紀錄只顯示標記與刪除按鈕，不提供編輯
                    if is_no_symptom:
                        with st.container(border=True):
                            col1, col2 = st.columns([5, 2])
                            with col1:
                                st.markdown("✅ **今日無症狀**")
                            with col2:
                                if st.button("🗑️", key=f"del_ns_{filltime}", use_container_width=True, help="刪除此紀錄"):
                                    delete_symptom_record(user_id, filltime)
                                    st.success("刪除成功！")
                                    st.rerun()
                        continue

                    if st.session_state.edit_mode == filltime:
                        # 編輯模式
                        with st.container(border=True):
                            edit_name = st.text_input(
                                "症狀名稱",
                                value=r.get("symptomname", ""),
                                key=f"edit_name_{filltime}"
                            )
                            try:
                                existing_stime = datetime.strptime(r.get("symptomtime", ""), "%Y-%m-%d %H:%M").time()
                            except Exception:
                                existing_stime = datetime.now().time()
                            edit_stime = st.time_input(
                                "發生時間",
                                value=existing_stime,
                                key=f"edit_stime_{filltime}"
                            )
                            current_duration = r.get("duration", "不確定")
                            edit_duration = st.selectbox(
                                "持續多久？",
                                DURATION_OPTIONS,
                                index=DURATION_OPTIONS.index(current_duration) if current_duration in DURATION_OPTIONS else 3,
                                key=f"edit_duration_{filltime}"
                            )
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("💾 儲存", key=f"save_{filltime}", use_container_width=True):
                                    date_part = r.get("symptomtime", fill_date).split(" ")[0]
                                    new_stime_str = f"{date_part} {edit_stime.strftime('%H:%M')}"
                                    update_symptom_record(user_id, filltime, edit_name, edit_duration, new_stime_str)
                                    st.session_state.edit_mode = None
                                    st.success("更新成功！")
                                    st.rerun()
                            with col2:
                                if st.button("取消", key=f"cancel_{filltime}", use_container_width=True):
                                    st.session_state.edit_mode = None
                                    st.rerun()
                    else:
                        # 顯示模式
                        with st.container(border=True):
                            col1, col2 = st.columns([5, 2])
                            with col1:
                                st.markdown(f"🤧 **{r.get('symptomname', '（未知症狀）')}**")
                                stime_raw = r.get("symptomtime", "")
                                stime_display = stime_raw.split(" ")[1] if " " in stime_raw else stime_raw
                                st.caption(f"發生時間：{stime_display}　持續：{r.get('duration', '—')}")
                            with col2:
                                btn_col1, btn_col2 = st.columns(2)
                                with btn_col1:
                                    if st.button("✏️", key=f"edit_{filltime}", use_container_width=True):
                                        st.session_state.edit_mode = filltime
                                        st.rerun()
                                with btn_col2:
                                    if st.button("🗑️", key=f"del_{filltime}", use_container_width=True):
                                        delete_symptom_record(user_id, filltime)
                                        st.success("刪除成功！")
                                        st.rerun()

# ===== 返回首頁 =====
st.markdown("---")
st.page_link("app.py", label="🏠 返回首頁")

from firebase_utils import db
from datetime import datetime, timedelta

# 模組名稱對照表
MODULE_NAMES = {
    "heartrate": "血壓心率",
    "weight": "體重",
    "sugar": "血糖",
    "temp": "體溫",
    "drug": "用藥",
    "life": "生活紀錄",
    "symptom":"不舒服的地方"
}

# 用藥時段選項
DRUG_SLOT_OPTIONS = ["早", "午", "晚", "睡前"]

# 模組對應的 Firebase 路徑
MODULE_PATHS = {
    "heartrate": "HeartRate",
    "weight": "Weight",
    "sugar": "Sugar",
    "temp": "Temp",
    "drug": "Drug",
    "life": "Life",
    "symptom":"Symptom"
}


def get_user_settings(user_id: str) -> dict:
    """取得用戶設定"""
    ref = db.reference(f"Settings/{user_id}")
    settings = ref.get()
    if settings:
        return settings
    # 如果沒有設定，回傳預設值
    return {
        "modules": {
            "heartrate": True,
            "weight": True,
            "sugar": True,
            "temp": True,
            "drug": True,
            "life": True
        }
    }


def get_enabled_modules(user_id: str) -> list:
    """取得用戶啟用的模組列表"""
    settings = get_user_settings(user_id)
    modules = settings.get("modules", {})
    return [key for key, enabled in modules.items() if enabled]


def update_module_setting(user_id: str, module_key: str, enabled: bool):
    """更新單一模組的啟用狀態"""
    ref = db.reference(f"Settings/{user_id}/modules/{module_key}")
    ref.set(enabled)


def get_reminder_settings(user_id: str) -> dict:
    """取得提醒設定"""
    ref = db.reference(f"Settings/{user_id}/reminder")
    settings = ref.get()
    if settings:
        # 確保 days_to_check 是 int
        settings["days_to_check"] = int(settings.get("days_to_check", 30))
        return settings
    return {"enabled": True, "days_to_check": 30}


def update_reminder_setting(user_id: str, key: str, value):
    """更新提醒設定"""
    ref = db.reference(f"Settings/{user_id}/reminder/{key}")
    ref.set(value)


def get_drug_slots(user_id: str) -> list:
    """取得用戶設定的用藥時段組合，回傳已勾選的時段列表如 ["早", "晚"]，未設定回傳 []"""
    ref = db.reference(f"Settings/{user_id}/drug_slots")
    slots = ref.get()
    if slots is None:
        return []
    return [slot for slot in DRUG_SLOT_OPTIONS if slots.get(slot, False)]


def save_drug_slots(user_id: str, selected_slots: list):
    """儲存用戶的用藥時段組合"""
    ref = db.reference(f"Settings/{user_id}/drug_slots")
    slots_dict = {slot: (slot in selected_slots) for slot in DRUG_SLOT_OPTIONS}
    ref.set(slots_dict)


def get_user_created_date(user_id: str) -> str:
    """取得用戶註冊日期"""
    ref = db.reference(f"User/{user_id}/created_at")
    created_at = ref.get()
    if created_at:
        return created_at
    # 如果沒有註冊日期（舊用戶），回傳今天
    return datetime.now().strftime("%Y-%m-%d")


def get_records_for_module(user_id: str, module_key: str) -> dict:
    """取得某模組的所有紀錄"""
    path = MODULE_PATHS.get(module_key)
    if not path:
        return {}
    ref = db.reference(f"{path}/{user_id}")
    records = ref.get()
    return records if records else {}


def get_recorded_dates(user_id: str, module_key: str) -> set:
    """取得某模組已有紀錄的日期集合"""
    records = get_records_for_module(user_id, module_key)
    dates = set()
    for filltime in records.keys():
        # filltime 格式: "2024-01-20 14:30" 或 "2024-01-20 14:30:00"
        date_part = filltime.split(" ")[0]
        dates.add(date_part)
    return dates


def get_recorded_slots_by_date(user_id: str) -> dict:
    """取得用藥模組中，每個日期已填寫的時段集合
    回傳: {"2024-01-15": {"早", "晚"}, ...}
    """
    records = get_records_for_module(user_id, "drug")
    date_slots = {}
    for filltime, record_data in records.items():
        date_part = filltime.split(" ")[0]
        eattime = ""
        if isinstance(record_data, dict):
            eattime = record_data.get("eattime", "").strip()
        if date_part not in date_slots:
            date_slots[date_part] = set()
        if eattime:
            date_slots[date_part].add(eattime)
    return date_slots


def get_first_record_date(user_id: str, module_key: str):
    """取得某模組第一筆紀錄的日期（用來判斷何時開始記錄）"""
    recorded_dates = get_recorded_dates(user_id, module_key)
    if not recorded_dates:
        return None
    # 取最早的日期
    return min(recorded_dates)


def get_missing_dates(user_id: str, module_key: str, days_to_check: int = 30) -> list:
    """
    取得某模組漏填的日期列表

    邏輯: 從「第一筆紀錄日期」開始檢查，而非註冊日。
          如果從來沒填過，就不提醒。

    參數:
        user_id: 用戶 ID
        module_key: 模組 key (heartrate, weight, etc.)
        days_to_check: 要檢查幾天內的紀錄 (預設 30 天)

    回傳:
        漏填的日期列表，格式 ["2024-01-15", "2024-01-16", ...]
    """
    # 取得第一筆紀錄日期作為起始點
    first_date_str = get_first_record_date(user_id, module_key)
    if first_date_str is None:
        return []  # 從沒填過，不提醒

    first_date = datetime.strptime(first_date_str, "%Y-%m-%d").date()

    # 今天
    today = datetime.now().date()

    # 計算檢查起始日 (取第一筆紀錄日和 N 天前的較晚者)
    check_start = today - timedelta(days=days_to_check)
    start_date = max(first_date, check_start)

    # 如果第一筆紀錄是今天，不需要檢查
    if start_date >= today:
        return []

    # 取得已有紀錄的日期
    recorded_dates = get_recorded_dates(user_id, module_key)

    # 找出漏填的日期 (不含今天，今天還可以填)
    missing = []
    current = start_date
    while current < today:
        date_str = current.strftime("%Y-%m-%d")
        if date_str not in recorded_dates:
            missing.append(date_str)
        current += timedelta(days=1)

    return missing


def get_missing_drug_slots(user_id: str, days_to_check: int = 30) -> list:
    """取得用藥模組中，漏填的 (日期, 時段) 列表
    回傳: [{"date": "2024-01-15", "slot": "晚"}, ...]
    如果使用者沒設定時段組合，回傳 []
    """
    required_slots = get_drug_slots(user_id)
    if not required_slots:
        return []

    first_date_str = get_first_record_date(user_id, "drug")
    if first_date_str is None:
        return []

    first_date = datetime.strptime(first_date_str, "%Y-%m-%d").date()
    today = datetime.now().date()

    check_start = today - timedelta(days=days_to_check)
    start_date = max(first_date, check_start)

    if start_date >= today:
        return []

    recorded_slots = get_recorded_slots_by_date(user_id)

    missing = []
    current = start_date
    while current < today:
        date_str = current.strftime("%Y-%m-%d")
        filled_slots = recorded_slots.get(date_str, set())
        for slot in required_slots:
            if slot not in filled_slots:
                missing.append({"date": date_str, "slot": slot})
        current += timedelta(days=1)

    return missing


def get_all_missing_records(user_id: str, days_to_check: int = 30) -> dict:
    """
    取得所有啟用模組的漏填紀錄

    回傳:
        {
            "heartrate": ["2024-01-15", "2024-01-16"],
            "weight": ["2024-01-15"],
            ...
        }
    """
    enabled_modules = get_enabled_modules(user_id)
    missing_records = {}

    for module_key in enabled_modules:
        if module_key == "drug":
            # 優先使用時段級別偵測
            drug_missing = get_missing_drug_slots(user_id, days_to_check)
            if drug_missing:
                missing_records["drug"] = drug_missing
            else:
                # 退回原始日期級別偵測
                missing = get_missing_dates(user_id, "drug", days_to_check)
                if missing:
                    missing_records["drug"] = missing
        else:
            missing = get_missing_dates(user_id, module_key, days_to_check)
            if missing:
                missing_records[module_key] = missing

    return missing_records


def check_today_records(user_id: str) -> dict:
    """
    檢查今天各模組是否已填寫

    回傳:
        {
            "heartrate": True,   # 已填
            "weight": False,     # 未填
            ...
        }
    """
    enabled_modules = get_enabled_modules(user_id)
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_status = {}

    for module_key in enabled_modules:
        if module_key == "drug":
            required_slots = get_drug_slots(user_id)
            if required_slots:
                recorded_slots = get_recorded_slots_by_date(user_id)
                filled_today = recorded_slots.get(today_str, set())
                missing_today = [s for s in required_slots if s not in filled_today]
                if not missing_today:
                    today_status["drug"] = True
                else:
                    today_status["drug"] = {
                        "filled": [s for s in required_slots if s in filled_today],
                        "missing": missing_today
                    }
            else:
                recorded_dates = get_recorded_dates(user_id, module_key)
                today_status[module_key] = today_str in recorded_dates
        else:
            recorded_dates = get_recorded_dates(user_id, module_key)
            today_status[module_key] = today_str in recorded_dates

    return today_status

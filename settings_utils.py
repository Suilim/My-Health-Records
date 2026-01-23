from firebase_utils import db
from datetime import datetime, timedelta

# 模組名稱對照表
MODULE_NAMES = {
    "heartrate": "血壓心率",
    "weight": "體重",
    "sugar": "血糖",
    "temp": "體溫",
    "drug": "用藥",
    "life": "生活紀錄"
}

# 模組對應的 Firebase 路徑
MODULE_PATHS = {
    "heartrate": "HeartRate",
    "weight": "Weight",
    "sugar": "Sugar",
    "temp": "Temp",
    "drug": "Drug",
    "life": "Life"
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


def get_missing_dates(user_id: str, module_key: str, days_to_check: int = 30) -> list:
    """
    取得某模組漏填的日期列表

    參數:
        user_id: 用戶 ID
        module_key: 模組 key (heartrate, weight, etc.)
        days_to_check: 要檢查幾天內的紀錄 (預設 30 天)

    回傳:
        漏填的日期列表，格式 ["2024-01-15", "2024-01-16", ...]
    """
    # 取得註冊日期
    created_at_str = get_user_created_date(user_id)
    created_at = datetime.strptime(created_at_str, "%Y-%m-%d").date()

    # 今天
    today = datetime.now().date()

    # 計算檢查起始日 (取註冊日和 N 天前的較晚者)
    check_start = today - timedelta(days=days_to_check)
    start_date = max(created_at, check_start)

    # 如果註冊日是今天，不需要檢查
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
        recorded_dates = get_recorded_dates(user_id, module_key)
        today_status[module_key] = today_str in recorded_dates

    return today_status

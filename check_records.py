from firebase_utils import db
from datetime import datetime, date, timedelta


# 所有需要檢查的資料類型
CHECK_TYPES = {
    "Sugar": {"node": "Sugar", "display_name": "血糖"},
    "Weight": {"node": "Weight", "display_name": "體重"},
    "HeartRate": {"node": "HeartRate", "display_name": "血壓心率"},
    "Temp": {"node": "Temp", "display_name": "體溫"},
    "Drug": {"node": "Drug", "display_name": "用藥"},
    "Life": {"node": "Life", "display_name": "生活紀錄"},
    "BodyFat": {"node": "BodyFat", "display_name": "體脂"},
    "Muscle": {"node": "Muscle", "display_name": "骨骼肌"},
    "BMI": {"node": "BMI", "display_name": "BMI"},
}


def _parse_date_from_filltime(filltime_str):
    """從 filltime 字串中取出日期"""
    try:
        return datetime.strptime(filltime_str[:10], "%Y-%m-%d").date()
    except:
        return None


def _get_recorded_dates(user_id, data_type):
    """取得某用戶某類型所有有紀錄的日期"""
    node = CHECK_TYPES[data_type]["node"]
    ref = db.reference(f'{node}/{user_id}')
    data = ref.get()

    if data is None:
        return set()

    dates = set()
    for record in data.values():
        filltime = record.get("filltime", "")
        record_date = _parse_date_from_filltime(filltime)
        if record_date:
            dates.add(record_date)

    return dates


def _get_first_record_date(user_id, data_type):
    """取得某用戶某類型第一筆紀錄的日期"""
    dates = _get_recorded_dates(user_id, data_type)
    if not dates:
        return None
    return min(dates)


def get_missing_dates(user_id, data_type, end_date=None):
    """
    取得某用戶某類型的漏填日期

    邏輯: 從第一筆紀錄日期 ~ end_date，找出沒有紀錄的日期

    參數:
        user_id: 使用者ID
        data_type: 資料類型 (Sugar, Weight, HeartRate, etc.)
        end_date: 結束日期 (date 物件，預設為今天)

    回傳:
        list of date (漏填的日期列表)
    """
    if data_type not in CHECK_TYPES:
        print(f"不支援的資料類型: {data_type}")
        return []

    if end_date is None:
        end_date = date.today()

    # 取得第一筆紀錄日期作為起始點
    first_date = _get_first_record_date(user_id, data_type)
    if first_date is None:
        return []  # 從沒填過，不提醒

    # 取得所有有紀錄的日期
    recorded_dates = _get_recorded_dates(user_id, data_type)

    # 找出漏填的日期
    missing = []
    current = first_date
    while current <= end_date:
        if current not in recorded_dates:
            missing.append(current)
        current += timedelta(days=1)

    return missing


def check_all_missing(user_id, end_date=None):
    """
    檢查某用戶所有類型的漏填情況

    參數:
        user_id: 使用者ID
        end_date: 結束日期 (date 物件，預設為今天)

    回傳:
        dict: {資料類型: [漏填日期列表]}
    """
    if end_date is None:
        end_date = date.today()

    result = {}

    for data_type, config in CHECK_TYPES.items():
        missing = get_missing_dates(user_id, data_type, end_date)
        if missing:
            result[data_type] = {
                "display_name": config["display_name"],
                "missing_dates": missing,
                "count": len(missing)
            }

    return result


def print_missing_report(user_id, end_date=None):
    """
    印出某用戶的漏填報告

    參數:
        user_id: 使用者ID
        end_date: 結束日期 (date 物件，預設為今天)
    """
    result = check_all_missing(user_id, end_date)

    if not result:
        print(f"用戶 {user_id} 沒有漏填紀錄!")
        return

    print(f"=== 用戶 {user_id} 漏填報告 ===\n")

    for data_type, info in result.items():
        display_name = info["display_name"]
        count = info["count"]
        missing_dates = info["missing_dates"]

        print(f"【{display_name}】漏填 {count} 天")

        # 最多顯示最近 5 天
        recent = sorted(missing_dates, reverse=True)[:5]
        for d in recent:
            print(f"  - {d.strftime('%Y-%m-%d')}")
        if count > 5:
            print(f"  ... 還有 {count - 5} 天")
        print()

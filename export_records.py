from firebase_utils import db
import pandas as pd
from datetime import datetime


# 所有資料類型及其欄位對應
DATA_TYPES = {
    "Sugar": {
        "node": "Sugar",
        "columns": ["id", "sugarlevel", "filltime"],
        "display_name": "血糖"
    },
    "Weight": {
        "node": "Weight",
        "columns": ["id", "wei", "wai", "filltime"],
        "display_name": "體重"
    },
    "HeartRate": {
        "node": "HeartRate",
        "columns": ["id", "mmHg1", "mmHg2", "bpm", "filltime"],
        "display_name": "血壓心率"
    },
    "Temp": {
        "node": "Temp",
        "columns": ["id", "temp", "filltime"],
        "display_name": "體溫"
    },
    "Drug": {
        "node": "Drug",
        "columns": ["id", "drugname", "drugpieces", "eattime", "filltime"],
        "display_name": "用藥"
    },
    "Life": {
        "node": "Life",
        "columns": ["id", "liferecord", "emotion", "filltime"],
        "display_name": "生活紀錄"
    },
    "BodyFat": {
        "node": "BodyFat",
        "columns": ["id", "bodyfat", "filltime"],
        "display_name": "體脂"
    },
    "Muscle": {
        "node": "Muscle",
        "columns": ["id", "muscle", "filltime"],
        "display_name": "骨骼肌"
    },
    "BMI": {
        "node": "BMI",
        "columns": ["id", "bmi", "filltime"],
        "display_name": "BMI"
    },
    "Symptom": {
        "node": "Symptom",
        "columns": ["id", "symptomname", "context", "duration", "symptomtime", "filltime"],
        "display_name": "不舒服的地方"
    },
    "Sleep": {
        "node": "Sleep",
        "columns": ["id", "sleeptime", "waketime", "duration", "quality", "tags", "filltime"],
        "display_name": "睡眠"
    },
}


def _parse_filltime(filltime_str):
    """解析 filltime 字串為 datetime"""
    try:
        # 處理有秒數的格式 "2024-01-20 14:30:00"
        if len(filltime_str) > 16:
            return datetime.strptime(filltime_str[:16], "%Y-%m-%d %H:%M")
        return datetime.strptime(filltime_str, "%Y-%m-%d %H:%M")
    except:
        return None


def _filter_by_date(records, start_date=None, end_date=None):
    """依日期篩選紀錄"""
    if start_date is None and end_date is None:
        return records

    filtered = []
    for record in records:
        filltime = record.get("filltime", "")
        record_date = _parse_filltime(filltime)

        if record_date is None:
            continue

        # 檢查日期範圍
        if start_date and record_date.date() < start_date:
            continue
        if end_date and record_date.date() > end_date:
            continue

        filtered.append(record)

    return filtered


def get_user_records(user_id, data_type, start_date=None, end_date=None):
    """
    取得特定用戶的特定類型紀錄

    參數:
        user_id: 使用者ID
        data_type: 資料類型 (Sugar, Weight, HeartRate, etc.)
        start_date: 開始日期 (date 物件，可選)
        end_date: 結束日期 (date 物件，可選)

    回傳:
        list of dict
    """
    if data_type not in DATA_TYPES:
        print(f"不支援的資料類型: {data_type}")
        return []

    node = DATA_TYPES[data_type]["node"]
    ref = db.reference(f'{node}/{user_id}')
    data = ref.get()

    if data is None:
        return []

    # 轉換為 list
    records = list(data.values())

    # 日期篩選
    records = _filter_by_date(records, start_date, end_date)

    # 依 filltime 排序
    records.sort(key=lambda x: x.get("filltime", ""))

    return records


def export_all_to_excel(user_id, filename=None, start_date=None, end_date=None):
    """
    匯出用戶所有健康紀錄到 Excel（每種資料一個 sheet）

    參數:
        user_id: 使用者ID
        filename: 輸出檔名（可選，預設為 {user_id}_健康紀錄.xlsx）
        start_date: 開始日期 (date 物件，可選)
        end_date: 結束日期 (date 物件，可選)

    範例:
        from datetime import date

        # 匯出全部
        export_all_to_excel("A001")

        # 匯出指定日期範圍
        export_all_to_excel("A001", start_date=date(2024, 1, 1), end_date=date(2024, 1, 31))
    """
    if filename is None:
        # 根據日期範圍產生檔名
        start_str = start_date.strftime("%Y%m%d") if start_date else "start"
        end_str = end_date.strftime("%Y%m%d") if end_date else "end"

        if start_date is None and end_date is None:
            filename = f"{user_id}_健康紀錄_全部.xlsx"
        else:
            filename = f"{user_id}_健康紀錄_{start_str}_{end_str}.xlsx"

    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        has_data = False

        for data_type, config in DATA_TYPES.items():
            records = get_user_records(user_id, data_type, start_date, end_date)

            if records:
                df = pd.DataFrame(records)
                # 重新排列欄位順序
                columns = [col for col in config["columns"] if col in df.columns]
                df = df[columns]

                # 使用中文名稱作為 sheet 名稱
                sheet_name = config["display_name"]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                has_data = True
                print(f"  {sheet_name}: {len(records)} 筆")

        if not has_data:
            # 建立空的 sheet 避免錯誤
            pd.DataFrame().to_excel(writer, sheet_name="無資料", index=False)
            print("沒有找到任何紀錄")

    print(f"\n匯出完成: {filename}")
    return filename

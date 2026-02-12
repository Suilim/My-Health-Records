import pandas as pd
from datetime import datetime
from export_records import DATA_TYPES


# 各模組要繪製的數值欄位
CHART_COLUMNS = {
    "HeartRate": {
        "columns": {"mmHg1": "收縮壓", "mmHg2": "舒張壓", "bpm": "心率"},
        "chart_type": "line",
    },
    "Weight": {
        "columns": {"wei": "體重(kg)", "wai": "腰圍(cm)"},
        "chart_type": "line",
    },
    "Sugar": {
        "columns": {"sugarlevel": "血糖(mg/dL)"},
        "chart_type": "line",
    },
    "Temp": {
        "columns": {"temp": "體溫(°C)"},
        "chart_type": "line",
    },
    "BodyFat": {
        "columns": {"bodyfat": "體脂(%)"},
        "chart_type": "line",
    },
    "Muscle": {
        "columns": {"muscle": "骨骼肌(kg)"},
        "chart_type": "line",
    },
    "BMI": {
        "columns": {"bmi": "BMI"},
        "chart_type": "line",
    },
    "Drug": {
        "columns": {},
        "chart_type": "drug",
    },
    "Life": {
        "columns": {},
        "chart_type": "life",
    },
}


def records_to_dataframe(records, data_type):
    """
    將記錄列表轉為 DataFrame，以 filltime 解析為 datetime index。

    回傳適合 st.line_chart 的 DataFrame（欄位已重命名為中文）。
    若無資料回傳 None。
    """
    if not records:
        return None

    df = pd.DataFrame(records)

    # 解析 filltime
    df["時間"] = df["filltime"].apply(_parse_filltime)
    df = df.dropna(subset=["時間"]).sort_values("時間")

    if df.empty:
        return None

    config = CHART_COLUMNS.get(data_type)
    if not config or not config["columns"]:
        return None

    # 只保留需要的欄位，轉為數值
    rename_map = config["columns"]
    cols_to_keep = list(rename_map.keys())
    for col in cols_to_keep:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    existing_cols = [c for c in cols_to_keep if c in df.columns]
    if not existing_cols:
        return None

    result = df[["時間"] + existing_cols].copy()
    result = result.rename(columns=rename_map)
    result = result.set_index("時間")

    return result


def get_summary_stats(df):
    """
    計算 DataFrame 各欄位的摘要統計。

    回傳 dict: {欄位名: {"平均": x, "最高": x, "最低": x, "筆數": n}}
    """
    if df is None or df.empty:
        return {}

    stats = {}
    for col in df.columns:
        numeric = df[col].dropna()
        if numeric.empty:
            continue
        stats[col] = {
            "平均": round(numeric.mean(), 1),
            "最高": round(numeric.max(), 1),
            "最低": round(numeric.min(), 1),
            "筆數": len(numeric),
        }
    return stats


def get_drug_compliance_table(records, start_date, end_date):
    """
    用藥記錄：建立每日 × 時段的服藥遵從表。

    回傳 DataFrame，index=日期(str), columns=["早","午","晚","睡前"]。
    值為 "V"（有吃）或 ""（沒吃）。
    若無資料回傳 None。
    """
    if not records:
        return None

    TIME_SLOTS = ["早", "午", "晚", "睡前"]

    # 收集每日每時段是否有紀錄
    compliance = {}
    for r in records:
        dt = _parse_filltime(r.get("filltime", ""))
        eattime = r.get("eattime", "").strip()
        if dt and eattime in TIME_SLOTS:
            date_str = dt.strftime("%m/%d")
            if date_str not in compliance:
                compliance[date_str] = {slot: "" for slot in TIME_SLOTS}
            compliance[date_str][eattime] = "V"

    if not compliance:
        return None

    # 按日期排序
    df = pd.DataFrame.from_dict(compliance, orient="index")
    df = df[TIME_SLOTS]  # 確保欄位順序
    df.index.name = "日期"
    df = df.sort_index()

    return df


def get_life_emotion_counts(records):
    """
    生活紀錄：計算情緒分布。

    回傳 DataFrame，index=情緒, columns=["次數"]。
    若無資料回傳 None。
    """
    if not records:
        return None

    emotions = [r.get("emotion", "未記錄") for r in records if r.get("emotion")]
    if not emotions:
        return None

    df = pd.DataFrame({"情緒": emotions})
    counts = df.groupby("情緒").size().reset_index(name="次數")
    counts = counts.set_index("情緒")

    return counts


def _parse_filltime(filltime_str):
    """解析 filltime 字串為 datetime"""
    if not filltime_str:
        return None
    try:
        # 處理有秒數的格式 "2024-01-20 14:30:00"
        if len(filltime_str) > 16:
            return datetime.strptime(filltime_str[:16], "%Y-%m-%d %H:%M")
        return datetime.strptime(filltime_str, "%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return None

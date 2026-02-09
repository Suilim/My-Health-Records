"""
日曆檢視相關工具函數
用於歷史紀錄總覽頁面
"""

from firebase_utils import db
from settings_utils import get_enabled_modules, MODULE_PATHS, MODULE_NAMES
from export_records import DATA_TYPES, _parse_filltime
from datetime import datetime, date
import streamlit as st
import calendar


@st.cache_data(ttl=300)  # 快取 5 分鐘
def get_month_recorded_dates(user_id: str, year: int, month: int) -> set:
    """
    取得指定月份有記錄的日期集合

    使用 shallow=True 只取 keys,減少傳輸量

    參數:
        user_id: 使用者 ID
        year: 年份
        month: 月份 (1-12)

    回傳:
        set of date objects - 該月份有記錄的日期集合
    """
    recorded_dates = set()
    enabled_modules = get_enabled_modules(user_id)

    # 月份的起始和結束日期字串 (用於比對)
    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1)
    else:
        month_end = date(year, month + 1, 1)

    for module_key in enabled_modules:
        # 取得 Firebase 節點名稱
        node_name = MODULE_PATHS.get(module_key)
        if not node_name:
            continue

        try:
            ref = db.reference(f'{node_name}/{user_id}')
            # shallow=True 只取 keys,不取值,大幅減少傳輸量
            data = ref.get(shallow=True)

            if data:
                # data 是 {filltime: True, ...} 的字典
                for filltime_key in data.keys():
                    record_date = _parse_filltime(filltime_key)
                    if record_date:
                        record_date_obj = record_date.date()
                        # 檢查是否在指定月份內
                        if month_start <= record_date_obj < month_end:
                            recorded_dates.add(record_date_obj)
        except Exception as e:
            # 忽略錯誤,繼續處理其他模組
            print(f"讀取 {module_key} 時發生錯誤: {e}")
            continue

    return recorded_dates


def get_day_all_records(user_id: str, target_date: date) -> dict:
    """
    取得指定日期的所有模組記錄

    優先從 session_state 快取讀取,若無則查詢 Firebase

    參數:
        user_id: 使用者 ID
        target_date: 目標日期 (date 物件)

    回傳:
        dict {
            'HeartRate': [record1, record2, ...],
            'Drug': [...],
            ...
        }
    """
    # 建立快取鍵
    cache_key = f"day_records_{user_id}_{target_date.strftime('%Y%m%d')}"

    # 檢查 session_state 快取
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    # 無快取,從 Firebase 查詢
    day_records = {}
    enabled_modules = get_enabled_modules(user_id)

    # 目標日期字串 (YYYY-MM-DD)
    target_date_str = target_date.strftime('%Y-%m-%d')

    for module_key in enabled_modules:
        node_name = MODULE_PATHS.get(module_key)
        if not node_name:
            continue

        try:
            ref = db.reference(f'{node_name}/{user_id}')
            data = ref.get()

            if data:
                # 篩選該日期的記錄
                day_data = []
                for filltime_key, record in data.items():
                    # 檢查 filltime 是否以目標日期開頭
                    if filltime_key.startswith(target_date_str):
                        day_data.append(record)

                if day_data:
                    # 按時間排序
                    day_data.sort(key=lambda x: x.get('filltime', ''))
                    day_records[node_name] = day_data
        except Exception as e:
            print(f"讀取 {module_key} 日記錄時發生錯誤: {e}")
            continue

    # 存入 session_state 快取
    st.session_state[cache_key] = day_records

    return day_records


def format_record_for_display(record: dict, module_type: str) -> str:
    """
    格式化記錄供顯示

    參數:
        record: 記錄字典
        module_type: 模組類型 (Firebase 節點名稱,如 'HeartRate', 'Drug' 等)

    回傳:
        格式化後的字串
    """
    filltime = record.get('filltime', '')

    # 提取時間部分 (HH:MM)
    try:
        time_part = filltime.split(' ')[1][:5]  # "14:30"
    except:
        time_part = ''

    # 根據模組類型格式化內容
    if module_type == 'HeartRate':
        mmHg1 = record.get('mmHg1', '')
        mmHg2 = record.get('mmHg2', '')
        bpm = record.get('bpm', '')
        return f"{time_part} - {mmHg1}/{mmHg2} mmHg, {bpm} bpm"

    elif module_type == 'Sugar':
        level = record.get('sugarlevel', '')
        return f"{time_part} - {level} mg/dL"

    elif module_type == 'Weight':
        wei = record.get('wei', '')
        wai = record.get('wai', '')
        return f"{time_part} - 體重 {wei} kg, 腰圍 {wai} cm"

    elif module_type == 'BodyFat':
        bodyfat = record.get('bodyfat', '')
        return f"{time_part} - {bodyfat}%"

    elif module_type == 'Muscle':
        muscle = record.get('muscle', '')
        return f"{time_part} - {muscle} kg"

    elif module_type == 'BMI':
        bmi = record.get('bmi', '')
        return f"{time_part} - {bmi}"

    elif module_type == 'Temp':
        temp = record.get('temp', '')
        return f"{time_part} - {temp} °C"

    elif module_type == 'Drug':
        drugname = record.get('drugname', '')
        pieces = record.get('drugpieces', '')
        eattime = record.get('eattime', '')
        return f"{time_part} {eattime} - {drugname} × {pieces}"

    elif module_type == 'Life':
        liferecord = record.get('liferecord', '')
        emotion = record.get('emotion', '')
        emotion_emoji = {
            '開心': '😊',
            '平靜': '😌',
            '疲累': '😔',
            '生氣': '😠',
            '焦慮': '😰'
        }.get(emotion, '')
        return f"{time_part} - {liferecord} {emotion_emoji}"

    else:
        # 未知模組類型,顯示原始資料
        return f"{time_part} - {str(record)}"


def get_module_display_name(module_type: str) -> str:
    """
    取得模組的中文顯示名稱

    參數:
        module_type: Firebase 節點名稱 (如 'HeartRate')

    回傳:
        中文名稱 (如 '血壓心率')
    """
    # 從 DATA_TYPES 查詢
    for data_type, config in DATA_TYPES.items():
        if config['node'] == module_type:
            return config['display_name']

    # 找不到,返回原始名稱
    return module_type


def get_module_emoji(module_type: str) -> str:
    """
    取得模組的 emoji 圖示

    參數:
        module_type: Firebase 節點名稱 (如 'HeartRate')

    回傳:
        emoji 字串
    """
    emoji_map = {
        'HeartRate': '❤️',
        'Sugar': '🩸',
        'Weight': '⚖️',
        'BodyFat': '📊',
        'Muscle': '💪',
        'BMI': '📏',
        'Temp': '🌡️',
        'Drug': '💊',
        'Life': '🏃'
    }
    return emoji_map.get(module_type, '📝')


def get_calendar_matrix(year: int, month: int) -> list:
    """
    取得月曆的矩陣結構

    參數:
        year: 年份
        month: 月份 (1-12)

    回傳:
        list of list - 每個子列表代表一週,包含 date 物件或 None
        例如: [
            [None, None, date(2025,2,1), date(2025,2,2), ...],
            [date(2025,2,9), date(2025,2,10), ...],
            ...
        ]
    """
    cal = calendar.monthcalendar(year, month)

    # 轉換為 date 物件
    matrix = []
    for week in cal:
        week_dates = []
        for day in week:
            if day == 0:
                week_dates.append(None)
            else:
                week_dates.append(date(year, month, day))
        matrix.append(week_dates)

    return matrix


def clear_day_cache(user_id: str, target_date: date):
    """
    清除指定日期的快取

    用於新增/刪除記錄後,強制重新載入該日數據

    參數:
        user_id: 使用者 ID
        target_date: 目標日期
    """
    cache_key = f"day_records_{user_id}_{target_date.strftime('%Y%m%d')}"
    if cache_key in st.session_state:
        del st.session_state[cache_key]


def clear_month_cache(user_id: str, year: int, month: int):
    """
    清除指定月份的快取

    用於新增記錄後,強制重新載入月曆標記

    參數:
        user_id: 使用者 ID
        year: 年份
        month: 月份
    """
    # 清除 Streamlit cache_data 的快取
    get_month_recorded_dates.clear()

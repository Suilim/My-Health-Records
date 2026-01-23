from firebase_utils import db
import datetime


def _get_current_filltime():
    """取得當前時間作為 filltime"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


# ========== 用戶 ==========
def create_user(user_id, name, password):
    """
    新增用戶
    路徑: User/{userId}
    """
    ref = db.reference(f'User/{user_id}')
    ref.set({
        "id": str(user_id),
        "name": str(name),
        "password": str(password),
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d")
    })
    print(f"用戶 {user_id} 建立完成")

    # 初始化用戶設定 - 預設啟用所有模組
    settings_ref = db.reference(f'Settings/{user_id}')
    settings_ref.set({
        "modules": {
            "heartrate": True,   # 血壓心率
            "weight": True,      # 體重
            "sugar": True,       # 血糖
            "temp": True,        # 體溫
            "drug": True,        # 用藥
            "life": True         # 生活紀錄
        }
    })
    print(f"用戶 {user_id} 設定初始化完成")


# ========== 血糖 ==========
def add_sugar_record(user_id, sugar_level, filltime=None):
    """
    新增血糖紀錄
    路徑: Sugar/{userId}/{filltime}
    """
    if filltime is None:
        filltime = _get_current_filltime()

    ref = db.reference(f'Sugar/{user_id}/{filltime}')
    ref.set({
        "id": str(user_id),
        "sugarlevel": str(sugar_level),
        "filltime": str(filltime)
    })
    print(f"血糖紀錄寫入完成: {user_id} - {sugar_level}")


# ========== 體重 ==========
def add_weight_record(user_id, weight, waist, filltime=None):
    """
    新增體重紀錄
    路徑: Weight/{userId}/{filltime}
    """
    if filltime is None:
        filltime = _get_current_filltime()

    ref = db.reference(f'Weight/{user_id}/{filltime}')
    ref.set({
        "id": str(user_id),
        "wei": str(weight),
        "wai": str(waist),
        "filltime": str(filltime)
    })
    print(f"體重紀錄寫入完成: {user_id} - 體重:{weight} 腰圍:{waist}")


# ========== 血壓心率 ==========
def add_heartrate_record(user_id, mmHg1, mmHg2, bpm, filltime=None):
    """
    新增血壓心率紀錄
    路徑: HeartRate/{userId}/{filltime}

    參數:
        mmHg1: 收縮壓
        mmHg2: 舒張壓
        bpm: 心跳
    """
    if filltime is None:
        filltime = _get_current_filltime()

    ref = db.reference(f'HeartRate/{user_id}/{filltime}')
    ref.set({
        "id": str(user_id),
        "mmHg1": str(mmHg1),
        "mmHg2": str(mmHg2),
        "bpm": str(bpm),
        "filltime": str(filltime)
    })
    print(f"血壓心率紀錄寫入完成: {user_id} - {mmHg1}/{mmHg2} mmHg, {bpm} bpm")


# ========== 體溫 ==========
def add_temp_record(user_id, temp, filltime=None):
    """
    新增體溫紀錄
    路徑: Temp/{userId}/{filltime}
    """
    if filltime is None:
        filltime = _get_current_filltime()

    ref = db.reference(f'Temp/{user_id}/{filltime}')
    ref.set({
        "id": str(user_id),
        "temp": str(temp),
        "filltime": str(filltime)
    })
    print(f"體溫紀錄寫入完成: {user_id} - {temp}°C")


# ========== 用藥 ==========
def add_drug_record(user_id, drug_name, drug_pieces, eat_time, filltime=None):
    """
    新增用藥紀錄
    路徑: Drug/{userId}/{filltime}

    參數:
        drug_name: 藥名
        drug_pieces: 藥量/顆數
        eat_time: 服藥時間
    """
    if filltime is None:
        filltime = _get_current_filltime()

    ref = db.reference(f'Drug/{user_id}/{filltime}')
    ref.set({
        "id": str(user_id),
        "drugname": str(drug_name),
        "drugpieces": str(drug_pieces),
        "eattime": str(eat_time),
        "filltime": str(filltime)
    })
    print(f"用藥紀錄寫入完成: {user_id} - {drug_name} x {drug_pieces}")


def update_drug_record(user_id, filltime, drug_name, drug_pieces, eat_time):
    """
    更新用藥紀錄
    路徑: Drug/{userId}/{filltime}
    """
    ref = db.reference(f'Drug/{user_id}/{filltime}')
    ref.update({
        "drugname": str(drug_name),
        "drugpieces": str(drug_pieces),
        "eattime": str(eat_time)
    })
    print(f"用藥紀錄更新完成: {user_id} - {drug_name}")


def delete_drug_record(user_id, filltime):
    """
    刪除用藥紀錄
    路徑: Drug/{userId}/{filltime}
    """
    ref = db.reference(f'Drug/{user_id}/{filltime}')
    ref.delete()
    print(f"用藥紀錄刪除完成: {user_id} - {filltime}")


def add_drug_records_batch(user_id, drugs, filltime=None):
    """
    批次新增多筆用藥紀錄（同一時間點）
    路徑: Drug/{userId}/{filltime}:XX (自動加秒數避免衝突)

    參數:
        user_id: 使用者ID
        drugs: list of dict，每個 dict 包含:
            - name: 藥名
            - pieces: 藥量/顆數
            - eattime: 服藥時間 (早/午/晚/睡)
        filltime: 填寫時間（可選，預設當前時間）

    範例:
        add_drug_records_batch("A001", [
            {"name": "降血糖藥", "pieces": 1, "eattime": "早"},
            {"name": "降血壓藥", "pieces": 2, "eattime": "早晚"},
            {"name": "維他命", "pieces": 1, "eattime": "早"},
        ])
    """
    if filltime is None:
        filltime = _get_current_filltime()

    for i, drug in enumerate(drugs):
        # 加上秒數避免 key 衝突: "2024-01-20 14:30:00", "2024-01-20 14:30:01", ...
        unique_filltime = f"{filltime}:{i:02d}"

        ref = db.reference(f'Drug/{user_id}/{unique_filltime}')
        ref.set({
            "id": str(user_id),
            "drugname": str(drug["name"]),
            "drugpieces": str(drug["pieces"]),
            "eattime": str(drug["eattime"]),
            "filltime": str(unique_filltime)
        })
        print(f"用藥紀錄寫入完成: {user_id} - {drug['name']} x {drug['pieces']}")

    print(f"批次寫入完成，共 {len(drugs)} 筆用藥紀錄")


# ========== 生活紀錄 ==========
def add_life_record(user_id, life_record, emotion, filltime=None):
    """
    新增生活紀錄
    路徑: Life/{userId}/{filltime}

    參數:
        life_record: 生活紀錄內容
        emotion: 情緒
    """
    if filltime is None:
        filltime = _get_current_filltime()

    ref = db.reference(f'Life/{user_id}/{filltime}')
    ref.set({
        "id": str(user_id),
        "liferecord": str(life_record),
        "emotion": str(emotion),
        "filltime": str(filltime)
    })
    print(f"生活紀錄寫入完成: {user_id} - {emotion}")


# ========== 體脂 ==========
def add_bodyfat_record(user_id, bodyfat, filltime=None):
    """
    新增體脂紀錄
    路徑: BodyFat/{userId}/{filltime}

    參數:
        bodyfat: 體脂率 (%)
    """
    if filltime is None:
        filltime = _get_current_filltime()

    ref = db.reference(f'BodyFat/{user_id}/{filltime}')
    ref.set({
        "id": str(user_id),
        "bodyfat": str(bodyfat),
        "filltime": str(filltime)
    })
    print(f"體脂紀錄寫入完成: {user_id} - {bodyfat}%")


# ========== 骨骼肌 ==========
def add_muscle_record(user_id, muscle, filltime=None):
    """
    新增骨骼肌紀錄
    路徑: Muscle/{userId}/{filltime}

    參數:
        muscle: 骨骼肌率 (%)
    """
    if filltime is None:
        filltime = _get_current_filltime()

    ref = db.reference(f'Muscle/{user_id}/{filltime}')
    ref.set({
        "id": str(user_id),
        "muscle": str(muscle),
        "filltime": str(filltime)
    })
    print(f"骨骼肌紀錄寫入完成: {user_id} - {muscle}%")


# ========== BMI ==========
def add_bmi_record(user_id, bmi, filltime=None):
    """
    新增 BMI 紀錄
    路徑: BMI/{userId}/{filltime}

    參數:
        bmi: BMI 值
    """
    if filltime is None:
        filltime = _get_current_filltime()

    ref = db.reference(f'BMI/{user_id}/{filltime}')
    ref.set({
        "id": str(user_id),
        "bmi": str(bmi),
        "filltime": str(filltime)
    })
    print(f"BMI 紀錄寫入完成: {user_id} - {bmi}")

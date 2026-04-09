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


def update_user_name(user_id, new_name):
    """
    更新用戶名稱
    路徑: User/{userId}
    """
    ref = db.reference(f'User/{user_id}')
    ref.update({"name": str(new_name)})
    print(f"用戶 {user_id} 名稱更新為: {new_name}")


def update_user_nickname(user_id, nickname):
    """
    更新用戶暱稱（顯示於登入按鈕，不含真名）
    路徑: User/{userId}
    """
    ref = db.reference(f'User/{user_id}')
    ref.update({"nickname": str(nickname)})
    print(f"用戶 {user_id} 暱稱更新為: {nickname}")


def delete_user_all_data(user_id):
    """
    刪除使用者帳號及所有資料
    路徑: User/{userId}、Settings/{userId}、各資料節點/{userId}
    """
    data_nodes = [
        "Sugar", "Weight", "BodyFat", "Muscle", "BMI",
        "HeartRate", "Temp", "Drug", "Life", "Symptom", "Sleep",
        "Food", "Drink"
    ]
    for node in data_nodes:
        db.reference(f'{node}/{user_id}').delete()
    db.reference(f'Settings/{user_id}').delete()
    db.reference(f'User/{user_id}').delete()
    print(f"用戶 {user_id} 帳號及所有資料已刪除")

    # 初始化用戶設定 - 預設啟用所有模組
    settings_ref = db.reference(f'Settings/{user_id}')
    settings_ref.set({
        "modules": {
            "heartrate": True,   # 血壓心率
            "weight": True,      # 體重
            "sugar": True,       # 血糖
            "temp": True,        # 體溫
            "drug": True,        # 用藥
            "life": True,        # 生活紀錄
            "symptom": True,     # 症狀
            "sleep": True        # 睡眠

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

# ========== 症狀 ==========
def add_symptom_record(user_id, symptom_name, duration, symptom_time, context=None, filltime=None):
    """
    新增症狀紀錄
    路徑: Symptom/{userId}/{filltime}

    參數:
        symptom_name: 症狀
        duration: 持續時間
        symptom_time: 發作時間
        context: 發生情境（可選，例如 "上班, 太吵"）
    """
    if filltime is None:
        filltime = _get_current_filltime()

    ref = db.reference(f'Symptom/{user_id}/{filltime}')
    ref.set({
        "id": str(user_id),
        "symptomname": str(symptom_name),
        "duration": str(duration),
        "symptomtime": str(symptom_time),
        "context": str(context) if context else "",
        "filltime": str(filltime)
    })
    print(f"症狀紀錄寫入完成: {user_id} - {symptom_name} {duration}")


def update_symptom_record(user_id, filltime, symptom_name, duration, symptom_time, context=None):
    """
    更新症狀紀錄
    路徑: Symptom/{userId}/{filltime}
    """
    ref = db.reference(f'Symptom/{user_id}/{filltime}')
    ref.update({
        "symptomname": str(symptom_name),
        "duration": str(duration),
        "symptomtime": str(symptom_time),
        "context": str(context) if context else ""
    })
    print(f"症狀紀錄更新完成: {user_id} - {symptom_name}")


def delete_symptom_record(user_id, filltime):
    """
    刪除症狀紀錄
    路徑: Symptom/{userId}/{filltime}
    """
    ref = db.reference(f'Symptom/{user_id}/{filltime}')
    ref.delete()
    print(f"症狀紀錄刪除完成: {user_id} - {filltime}")


# ========== 睡眠 ==========
def add_sleep_record(user_id, sleep_time, wake_time, duration, quality, tags, filltime=None):
    """
    新增睡眠紀錄
    路徑: Sleep/{userId}/{filltime}

    參數:
        sleep_time: 睡覺時間（字串，例如 "23:30"）
        wake_time: 起床時間（字串，例如 "07:00"）
        duration: 睡眠時數（float，例如 7.5）
        quality: 睡眠品質（int 1-5，對應 😫😕😐😊😄）
        tags: 快速標籤（字串，逗號分隔，例如 "一直做夢, 半夜醒來"）
    """
    if filltime is None:
        filltime = _get_current_filltime()

    ref = db.reference(f'Sleep/{user_id}/{filltime}')
    ref.set({
        "id": str(user_id),
        "sleeptime": str(sleep_time),
        "waketime": str(wake_time),
        "duration": str(duration),
        "quality": str(quality),
        "tags": str(tags) if tags else "",
        "filltime": str(filltime)
    })
    print(f"睡眠紀錄寫入完成: {user_id} - {sleep_time}~{wake_time} ({duration}h)")


def delete_sleep_record(user_id, filltime):
    """
    刪除睡眠紀錄
    路徑: Sleep/{userId}/{filltime}
    """
    ref = db.reference(f'Sleep/{user_id}/{filltime}')
    ref.delete()
    print(f"睡眠紀錄刪除完成: {user_id} - {filltime}")


def add_symptom_records_batch(user_id, symptoms, filltime=None):
    """
    批次新增多筆用藥紀錄（同一時間點）
    路徑: Symptom/{userId}/{filltime}:XX (自動加秒數避免衝突)

    參數:
        user_id: 使用者ID
        symptoms: list of dict，每個 dict 包含:
            - name: 症狀名稱
            - duration: 持續時間（很快就過了/一段時間/很久）
            - symptomtime: 確切時間點
            - context: 發生情境（可選）
        filltime: 填寫時間（可選，預設當前時間）

    範例:
        add_symptom_records_batch("A001", [
            {"name": "頭痛", "duration": "一段時間", "symptomtime": "2024-01-20 14:30", "context": "上班"},
            {"name": "皮膚乾癢", "duration": "很久", "symptomtime": "2024-01-20 21:00"},
        ])
    """
    if filltime is None:
        filltime = _get_current_filltime()

    for i, symptom in enumerate(symptoms):
        # 加上秒數避免 key 衝突: "2024-01-20 14:30:00", "2024-01-20 14:30:01", ...
        unique_filltime = f"{filltime}:{i:02d}"

        ref = db.reference(f'Symptom/{user_id}/{unique_filltime}')
        ref.set({
            "id": str(user_id),
            "symptomname": str(symptom["name"]),
            "duration": str(symptom["duration"]),
            "symptomtime": str(symptom["symptomtime"]),
            "context": str(symptom["context"]) if symptom.get("context") else "",
            "filltime": str(unique_filltime)
        })
        print(f"症狀紀錄寫入完成: {user_id} - {symptom['name']} / {symptom['duration']}")

    print(f"批次寫入完成，共 {len(symptoms)} 筆用藥紀錄")


# ========== 飲食 ==========
def add_food_record(user_id, food_name, food_pieces, eat_time, filltime=None):
    """
    新增食物紀錄
    路徑: Food/{userId}/{filltime}

    參數:
        food_name: 食物名稱
        food_pieces: 份量（份）
        eat_time: 進食時間（早/午/晚/點心）
    """
    if filltime is None:
        filltime = _get_current_filltime()

    ref = db.reference(f'Food/{user_id}/{filltime}')
    ref.set({
        "id": str(user_id),
        "foodname": str(food_name),
        "foodpieces": str(food_pieces),
        "eattime": str(eat_time),
        "filltime": str(filltime)
    })
    print(f"食物紀錄寫入完成: {user_id} - {food_name} x {food_pieces} 份")


def update_food_record(user_id, filltime, food_name, food_pieces, eat_time):
    """
    更新食物紀錄
    路徑: Food/{userId}/{filltime}
    """
    ref = db.reference(f'Food/{user_id}/{filltime}')
    ref.update({
        "foodname": str(food_name),
        "foodpieces": str(food_pieces),
        "eattime": str(eat_time)
    })
    print(f"食物紀錄更新完成: {user_id} - {food_name}")


def delete_food_record(user_id, filltime):
    """
    刪除食物紀錄
    路徑: Food/{userId}/{filltime}
    """
    ref = db.reference(f'Food/{user_id}/{filltime}')
    ref.delete()
    print(f"食物紀錄刪除完成: {user_id} - {filltime}")


def add_food_records_batch(user_id, foods, filltime=None):
    """
    批次新增多筆食物紀錄（同一時間點）
    路徑: Food/{userId}/{filltime}:XX (自動加秒數避免衝突)

    參數:
        user_id: 使用者ID
        foods: list of dict，每個 dict 包含:
            - name: 食物名稱
            - pieces: 份量（份）
            - eattime: 進食時間 (早/午/晚/點心)
        filltime: 填寫時間（可選，預設當前時間）

    範例:
        add_food_records_batch("A001", [
            {"name": "白飯", "pieces": 1, "eattime": "早"},
            {"name": "蛋", "pieces": 1, "eattime": "早"},
        ])
    """
    if filltime is None:
        filltime = _get_current_filltime()

    for i, food in enumerate(foods):
        # 加上秒數避免 key 衝突
        unique_filltime = f"{filltime}:{i:02d}"

        ref = db.reference(f'Food/{user_id}/{unique_filltime}')
        ref.set({
            "id": str(user_id),
            "foodname": str(food["name"]),
            "foodpieces": str(food["pieces"]),
            "eattime": str(food["eattime"]),
            "filltime": str(unique_filltime)
        })
        print(f"食物紀錄寫入完成: {user_id} - {food['name']} x {food['pieces']} 份")

    print(f"批次寫入完成，共 {len(foods)} 筆食物紀錄")


# ========== 飲品 ==========
def add_drink_record(user_id, drink_name, cups, eat_time, filltime=None):
    """
    新增飲品紀錄
    路徑: Drink/{userId}/{filltime}

    參數:
        drink_name: 飲品名稱（如「白開水」、「咖啡」等）
        cups: 杯數（數字）
        eat_time: 進食時間（早/午/晚/點心）
    """
    if filltime is None:
        filltime = _get_current_filltime()

    ref = db.reference(f'Drink/{user_id}/{filltime}')
    ref.set({
        "id": str(user_id),
        "drinkname": str(drink_name),
        "cups": str(cups),
        "eattime": str(eat_time),
        "filltime": str(filltime)
    })
    print(f"飲品紀錄寫入完成: {user_id} - {drink_name} {cups} 杯")


def update_drink_record(user_id, filltime, drink_name, cups, eat_time):
    """
    更新飲品紀錄
    路徑: Drink/{userId}/{filltime}
    """
    ref = db.reference(f'Drink/{user_id}/{filltime}')
    ref.update({
        "drinkname": str(drink_name),
        "cups": str(cups),
        "eattime": str(eat_time)
    })
    print(f"飲品紀錄更新完成: {user_id} - {drink_name}")


def delete_drink_record(user_id, filltime):
    """
    刪除飲品紀錄
    路徑: Drink/{userId}/{filltime}
    """
    ref = db.reference(f'Drink/{user_id}/{filltime}')
    ref.delete()
    print(f"飲品紀錄刪除完成: {user_id} - {filltime}")


def add_drink_records_batch(user_id, drinks, filltime=None):
    """
    批次新增多筆飲品紀錄（同一時間點）
    路徑: Drink/{userId}/{filltime}:XX (自動加秒數避免衝突)

    參數:
        user_id: 使用者ID
        drinks: list of dict，每個 dict 包含:
            - name: 飲品名稱
            - cups: 杯數（數字）
            - eattime: 進食時間 (早/午/晚/點心)
        filltime: 填寫時間（可選，預設當前時間）

    範例:
        add_drink_records_batch("A001", [
            {"name": "白開水", "cups": 2, "eattime": "早"},
            {"name": "咖啡", "cups": 1, "eattime": "午"},
        ])
    """
    if filltime is None:
        filltime = _get_current_filltime()

    for i, drink in enumerate(drinks):
        # 加上秒數避免 key 衝突
        unique_filltime = f"{filltime}:{i:02d}"

        ref = db.reference(f'Drink/{user_id}/{unique_filltime}')
        ref.set({
            "id": str(user_id),
            "drinkname": str(drink["name"]),
            "cups": str(drink["cups"]),
            "eattime": str(drink["eattime"]),
            "filltime": str(unique_filltime)
        })
        print(f"飲品紀錄寫入完成: {user_id} - {drink['name']} {drink['cups']} 杯")

    print(f"批次寫入完成，共 {len(drinks)} 筆飲品紀錄")


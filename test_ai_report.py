"""
測試腳本：直接印出餵給 LLM 的週塊文字，不需要 Firebase 連線。
執行：uv run python test_ai_report.py
"""

from datetime import date, timedelta
from collections import defaultdict


# ── 把需要的函式複製過來（不依賴 Firebase）──

def _week_label(d):
    week_num = (d.day - 1) // 7 + 1
    return f"{d.month}月第{week_num}週"

def _week_range_label(week_start, week_end):
    return f"{week_start.month}/{week_start.day}～{week_end.month}/{week_end.day}"

def _iter_weeks(start_date, end_date):
    current = start_date - timedelta(days=start_date.weekday())
    while current <= end_date:
        week_end = min(current + timedelta(days=6), end_date)
        week_start = max(current, start_date)
        yield week_start, week_end
        current += timedelta(days=7)

def _dates_in_range(week_start, week_end):
    d = week_start
    while d <= week_end:
        yield d
        d += timedelta(days=1)


def _block_drug_mock(required_slots, recorded_slots, prn_records, week_start, week_end):
    lines = []
    if required_slots:
        missing_entries = []
        for d in _dates_in_range(week_start, week_end):
            d_str = d.strftime("%Y-%m-%d")
            filled = recorded_slots.get(d_str, set())
            for slot in required_slots:
                if slot not in filled:
                    missing_entries.append(f"{d.month}/{d.day} {slot}❌")
        if missing_entries:
            lines.append(f"用藥：{'、'.join(missing_entries)}")
        else:
            lines.append("用藥：全週正常 ✅")

    prn_drugs = []
    for d, name, pieces in prn_records:
        if week_start <= d <= week_end:
            prn_drugs.append(f"{d.month}/{d.day} {name} {pieces}顆")
    if prn_drugs:
        lines.append(f"需要時：{'、'.join(prn_drugs)}")
    return lines


def _block_symptom_mock(symptom_records, week_start, week_end):
    symptom_data = defaultdict(lambda: {"count": 0, "times": []})
    for d, name, occur_time in symptom_records:
        if week_start <= d <= week_end and name != "（無症狀）":
            symptom_data[name]["count"] += 1
            if occur_time:
                symptom_data[name]["times"].append(occur_time)
    if not symptom_data:
        return []
    parts = []
    for name, info in symptom_data.items():
        times = info["times"]
        if times:
            most_common = max(set(times), key=times.count)
            parts.append(f"{name}（{info['count']}次，{most_common}）")
        else:
            parts.append(f"{name}（{info['count']}次）")
    return [f"不舒服：{'、'.join(parts)}"]


def _block_weight_mock(weight_records, week_start, week_end):
    week_weights = [(d, w) for d, w in weight_records if week_start <= d <= week_end]
    if not week_weights:
        return []
    week_weights.sort()
    if len(week_weights) == 1:
        return [f"體重：{week_weights[0][1]} kg"]
    return [f"體重：{week_weights[0][1]} → {week_weights[-1][1]} kg"]


def _block_life_mock(life_records, week_start, week_end):
    emotions = []
    diaries = []
    for d, emotion_list, diary in life_records:
        if week_start <= d <= week_end:
            emotions.extend(emotion_list)
            if diary:
                diaries.append(diary)
    if not emotions and not diaries:
        return []
    parts = []
    if emotions:
        ec = defaultdict(int)
        for e in emotions:
            ec[e] += 1
        parts.append(f"情緒〔{'、'.join(f'{e}×{n}' for e, n in ec.items())}〕")
    if diaries:
        parts.append(f"日記：{' '.join(diaries)}")
    return [f"生活：{'　'.join(parts)}"]


# ── 模擬資料 ──────────────────────────────────────────────

start_date = date(2026, 3, 1)
end_date = date(2026, 3, 21)

# 設定時段
required_slots = ["早", "午", "晚"]

# 已填時段（3/5 午漏服、3/12 晚漏服）
recorded_slots = {}
for d_offset in range(21):
    d = start_date + timedelta(days=d_offset)
    d_str = d.strftime("%Y-%m-%d")
    slots = {"早", "午", "晚"}
    if d == date(2026, 3, 5):
        slots = {"早", "晚"}       # 午漏服
    if d == date(2026, 3, 12):
        slots = {"早", "午"}       # 晚漏服
    recorded_slots[d_str] = slots

# 需要時用藥
prn_records = [
    (date(2026, 3, 5), "便秘藥", 1),
    (date(2026, 3, 14), "止痛藥", 1),
]

# 不舒服紀錄
symptom_records = [
    (date(2026, 3, 3), "頭痛", "早"),
    (date(2026, 3, 4), "頭痛", "早"),
    (date(2026, 3, 5), "頭痛", "早"),
    (date(2026, 3, 5), "胃痛", "晚"),
    (date(2026, 3, 13), "失眠", ""),
    (date(2026, 3, 20), "頭暈", "早"),
]

# 體重（每天）
weight_records = [
    (start_date + timedelta(days=i), round(68.5 + i * 0.05, 1))
    for i in range(21)
]

# 生活紀錄
life_records = [
    (date(2026, 3, 3), ["焦慮", "平靜"], "最近壓力有點大，工作很多事情要處理"),
    (date(2026, 3, 5), ["難過"], "月經來了，頭很痛，整天都不舒服"),
    (date(2026, 3, 10), ["平靜", "開心"], "今天天氣很好，出去走走心情好一些"),
    (date(2026, 3, 14), ["焦慮"], "睡不好，一直想東想西"),
    (date(2026, 3, 18), ["開心", "平靜"], "家人來探望，心情好很多"),
]

# ── 產生週塊輸出 ─────────────────────────────────────────

blocks = []
for week_start, week_end in _iter_weeks(start_date, end_date):
    label = f"### {_week_label(week_start)}（{_week_range_label(week_start, week_end)}）"
    lines = [label]
    lines += _block_drug_mock(required_slots, recorded_slots, prn_records, week_start, week_end)
    lines += _block_symptom_mock(symptom_records, week_start, week_end)
    lines += _block_weight_mock(weight_records, week_start, week_end)
    lines += _block_life_mock(life_records, week_start, week_end)
    if len(lines) > 1:
        blocks.append("\n".join(lines))

output = "\n\n".join(blocks)
print(output)
print(f"\n{'='*50}")
print(f"總字數：{len(output)} 字")

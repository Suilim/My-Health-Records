from datetime import date, timedelta
from collections import defaultdict
from io import BytesIO

import streamlit as st
from google import genai
from google.genai import types
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from export_records import get_user_records


def _week_label(d: date) -> str:
    """回傳該日期所在週的標籤，例如 '2026/01 第2週'"""
    first_day = date(d.year, d.month, 1)
    week_num = (d.day - 1) // 7 + 1
    return f"{d.year}/{d.month:02d} 第{week_num}週"


def _prepare_heartrate(records: list) -> str:
    """血壓心率：每週平均，標註異常"""
    if not records:
        return ""

    weekly = defaultdict(list)
    for r in records:
        try:
            d = date.fromisoformat(r["filltime"][:10])
            systolic = float(r.get("mmHg1", 0))
            diastolic = float(r.get("mmHg2", 0))
            bpm = float(r.get("bpm", 0))
            if systolic > 0:
                weekly[_week_label(d)].append((systolic, diastolic, bpm))
        except Exception:
            continue

    lines = ["【血壓心率】"]
    for week, values in sorted(weekly.items()):
        avg_sys = sum(v[0] for v in values) / len(values)
        avg_dia = sum(v[1] for v in values) / len(values)
        avg_bpm = sum(v[2] for v in values) / len(values)
        note = ""
        if avg_sys > 130:
            note = " ⚠️偏高"
        elif avg_sys < 90:
            note = " ⚠️偏低"
        lines.append(
            f"  {week}：收縮壓 {avg_sys:.0f} / 舒張壓 {avg_dia:.0f} / 心率 {avg_bpm:.0f}{note}"
        )
    return "\n".join(lines)


def _prepare_drug(records: list) -> str:
    """用藥：每日列出藥物，標註變動"""
    if not records:
        return ""

    # 按日期分組
    daily = defaultdict(set)
    for r in records:
        try:
            d = r["filltime"][:10]
            name = r.get("drugname", "").strip()
            if name:
                daily[d].add(name)
        except Exception:
            continue

    if not daily:
        return ""

    sorted_dates = sorted(daily.keys())
    lines = ["【用藥紀錄】"]
    prev_drugs = None
    for d in sorted_dates:
        drugs = daily[d]
        drug_str = "、".join(sorted(drugs))
        if prev_drugs is None:
            lines.append(f"  {d}：{drug_str}")
        else:
            added = drugs - prev_drugs
            removed = prev_drugs - drugs
            change = ""
            if added:
                change += f" 🆕新增：{'、'.join(sorted(added))}"
            if removed:
                change += f" ❌停用：{'、'.join(sorted(removed))}"
            if change:
                lines.append(f"  {d}：{drug_str}{change}")
            else:
                # 相同就只記錄最後一天
                lines[-1] = f"  {sorted_dates[0]}～{d}：{drug_str}（無變動）"
        prev_drugs = drugs

    return "\n".join(lines)


def _prepare_weight(records: list) -> str:
    """體重：起始/結束/趨勢"""
    if not records:
        return ""

    weights = []
    for r in records:
        try:
            d = r["filltime"][:10]
            w = float(r.get("wei", 0))
            if w > 0:
                weights.append((d, w))
        except Exception:
            continue

    if not weights:
        return ""

    weights.sort()
    start_d, start_w = weights[0]
    end_d, end_w = weights[-1]
    diff = end_w - start_w
    trend = f"{'增加' if diff > 0 else '減少'} {abs(diff):.1f} kg" if diff != 0 else "持平"
    return f"【體重】\n  {start_d}：{start_w} kg → {end_d}：{end_w} kg（{trend}）"


def _prepare_life(records: list) -> str:
    """生活紀錄：每週情緒統計 + 日記前200字"""
    if not records:
        return ""

    weekly_emotions = defaultdict(list)
    weekly_diary = defaultdict(list)

    for r in records:
        try:
            d = date.fromisoformat(r["filltime"][:10])
            week = _week_label(d)
            emotion = r.get("emotion", "")
            diary = r.get("liferecord", "").strip()
            if emotion:
                for e in emotion.split("、"):
                    e = e.strip()
                    if e:
                        weekly_emotions[week].append(e)
            if diary:
                weekly_diary[week].append(diary)
        except Exception:
            continue

    lines = ["【生活紀錄】"]
    for week in sorted(set(list(weekly_emotions.keys()) + list(weekly_diary.keys()))):
        emotions = weekly_emotions.get(week, [])
        diaries = weekly_diary.get(week, [])

        emotion_count = defaultdict(int)
        for e in emotions:
            emotion_count[e] += 1
        emotion_str = "、".join(f"{e}×{n}" for e, n in emotion_count.items()) if emotion_count else "無"

        diary_combined = " ".join(diaries)
        if len(diary_combined) > 200:
            diary_combined = diary_combined[:200] + "…"

        lines.append(f"  {week}：情緒〔{emotion_str}〕")
        if diary_combined:
            lines.append(f"    日記：{diary_combined}")

    return "\n".join(lines)


def _prepare_symptom(records: list) -> str:
    """不舒服的地方：症狀名稱頻率 + 情境標籤"""
    if not records:
        return ""

    real_records = [r for r in records if r.get("symptomname", "") != "（無症狀）"]
    if not real_records:
        return "【不舒服的地方】\n  此期間無症狀紀錄"

    symptom_count = defaultdict(int)
    context_count = defaultdict(int)
    for r in real_records:
        name = r.get("symptomname", "").strip()
        if name:
            symptom_count[name] += 1
        ctx = r.get("context", "")
        for c in ctx.split(","):
            c = c.strip()
            if c:
                context_count[c] += 1

    lines = ["【不舒服的地方】"]
    top_symptoms = sorted(symptom_count.items(), key=lambda x: -x[1])[:10]
    lines.append("  症狀頻率：" + "、".join(f"{n}（{c}次）" for n, c in top_symptoms))
    if context_count:
        top_ctx = sorted(context_count.items(), key=lambda x: -x[1])[:5]
        lines.append("  常見情境：" + "、".join(f"{n}（{c}次）" for n, c in top_ctx))
    return "\n".join(lines)


def _prepare_sleep(records: list) -> str:
    """睡眠：每週平均時數與品質 + 標籤頻率"""
    if not records:
        return ""

    weekly_duration = defaultdict(list)
    weekly_quality = defaultdict(list)
    tag_count = defaultdict(int)

    for r in records:
        try:
            d = date.fromisoformat(r["filltime"][:10])
            week = _week_label(d)
            dur = r.get("duration")
            if dur is not None:
                weekly_duration[week].append(float(dur))
            qual = r.get("quality")
            if qual is not None:
                weekly_quality[week].append(float(qual))
            tags = r.get("tags", "")
            for t in tags.split(","):
                t = t.strip()
                if t:
                    tag_count[t] += 1
        except Exception:
            continue

    lines = ["【睡眠】"]
    for week in sorted(set(list(weekly_duration.keys()) + list(weekly_quality.keys()))):
        dur_vals = weekly_duration.get(week, [])
        qual_vals = weekly_quality.get(week, [])
        dur_str = f"{sum(dur_vals)/len(dur_vals):.1f}小時" if dur_vals else "—"
        qual_str = f"{sum(qual_vals)/len(qual_vals):.1f}/5" if qual_vals else "—"
        lines.append(f"  {week}：平均睡眠 {dur_str}，品質 {qual_str}")

    if tag_count:
        top_tags = sorted(tag_count.items(), key=lambda x: -x[1])[:5]
        lines.append("  常見標籤：" + "、".join(f"{t}（{c}次）" for t, c in top_tags))

    return "\n".join(lines)


def _prepare_simple(records: list, module_key: str, field: str, display_name: str, unit: str,
                     high_threshold: float = None, low_threshold: float = None) -> str:
    """血糖/體溫等簡單數值：每週平均，標註異常"""
    if not records:
        return ""

    weekly = defaultdict(list)
    for r in records:
        try:
            d = date.fromisoformat(r["filltime"][:10])
            val = float(r.get(field, 0))
            if val > 0:
                weekly[_week_label(d)].append(val)
        except Exception:
            continue

    if not weekly:
        return ""

    lines = [f"【{display_name}】"]
    for week, vals in sorted(weekly.items()):
        avg = sum(vals) / len(vals)
        note = ""
        if high_threshold and avg > high_threshold:
            note = " ⚠️偏高"
        elif low_threshold and avg < low_threshold:
            note = " ⚠️偏低"
        lines.append(f"  {week}：平均 {avg:.1f} {unit}{note}")
    return "\n".join(lines)


def prepare_data_for_ai(user_id: str, start_date: date, end_date: date, selected_modules: list) -> str:
    """
    從 Firebase 讀取各模組資料，整理成給 Gemini 的純文字 context。
    selected_modules: 模組 key 列表，如 ['heartrate', 'drug', 'life', ...]
    """
    MODULE_TO_NODE = {
        "heartrate": "HeartRate",
        "weight": "Weight",
        "sugar": "Sugar",
        "temp": "Temp",
        "drug": "Drug",
        "life": "Life",
        "symptom": "Symptom",
        "sleep": "Sleep",
    }

    sections = []

    for mod in selected_modules:
        node = MODULE_TO_NODE.get(mod)
        if not node:
            continue
        records = get_user_records(user_id, node, start_date, end_date)

        if mod == "heartrate":
            s = _prepare_heartrate(records)
        elif mod == "drug":
            s = _prepare_drug(records)
        elif mod == "weight":
            s = _prepare_weight(records)
        elif mod == "life":
            s = _prepare_life(records)
        elif mod == "symptom":
            s = _prepare_symptom(records)
        elif mod == "sleep":
            s = _prepare_sleep(records)
        elif mod == "sugar":
            s = _prepare_simple(records, mod, "sugarlevel", "血糖", "mg/dL",
                                 high_threshold=126, low_threshold=70)
        elif mod == "temp":
            s = _prepare_simple(records, mod, "temp", "體溫", "°C",
                                 high_threshold=37.5, low_threshold=36.0)
        else:
            s = ""

        if s:
            sections.append(s)

    if not sections:
        return "（此期間無任何紀錄）"

    return "\n\n".join(sections)


def generate_report_with_gemini(user_name: str, data_context: str,
                                 start_date: date, end_date: date) -> str:
    """
    呼叫 Gemini API，回傳 markdown 格式的健康報告。
    """
    api_key = st.secrets.get("gemini", {}).get("api_key", "")
    if not api_key:
        raise ValueError("請在 .streamlit/secrets.toml 設定 [gemini] api_key")

    client = genai.Client(api_key=api_key)

    prompt = f"""你是一位專業醫療助理，請根據以下健康紀錄，撰寫一份給醫師閱覽的健康狀況報告。

使用者：{user_name}
紀錄期間：{start_date.strftime("%Y年%m月%d日")} 至 {end_date.strftime("%Y年%m月%d日")}

健康紀錄資料：
---
{data_context}
---

請依以下格式撰寫報告（使用繁體中文，語氣專業但易讀）：

# {user_name} 的狀況記錄
**紀錄期間：{start_date.strftime("%Y/%m/%d")} ～ {end_date.strftime("%Y/%m/%d")}**

## 各項指標總結
（逐一說明有紀錄的各模組概況，注意趨勢與特殊數值）

## 特殊時間點與跨項目關聯分析
（這是最重要的部分。請找出特殊時間點，例如某週某數值異常，並對照同期其他紀錄（日記內容、藥物變動、症狀、睡眠）尋找可能關聯。
例如：「X月第N週血壓偏高，同期日記記錄提到壓力增加，且睡眠品質下降至X分」）

## 整體觀察
（2-4句整體觀察，供醫師參考，非診斷）
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    return response.text


def export_report_to_docx(report_text: str, user_name: str,
                           start_date: date, end_date: date) -> BytesIO:
    """
    將 markdown 格式報告轉成 Word 檔，回傳 BytesIO。
    """
    doc = Document()

    # 設定預設字型
    style = doc.styles["Normal"]
    style.font.name = "微軟正黑體"
    style.font.size = Pt(11)

    for line in report_text.split("\n"):
        line = line.rstrip()

        if line.startswith("# "):
            p = doc.add_heading(line[2:], level=1)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif line.startswith("## "):
            doc.add_heading(line[3:], level=2)
        elif line.startswith("### "):
            doc.add_heading(line[4:], level=3)
        elif line.startswith("**") and line.endswith("**"):
            p = doc.add_paragraph()
            run = p.add_run(line.strip("*"))
            run.bold = True
        elif line.startswith("- ") or line.startswith("* "):
            doc.add_paragraph(line[2:], style="List Bullet")
        elif line == "":
            doc.add_paragraph("")
        else:
            # 處理行內粗體 **text**
            if "**" in line:
                p = doc.add_paragraph()
                parts = line.split("**")
                for i, part in enumerate(parts):
                    run = p.add_run(part)
                    if i % 2 == 1:
                        run.bold = True
            else:
                doc.add_paragraph(line)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

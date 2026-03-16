import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from export_records import DATA_TYPES


# 各模組要繪製的數值欄位與設定
CHART_COLUMNS = {
    "HeartRate": {
        "columns": {"mmHg1": "收縮壓", "mmHg2": "舒張壓", "bpm": "心率"},
        "chart_type": "line",
        "units": {"mmHg1": "mmHg", "mmHg2": "mmHg", "bpm": "bpm"},
        "colors": {"mmHg1": "#FF6B6B", "mmHg2": "#4ECDC4", "bpm": "#FFE66D"}
    },
    "Weight": {
        "columns": {"wei": "體重", "wai": "腰圍"},
        "chart_type": "line",
        "units": {"wei": "kg", "wai": "cm"},
        "colors": {"wei": "#1A535C", "wai": "#FF6B6B"}
    },
    "Sugar": {
        "columns": {"sugarlevel": "血糖"},
        "chart_type": "line",
        "units": {"sugarlevel": "mg/dL"},
        "colors": {"sugarlevel": "#FF9F1C"}
    },
    "Temp": {
        "columns": {"temp": "體溫"},
        "chart_type": "line",
        "units": {"temp": "°C"},
        "colors": {"temp": "#FF6B6B"}
    },
    "BodyFat": {
        "columns": {"bodyfat": "體脂"},
        "chart_type": "line",
        "units": {"bodyfat": "%"},
        "colors": {"bodyfat": "#2EC4B6"}
    },
    "Muscle": {
        "columns": {"muscle": "骨骼肌"},
        "chart_type": "line",
        "units": {"muscle": "kg"},
        "colors": {"muscle": "#CBF3F0"}
    },
    "BMI": {
        "columns": {"bmi": "BMI"},
        "chart_type": "line",
        "units": {"bmi": ""},
        "colors": {"bmi": "#2B2D42"}
    },
    "Drug": {
        "columns": {},
        "chart_type": "drug",
    },
    "Life": {
        "columns": {},
        "chart_type": "life",
    },
    "Symptom": {
        "columns": {},
        "chart_type": "symptom",
    },
    "Sleep": {
        "columns": {},
        "chart_type": "sleep",
    },
}


def records_to_dataframe(records, data_type):
    """
    將記錄列表轉為 DataFrame，以 filltime 解析為 datetime index。
    回傳適合繪圖的 DataFrame（欄位已重命名為中文）。
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
    
    # 確保數值欄位存在且轉型
    for col in cols_to_keep:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    existing_cols = [c for c in cols_to_keep if c in df.columns]
    if not existing_cols:
        return None

    # 重命名欄位
    result = df[["時間"] + existing_cols].copy()
    result = result.rename(columns=rename_map)
    result = result.set_index("時間")

    return result


def create_plotly_line_chart(df, data_type):
    """
    使用 Plotly 繪製折線圖
    """
    if df is None or df.empty:
        return None

    config = CHART_COLUMNS.get(data_type, {})
    units = config.get("units", {})
    colors = config.get("colors", {})
    
    # 建立 Figure
    fig = go.Figure()

    # 針對每個欄位畫一條線
    for col_name in df.columns:
        # 找對應的原始欄位key (為了拿單位和顏色)
        original_key = None
        for k, v in config["columns"].items():
            if v == col_name:
                original_key = k
                break
        
        unit = units.get(original_key, "")
        color = colors.get(original_key, None)
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df[col_name],
            mode='lines+markers',
            name=col_name,
            line=dict(width=3, color=color),
            marker=dict(size=6),
            hovertemplate=f"<b>%{{x|%m/%d %H:%M}}</b><br>{col_name}: %{{y}} {unit}<extra></extra>"
        ))

    # 更新 layout
    fig.update_layout(
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis_title="時間",
        yaxis_title="數值",
        template="plotly_white"
    )
    
    # RWD
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#eee')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#eee')

    return fig


def create_combined_chart(df, data_type, drug_records, user_drug_slots=None):
    """
    建立折線圖（背景色顯示當日用藥達成率）。
    user_drug_slots: 使用者設定的應服時段 list，如 ["早", "晚"]；None 表示不顯示用藥背景。
    """
    if df is None or df.empty:
        return None

    config = CHART_COLUMNS.get(data_type, {})
    units = config.get("units", {})
    colors = config.get("colors", {})

    fig = go.Figure()

    # ── 繪製折線圖 ──
    for col_name in df.columns:
        original_key = None
        for k, v in config["columns"].items():
            if v == col_name:
                original_key = k
                break

        unit = units.get(original_key, "")
        color = colors.get(original_key, None)

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df[col_name],
            mode='lines+markers',
            name=col_name,
            line=dict(width=3, color=color),
            marker=dict(size=6),
            hovertemplate=f"{col_name}: %{{y}} {unit}<extra></extra>"
        ))

    fig.update_layout(
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        height=400,
        showlegend=True,
        template="plotly_white",
        legend=dict(orientation="h", y=1.1)
    )

    return fig


def create_plot_line_chart(df, data_type):
    # Backward compatibility or unused, keep for now if needed, 
    # but create_plotly_line_chart is what we used before.
    return create_plotly_line_chart(df, data_type)


def create_drug_heatmap_chart(records, start_date, end_date, user_drug_slots=None):
    """
    使用 Plotly 繪製用藥熱力圖。
    user_drug_slots: 使用者設定應服的時段 list；None 或空 list 表示顯示全部 4 個時段。
    """
    if not records:
        return None

    ALL_SLOTS = ["早", "午", "晚", "睡前"]
    TIME_SLOTS = user_drug_slots if user_drug_slots else ALL_SLOTS
    
    # 整理資料
    date_slot_matrix = []
    dates = []
    
    # 找出所有日期範圍內的日期
    # 若 records 很多，直接用 records 的日期
    # 這裡簡單處理：掃描 records 建立矩陣
    
    compliance = {}
    for r in records:
        dt = _parse_filltime(r.get("filltime", ""))
        eattime = r.get("eattime", "").strip()
        if dt and eattime in TIME_SLOTS:
            date_str = dt.strftime("%Y-%m-%d")
            if date_str not in compliance:
                compliance[date_str] = {slot: 0 for slot in TIME_SLOTS}
            compliance[date_str][eattime] = 1 # 1 表示有吃

    if not compliance:
        return None
        
    # 轉為列表供 heatmap 使用
    sorted_dates = sorted(compliance.keys())
    
    z_values = [] # 顏色值 (0/1)
    text_values = [] # 顯示文字 (V/Empty)
    
    # 轉置矩陣：X軸=日期，Y軸=時段
    # Plotly Heatmap x=dates, y=slots
    
    # 準備 4 個時段的數據列
    slot_data = {s: [] for s in TIME_SLOTS}
    
    for d in sorted_dates:
        for s in TIME_SLOTS:
            val = compliance[d].get(s, 0)
            slot_data[s].append(val)

    # 構建 z 矩陣 (y 軸是時段，所以是 4 列)
    z = [slot_data[s] for s in TIME_SLOTS]
    
    # 自定義顏色：0=白/淺灰, 1=綠
    colorscale = [[0, '#f0f0f0'], [1, '#4caf50']]
    
    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=sorted_dates,
        y=TIME_SLOTS,
        colorscale=colorscale,
        showscale=False,
        xgap=2, # 格子間距
        ygap=2,
        hovertemplate="日期: %{x}<br>時段: %{y}<br>狀態: 已服藥<extra></extra>"
    ))
    
    fig.update_layout(
        title="近期用藥達成狀況",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_type='category' # 確保日期顯示完整
    )
    
    return fig


def create_emotion_bar_chart(records):
    """
    生活紀錄：情緒分布長條圖（支援多選情緒，以「、」分隔）
    """
    if not records:
        return None

    all_emotions = []
    for r in records:
        raw = r.get("emotion", "")
        if not raw:
            continue
        # 多選情緒以「、」分隔，逐一拆開統計
        for e in raw.split("、"):
            e = e.strip()
            if e:
                all_emotions.append(e)

    if not all_emotions:
        return None

    counts = pd.Series(all_emotions).value_counts().reset_index()
    counts.columns = ["情緒", "次數"]
    
    fig = px.bar(
        counts, 
        x="情緒", 
        y="次數", 
        color="情緒",
        text="次數",
        title="情緒分布"
    )
    
    fig.update_traces(textposition='outside')
    fig.update_layout(
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
        height=300
    )
    
    return fig


def get_summary_stats(df):
    """
    計算 DataFrame 各欄位的摘要統計，包含與上一筆的差值。
    """
    if df is None or df.empty:
        return {}

    stats = {}
    for col in df.columns:
        numeric = df[col].dropna()
        if numeric.empty:
            continue
        latest = round(numeric.iloc[-1], 1)
        prev = round(numeric.iloc[-2], 1) if len(numeric) >= 2 else None
        stats[col] = {
            "平均": round(numeric.mean(), 1),
            "最高": round(numeric.max(), 1),
            "最低": round(numeric.min(), 1),
            "筆數": len(numeric),
            "最新": latest,
            "上一筆": prev,
        }
    return stats


def create_symptom_bar_chart(records):
    """
    不舒服的地方：症狀出現頻率長條圖
    """
    if not records:
        return None

    names = [r.get("symptomname", "").strip() for r in records if r.get("symptomname", "").strip()]
    # 排除「無症狀」標記
    names = [n for n in names if n != "（無症狀）"]
    if not names:
        return None

    counts = pd.Series(names).value_counts().reset_index()
    counts.columns = ["症狀", "次數"]

    fig = px.bar(
        counts,
        x="症狀",
        y="次數",
        color="症狀",
        text="次數",
        title="症狀出現頻率"
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
        height=300
    )
    return fig


def create_sleep_charts(records):
    """
    睡眠紀錄：回傳 (時數折線圖, 品質折線圖) tuple
    品質分數 1-5 對應 😫😕😐😊😄
    """
    if not records:
        return None, None

    QUALITY_LABELS = {1: "😫", 2: "😕", 3: "😐", 4: "😊", 5: "😄"}

    rows = []
    for r in records:
        dt = _parse_filltime(r.get("filltime", ""))
        if dt is None:
            continue
        try:
            dur = float(r.get("duration", 0))
            quality = int(r.get("quality", 0))
        except (ValueError, TypeError):
            continue
        rows.append({"時間": dt.strftime("%Y-%m-%d"), "時數": dur, "品質": quality})

    if not rows:
        return None, None

    df = pd.DataFrame(rows).sort_values("時間")

    # 睡眠時數折線圖
    fig_dur = go.Figure()
    fig_dur.add_trace(go.Scatter(
        x=df["時間"], y=df["時數"],
        mode='lines+markers',
        name="睡眠時數",
        line=dict(width=3, color="#5B8DEF"),
        marker=dict(size=7),
        hovertemplate="<b>%{x}</b><br>睡眠時數: %{y} 小時<extra></extra>"
    ))
    # 建議範圍參考線 7-9 小時
    fig_dur.add_hrect(y0=7, y1=9, fillcolor="#d4edda", opacity=0.3, line_width=0, annotation_text="建議範圍 7-9h", annotation_position="top right")
    fig_dur.update_layout(
        title="睡眠時數",
        yaxis_title="小時",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        template="plotly_white"
    )

    # 睡眠品質折線圖
    fig_q = go.Figure()
    fig_q.add_trace(go.Scatter(
        x=df["時間"], y=df["品質"],
        mode='lines+markers',
        name="睡眠品質",
        line=dict(width=3, color="#F4A261"),
        marker=dict(size=7),
        hovertemplate="<b>%{x}</b><br>品質: %{y}<extra></extra>"
    ))
    fig_q.update_layout(
        title="睡眠品質",
        yaxis=dict(
            title="品質",
            tickmode="array",
            tickvals=[1, 2, 3, 4, 5],
            ticktext=["😫", "😕", "😐", "😊", "😄"],
            range=[0.5, 5.5]
        ),
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        template="plotly_white"
    )

    return fig_dur, fig_q


def _parse_filltime(filltime_str):
    """解析 filltime 字串為 datetime"""
    if not filltime_str:
        return None
    try:
        if len(filltime_str) > 16:
            return datetime.strptime(filltime_str[:16], "%Y-%m-%d %H:%M")
        return datetime.strptime(filltime_str, "%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return None

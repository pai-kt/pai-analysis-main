"""Shared app helpers: charts, env classification, column helpers."""
from __future__ import annotations

import os

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

from src.ml_utils import compute_metrics, make_model, safe_predict
from src.rolling_features import build_window_feature_name, compute_rolling_summary
from src.paths import FONTS_DIR

FONT_PATH = str(FONTS_DIR / "NanumGothic.ttf")

try:
    if os.path.exists(FONT_PATH):
        fm.fontManager.addfont(FONT_PATH)
        font_prop = fm.FontProperties(fname=FONT_PATH)
        plt.rcParams["font.family"] = font_prop.get_name()
except Exception:
    pass

plt.rcParams["axes.unicode_minus"] = False

# 그래프·표 기본 설정 (고정)
graph_theme = "기본"
font_scale = 1.0
line_width_scale = 1.2
plotly_template = "plotly_white"


def render_kpi_cards(items):
    """색상이 다른 KPI 카드 행을 렌더링합니다. items: [(label, value, color), ...]"""
    cols = st.columns(len(items))
    for col, (label, value, color) in zip(cols, items):
        with col:
            st.markdown(
                f"""
                <div class="xai-kpi-card">
                    <div class="xai-kpi-label">{label}</div>
                    <div class="xai-kpi-value" style="color:{color};">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_insight(text, variant="blue"):
    """색상 테두리가 있는 인사이트 카드를 렌더링합니다."""
    css_class = "xai-insight" if variant == "blue" else f"xai-insight xai-insight-{variant}"
    st.markdown(f'<div class="{css_class}">{text}</div>', unsafe_allow_html=True)


def render_alert_card(text, variant="info"):
    """success / warning / info 스타일 알림 카드 (글자색 보장)."""
    css_class = f"xai-alert-card xai-alert-{variant}"
    st.markdown(f'<div class="{css_class}">{text}</div>', unsafe_allow_html=True)


def build_interactive_timeseries(df, x_col, y_col, title=None):
    """줌·팬·호버가 가능한 Plotly 시계열 그래프."""
    plot_df = df[[x_col, y_col]].copy()
    plot_df[x_col] = pd.to_datetime(plot_df[x_col], errors="coerce")
    plot_df[y_col] = pd.to_numeric(plot_df[y_col], errors="coerce")
    plot_df = plot_df.dropna(subset=[x_col, y_col])

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=plot_df[x_col],
            y=plot_df[y_col],
            mode="lines+markers",
            name=str(y_col),
            line=dict(width=2.5),
            marker=dict(size=7),
            hovertemplate="조사일자: %{x|%Y-%m-%d}<br>값: %{y:.3f}<extra></extra>",
        )
    )
    fig.update_layout(
        title=title or f"{y_col} 시계열",
        xaxis_title="조사일자",
        yaxis_title=str(y_col),
        hovermode="x unified",
        showlegend=False,
        height=380,
        dragmode="zoom",
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#f8fafc",
        font=dict(color="#1e293b", size=12),
    )
    fig.update_xaxes(
        rangeslider_visible=False,
        gridcolor="#e2e8f0",
        linecolor="#cbd5e1",
        tickfont=dict(color="#334155"),
        title_font=dict(color="#1e293b"),
    )
    fig.update_yaxes(
        gridcolor="#e2e8f0",
        linecolor="#cbd5e1",
        tickfont=dict(color="#334155"),
        title_font=dict(color="#1e293b"),
    )
    return fig


def _apply_plotly_light_layout(fig, height=400, title=None):
    """Plotly 공통 밝은 테마."""
    layout_kwargs = dict(
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#f8fafc",
        font=dict(color="#1e293b", size=12),
        height=height,
        hovermode="closest",
        margin=dict(l=20, r=20, t=60 if title else 40, b=40),
    )
    if title:
        layout_kwargs["title"] = dict(text=title, font=dict(size=15, color="#1e293b"), x=0)
    fig.update_layout(**layout_kwargs)
    fig.update_xaxes(gridcolor="#e2e8f0", linecolor="#cbd5e1", tickfont=dict(color="#334155"))
    fig.update_yaxes(gridcolor="#e2e8f0", linecolor="#cbd5e1", tickfont=dict(color="#334155"))
    return fig


def build_weekly_metric_chart(weekly_df, metric, title, color):
    """1~7주 MSE / MAE / R² 인터랙티브 라인 차트."""
    weeks = weekly_df["Week"].tolist()
    values = weekly_df[metric].tolist()
    fill_map = {
        "#2563eb": "rgba(37,99,235,0.12)",
        "#0d9488": "rgba(13,148,136,0.12)",
        "#d97706": "rgba(217,119,6,0.12)",
    }
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=values,
            mode="lines+markers",
            name=metric,
            line=dict(color=color, width=3, shape="spline"),
            marker=dict(size=10, color=color, line=dict(color="#ffffff", width=2)),
            fill="tozeroy",
            fillcolor=fill_map.get(color, "rgba(37,99,235,0.12)"),
            hovertemplate="주차: %{x}주<br>%{fullData.name}: %{y:.4f}<extra></extra>",
        )
    )
    y_labels = {"MSE": "MSE (평균제곱오차)", "MAE": "MAE (평균절대오차)", "R2": "R² (결정계수)"}
    _apply_plotly_light_layout(fig, height=340, title=title)
    fig.update_xaxes(title="주차", dtick=1)
    fig.update_yaxes(title=y_labels.get(metric, metric))
    return fig


def pick_column_index(columns, candidates, fallback=0):
    from src.column_mapping import pick_column_index as _pick
    return _pick(columns, candidates, fallback)


def is_external_cumulative_solar_column(col) -> bool:
    from src.column_mapping import is_external_cumulative_solar_column as _is
    return _is(col)


def list_external_cumulative_solar_columns(columns):
    from src.column_mapping import list_external_cumulative_solar_columns as _list
    return _list(columns)


def pick_external_cumulative_solar_index(columns, fallback=None):
    from src.column_mapping import pick_external_cumulative_solar_index as _pick
    return _pick(columns, fallback)


def pick_external_cumulative_solar_column(columns):
    from src.column_mapping import pick_external_cumulative_solar_column as _pick
    return _pick(columns)


def aggregate_fruit_level_yield(yield_df, date_col):
    """과실 단위 수확 CSV를 조사일자별 요약 데이터로 변환합니다."""
    if "화방별수확수" in yield_df.columns or "수확과중" not in yield_df.columns:
        return yield_df

    tmp = yield_df.copy()
    tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
    tmp = tmp.dropna(subset=[date_col])
    if tmp.empty:
        return yield_df

    agg = tmp.groupby(date_col, as_index=False).agg(
        수확수=("수확과중", "count"),
        착과수=("수확과중", "sum"),
    )
    return agg.rename(columns={date_col: "조사일자"})


def display_plotly(fig, use_container_width=True, key=None):
    """Plotly 그래프 템플릿을 적용해 안전하게 출력합니다."""
    try:
        fig.update_layout(
            template="plotly_white",
            font=dict(size=max(10, int(12 * font_scale)), color="#1e293b"),
            margin=dict(l=20, r=20, t=45, b=20),
            paper_bgcolor="#ffffff",
            plot_bgcolor="#f8fafc",
        )
        fig.update_xaxes(gridcolor="#e2e8f0", linecolor="#cbd5e1")
        fig.update_yaxes(gridcolor="#e2e8f0", linecolor="#cbd5e1")
    except Exception as e:
        st.warning(f"Plotly 디자인 적용 중 경고: {e}")
    st.plotly_chart(
        fig,
        use_container_width=use_container_width,
        key=key,
        config={
            "scrollZoom": True,
            "displaylogo": False,
            "modeBarButtonsToAdd": ["zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d"],
        },
    )


def classify_environment_zone(feature_name, value):
    """
    환경변수를 최저한계구간, 저구간, 중간구간, 최적구간, 고구간, 최고한계구간으로 분류합니다.
    평균주간온도와 평균야간온도는 서로 다른 기준을 적용합니다.
    기준은 교육용 기본값이며 작물·품종·생육단계에 따라 조정할 수 있습니다.
    """
    if pd.isna(value):
        return "데이터없음", "값이 없어 구간을 판단할 수 없습니다."

    fname = str(feature_name)

    # 평균주간온도 기준
    if "주간온도" in fname:
        if value < 15:
            return "최저한계구간", "15℃ 미만: 저온 한계로 생육 정지, 양분 흡수 저하, 저온장해 위험이 큽니다."
        elif value < 20:
            return "저온구간", "15~20℃: 생육은 가능하지만 광합성·과실 비대가 둔화될 수 있습니다."
        elif value < 24:
            return "최적구간", "20~24℃: 주간 광합성과 증산 균형이 좋아 생육·수확 형성에 유리합니다."
        elif value < 30:
            return "고온구간", "24~30℃: 생육은 가능하나 증산·호흡 증가로 환기와 수분 관리가 중요합니다."
        else:
            return "최고한계구간", "30℃ 이상: 고온 스트레스, 착과 불량, 품질 저하, 엽온 상승 위험이 큽니다."

    # 평균야간온도 기준
    if "야간온도" in fname:
        if value < 10:
            return "최저한계구간", "10℃ 미만: 야간 저온 한계로 생육 정지와 저온장해 위험이 큽니다."
        elif value < 15:
            return "저온구간", "10~15℃: 호흡은 줄지만 생육 회복과 양분 이동이 둔화될 수 있습니다."
        elif value < 18:
            return "최적구간", "15~18℃: 야간 호흡과 당 소모가 적절하여 생육 균형 유지에 유리합니다."
        elif value < 23:
            return "고온구간", "18~23℃: 야간 호흡량 증가로 당 소모가 커질 수 있습니다."
        else:
            return "최고한계구간", "23℃ 이상: 야간 고온으로 호흡 과다, 생장 불균형, 품질 저하 위험이 있습니다."

    # 기타 온도 기준
    if "온도" in fname:
        if value < 15:
            return "최저한계구간", "15℃ 미만: 저온 한계로 생육 정지와 저온장해 위험이 있습니다."
        elif value < 20:
            return "저온구간", "15~20℃: 생육은 가능하지만 광합성·양분 흡수·과실 비대가 둔화될 수 있습니다."
        elif value < 24:
            return "최적구간", "20~24℃: 광합성과 호흡 균형이 좋아 안정적 생육에 유리합니다."
        elif value < 30:
            return "고온구간", "24~30℃: 생육은 가능하나 증산과 호흡 증가로 수분·환기 관리가 중요합니다."
        else:
            return "최고한계구간", "30℃ 이상: 고온 스트레스, 착과 불량, 품질 저하 위험이 증가합니다."

    # 습도
    if "습도" in fname:
        if value < 40:
            return "최저한계구간", "40% 미만: 극건조로 VPD가 과도하게 높아져 위조·수분 스트레스 위험이 큽니다."
        elif value < 60:
            return "저습구간", "40~60%: 건조 경향으로 증산 과다와 생육 지연이 발생할 수 있습니다."
        elif value < 80:
            return "최적구간", "60~80%: 증산과 기공 조절이 안정적인 적정 습도 구간입니다."
        elif value < 90:
            return "다습구간", "80~90%: 야간 결로와 병해 위험이 증가할 수 있습니다."
        else:
            return "최고한계구간", "90% 이상: 과습·결로·병해 확산 위험이 높아 제습과 환기가 필요합니다."

    # CO2
    if "CO₂" in fname or "CO2" in fname:
        if value < 350:
            return "최저한계구간", "350ppm 미만: CO₂ 부족으로 광합성이 제한될 수 있습니다."
        elif value < 400:
            return "저농도구간", "350~400ppm: 외기 수준 이하로 광합성 원료가 부족할 수 있습니다."
        elif value < 800:
            return "중간구간", "400~800ppm: 일반 생육은 가능하나 적극적인 CO₂ 시비 효과는 제한적일 수 있습니다."
        elif value < 1200:
            return "최적구간", "800~1200ppm: 충분한 광·온도 조건에서 광합성 촉진에 유리합니다."
        else:
            return "최고한계구간", "1200ppm 이상: 과다 공급 또는 환기 부족 가능성이 있어 공급량과 환기를 점검해야 합니다."

    # 일사량
    if "일사" in fname or "광" in fname:
        if value < 300:
            return "최저한계구간", "매우 낮은 일사량: 광합성량과 동화산물 생산이 크게 부족할 수 있습니다."
        elif value < 500:
            return "저광구간", "낮은 일사량: 생육단계에 따라 보광이 필요할 수 있습니다."
        elif value < 1200:
            return "중간구간", "중간 일사량: 기본 광합성은 가능하나 생육단계에 따라 보광 판단이 필요합니다."
        elif value < 2000:
            return "최적구간", "충분한 일사량: 광합성과 당 생산에 유리하여 생육·수확 증가에 긍정적입니다."
        else:
            return "최고한계구간", "매우 높은 일사량: 고온·건조·엽온 상승이 동반될 수 있어 차광·냉방 관리가 필요합니다."

    return "기타", "해당 변수는 별도 기준 설정 후 해석하는 것이 좋습니다."


# Re-export rolling helpers used by UI as core.*
__all__ = [
    "compute_metrics",
    "make_model",
    "safe_predict",
    "build_window_feature_name",
    "compute_rolling_summary",
    "render_kpi_cards",
    "render_insight",
    "render_alert_card",
    "build_interactive_timeseries",
    "build_weekly_metric_chart",
    "pick_column_index",
    "is_external_cumulative_solar_column",
    "list_external_cumulative_solar_columns",
    "pick_external_cumulative_solar_index",
    "pick_external_cumulative_solar_column",
    "aggregate_fruit_level_yield",
    "display_plotly",
    "classify_environment_zone",
    "graph_theme",
    "font_scale",
    "line_width_scale",
    "plotly_template",
]

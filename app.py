import os

# Streamlit Cloud / Linux 서버: matplotlib 캐시·GUI 백엔드 이슈 방지
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
os.environ.setdefault("MPLBACKEND", "Agg")

import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.naive_bayes import GaussianNB
import shap
import matplotlib.pyplot as plt
from sklearn.inspection import PartialDependenceDisplay
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import matplotlib
import platform
import re

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

FONT_PATH = "fonts/NanumGothic.ttf"

try:
    if os.path.exists(FONT_PATH):
        fm.fontManager.addfont(FONT_PATH)
        font_prop = fm.FontProperties(fname=FONT_PATH)
        plt.rcParams["font.family"] = font_prop.get_name()
except Exception:
    pass

plt.rcParams["axes.unicode_minus"] = False

plt.rcParams['axes.unicode_minus'] = False

if os.environ.get("PAI_APP_MODE") != "mobile":
    st.set_page_config(page_title="A-DIMS · 토마토 대시보드", layout="wide")

# 그래프·표 기본 설정 (고정)
graph_theme = "기본"
font_scale = 1.0
line_width_scale = 1.2
heatmap_cmap = "coolwarm"
plotly_template = "plotly_white"

# A-DIMS UI 스타일은 dims_ui.py ADIMS_CSS에서 주입됩니다 (모바일 모드 제외).
if os.environ.get("PAI_APP_MODE") == "mobile":
    st.markdown(
        """
        <style>
        .block-container { max-width: 100% !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_crop_selector(crop_options):
    """페이지 최상단 작물 선택."""
    st.markdown('<div class="crop-top-bar-marker"></div>', unsafe_allow_html=True)
    return st.selectbox("🌱 작물 선택", crop_options, key="crop_select")


def render_page_hero(crop_name):
    crop_icon = "🍅" if crop_name == "토마토" else "🥒"
    st.markdown(
        f"""
        <div class="xai-hero">
            <div class="xai-hero-kicker">EXPLAINABLE AI · SMART FARM ANALYTICS</div>
            <h1 class="xai-hero-title">{crop_icon} {crop_name} 생육·수확 분석 대시보드</h1>
            <p class="xai-hero-desc">
                환경센서와 생육 데이터를 결합해 SHAP · ICE · PDP · ALE 기반 설명가능 AI 분석을 수행합니다.
            </p>
            <div class="xai-pill-wrap">
                <div class="xai-pill xai-pill-blue">
                    <div class="label">분석 파이프라인</div>
                    <div class="value">7주 롤링</div>
                </div>
                <div class="xai-pill xai-pill-teal">
                    <div class="label">지원 모델</div>
                    <div class="value">5종</div>
                </div>
                <div class="xai-pill xai-pill-purple">
                    <div class="label">XAI</div>
                    <div class="value">SHAP · ALE</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title, subtitle="", icon="📊", accent="blue"):
    subtitle_html = f'<p class="xai-section-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div class="xai-section-header xai-accent-{accent}">
            <div class="xai-section-icon">{icon}</div>
            <div>
                <h3 class="xai-section-title">{title}</h3>
                {subtitle_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


_STEP_COLORS = {1: "step-blue", 2: "step-teal", 3: "step-purple", 4: "step-amber"}


def render_step_badge(step, label):
    css_class = _STEP_COLORS.get(step, "step-blue")
    st.markdown(
        f'<div class="xai-step-badge {css_class}">STEP {step} · {label}</div>',
        unsafe_allow_html=True,
    )


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


def render_checkbox_group(label, options, key_prefix, default_all=True, columns=4):
    """체크박스 그룹 — 기본값은 전체 선택."""
    if not options:
        return []
    st.markdown(f"**{label}**")
    selected = []
    n_cols = min(len(options), columns)
    cols = st.columns(n_cols)
    for i, opt in enumerate(options):
        safe = re.sub(r"\W+", "_", opt)
        with cols[i % n_cols]:
            if st.checkbox(opt, value=default_all, key=f"{key_prefix}_{safe}_{i}"):
                selected.append(opt)
    return selected


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


def fig_temporal_shap_bar(week_df):
    """Temporal SHAP — 기본 막대 그래프 (원본 스타일)."""
    week_df = week_df.sort_values("Week")
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(
        week_df["Week"].astype(str),
        week_df["TotalMeanAbsSHAP"],
        color="#3b82f6",
        edgecolor="#1e40af",
        linewidth=0.8,
        width=0.65,
    )
    ax.set_title("주차별 영향도", fontweight="bold", color="#1e293b")
    ax.set_xlabel("시간 단위: 주(week)")
    ax.set_ylabel("단위: Mean(|SHAP value|)")
    ax.grid(True, linestyle="--", alpha=0.4, axis="y")
    ax.set_axisbelow(True)
    return fig


def fig_feature_week_heatmap(heatmap_df, target_col=None):
    """Feature × Week Heatmap — 정적 matplotlib."""
    hm = heatmap_df.copy()
    hm = hm.reindex(sorted(hm.columns, key=lambda x: int(x)), axis=1)
    y_labels = [pretty_time_text(idx) for idx in hm.index]
    x_labels = [f"{int(c)}주" for c in hm.columns]
    z = hm.values.astype(float)

    fig_h, ax_h = plt.subplots(figsize=(max(8, len(x_labels) * 0.85), max(5.5, len(y_labels) * 0.42)))
    im = ax_h.imshow(z, aspect="auto", cmap="Blues", interpolation="nearest", vmin=0)
    ax_h.set_xticks(range(len(x_labels)))
    ax_h.set_xticklabels(x_labels, fontsize=10)
    ax_h.set_yticks(range(len(y_labels)))
    ax_h.set_yticklabels(y_labels, fontsize=9)
    ax_h.set_xlabel("시간 단위: 주(week)", fontsize=11, color="#334155")
    ax_h.set_ylabel("환경/생육 변수", fontsize=11, color="#334155")
    title = "Feature × Week Heatmap"
    if target_col:
        title += f" (예측: {target_col})"
    ax_h.set_title(title, fontweight="bold", color="#1e293b", pad=12)

    if z.size <= 84:
        for i in range(z.shape[0]):
            for j in range(z.shape[1]):
                val = z[i, j]
                txt_color = "white" if val > z.max() * 0.55 else "#1e293b"
                ax_h.text(j, i, f"{val:.3f}", ha="center", va="center", fontsize=8, color=txt_color)

    cbar = fig_h.colorbar(im, ax=ax_h, shrink=0.88, pad=0.02)
    cbar.set_label("Mean(|SHAP|)", fontsize=10, color="#334155")
    cbar.ax.tick_params(labelsize=9, colors="#334155")
    fig_h.tight_layout()
    return fig_h


def fig_ice_pdp(xs, ice_curves_y, pdp_x, pdp_y, feature_name, best_interval=None):
    """ICE + PDP — 정적 matplotlib (최적 구간 하이라이트)."""
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for preds in ice_curves_y:
        ax.plot(xs, preds, color="#93c5fd", alpha=0.35, linewidth=1.2)
    ax.plot(pdp_x, pdp_y, color="#dc2626", linewidth=3, label="PDP", zorder=5)
    if best_interval:
        start, end = best_interval
        ax.axvspan(start, end, alpha=0.18, color="#10b981", label="최적 구간", zorder=1)
    ax.set_title(f"ICE + PDP: {feature_name}", fontweight="bold", color="#1e293b", pad=10)
    ax.set_xlabel(feature_name, fontsize=11, color="#334155")
    ax.set_ylabel("Predicted", fontsize=11, color="#334155")
    ax.legend(loc="best", framealpha=0.9, edgecolor="#e2e8f0")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)
    fig.tight_layout()
    return fig


def fig_centered_ale(bin_centers, ale_vals, feature_name, pos_intervals=None, neg_intervals=None):
    """Centered ALE — 정적 matplotlib (양/음 구간 색상)."""
    fig, ax = plt.subplots(figsize=(6, 4))
    for a, b, _ in (neg_intervals or []):
        ax.axvspan(a, b, alpha=0.15, color="#fca5a5", zorder=1)
    for a, b, _ in (pos_intervals or []):
        ax.axvspan(a, b, alpha=0.18, color="#86efac", zorder=1)
    ax.axhline(0, color="#94a3b8", linestyle="--", linewidth=1, zorder=2)
    if len(bin_centers) > 1:
        ax.plot(bin_centers, ale_vals, color="#7c3aed", linewidth=2.5, marker="o",
                markersize=7, markerfacecolor="#7c3aed", markeredgecolor="#ffffff", markeredgewidth=1.5, zorder=4)
    else:
        ax.hlines(ale_vals[0], bin_centers[0] - 0.5, bin_centers[0] + 0.5, colors="#7c3aed", linewidth=2.5)
    ax.set_title(f"Centered ALE: {feature_name}", fontweight="bold", color="#1e293b", pad=10)
    ax.set_xlabel(feature_name, fontsize=11, color="#334155")
    ax.set_ylabel("ALE", fontsize=11, color="#334155")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)
    fig.tight_layout()
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


# Counterfactual 안정화 패치 적용

# -------------------------------------------------------------
# 공통 유틸
# -------------------------------------------------------------
def safe_predict(model, X_input, feature_names):
    if isinstance(X_input, pd.Series):
        X_input = pd.DataFrame([X_input])
    elif isinstance(X_input, np.ndarray):
        X_input = pd.DataFrame(X_input, columns=feature_names)
    elif not isinstance(X_input, pd.DataFrame):
        raise TypeError("X_input은 Series, ndarray, DataFrame 중 하나여야 합니다.")

    X_input = X_input.reindex(columns=feature_names)
    return model.predict(X_input)


def make_model(model_choice: str):
    if model_choice == "RandomForest":
        return RandomForestRegressor(random_state=42)
    if model_choice == "GradientBoosting":
        return GradientBoostingRegressor(random_state=42)
    if model_choice == "XGBoost":
        return XGBRegressor(random_state=42, objective="reg:squarederror")
    if model_choice == "LGBM":
        return LGBMRegressor(random_state=42)
    if model_choice == "GaussianNB":
        return GaussianNB()
    raise ValueError("지원하지 않는 모델")


def compute_metrics(y_true, y_pred):
    return {
        "MSE": mean_squared_error(y_true, y_pred),
        "MAE": mean_absolute_error(y_true, y_pred),
        "R2": r2_score(y_true, y_pred),
    }


def feature_importance_table(model, features):
    if hasattr(model, "feature_importances_"):
        fi_df = pd.DataFrame({
            "Feature": features,
            "Importance": model.feature_importances_
        }).sort_values("Importance", ascending=False)
    else:
        fi_df = pd.DataFrame({
            "Feature": features,
            "Importance": np.zeros(len(features))
        }).sort_values("Importance", ascending=False)
    return fi_df


def summarize_shap_results(shap_values, features):
    shap_mean_abs = np.abs(shap_values.values).mean(axis=0)
    shap_mean_signed = shap_values.values.mean(axis=0)
    shap_df = pd.DataFrame({
        "Feature": features,
        "Mean(|SHAP|)": shap_mean_abs,
        "Mean(SHAP)": shap_mean_signed,
    }).sort_values("Mean(|SHAP|)", ascending=False)
    return shap_df


def infer_controllable_features(feature_names):
    keywords = ["온도", "습도", "CO2", "CO₂", "일사", "광", "temp", "hum", "humidity", "co2", "solar"]
    selected = []
    for f in feature_names:
        low = str(f).lower()
        fname = str(f)
        if "내부" in fname and ("일사" in fname or "광" in fname):
            continue
        if any(k.lower() in low for k in keywords):
            selected.append(f)
    return selected


def build_window_feature_name(week, suffix):
    return f"{week}주{suffix}"


def pick_column_index(columns, candidates, fallback=0):
    from column_mapping import pick_column_index as _pick
    return _pick(columns, candidates, fallback)


def is_external_cumulative_solar_column(col) -> bool:
    from column_mapping import is_external_cumulative_solar_column as _is
    return _is(col)


def list_external_cumulative_solar_columns(columns):
    from column_mapping import list_external_cumulative_solar_columns as _list
    return _list(columns)


def pick_external_cumulative_solar_index(columns, fallback=None):
    from column_mapping import pick_external_cumulative_solar_index as _pick
    return _pick(columns, fallback)


def pick_external_cumulative_solar_column(columns):
    from column_mapping import pick_external_cumulative_solar_column as _pick
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






def apply_graph_design(fig):
    """사이드바에서 선택한 그래프 스타일을 matplotlib Figure에 공통 적용합니다."""
    base_font = 10 * font_scale
    title_font = 12 * font_scale
    label_font = 10 * font_scale
    tick_font = 9 * font_scale
    lw = 1.4 * line_width_scale

    style_cfg = {
        "기본": {"fig_bg": "white", "ax_bg": "white", "grid": "#d1d5db", "spine": "#64748b", "text": "#0f172a"},
        "논문(Paper)": {"fig_bg": "white", "ax_bg": "white", "grid": "#e5e7eb", "spine": "#111827", "text": "#000000"},
        "발표(Presentation)": {"fig_bg": "#ffffff", "ax_bg": "#f8fafc", "grid": "#cbd5e1", "spine": "#334155", "text": "#0f172a"},
        "다크모드": {"fig_bg": "#0f172a", "ax_bg": "#111827", "grid": "#334155", "spine": "#94a3b8", "text": "#f8fafc"},
        "스마트팜": {"fig_bg": "#f0fdf4", "ax_bg": "#ffffff", "grid": "#bbf7d0", "spine": "#16a34a", "text": "#14532d"},
        "컬러풀": {"fig_bg": "#fff7ed", "ax_bg": "#ffffff", "grid": "#fed7aa", "spine": "#f97316", "text": "#7c2d12"},
    }
    cfg = style_cfg.get(graph_theme, style_cfg["기본"])

    fig.patch.set_facecolor(cfg["fig_bg"])
    for ax in fig.get_axes():
        ax.set_facecolor(cfg["ax_bg"])
        ax.grid(True, linestyle="--", alpha=0.45, color=cfg["grid"])
        ax.title.set_fontsize(title_font)
        ax.title.set_fontweight("bold")
        ax.title.set_color(cfg["text"])
        ax.xaxis.label.set_fontsize(label_font)
        ax.yaxis.label.set_fontsize(label_font)
        ax.xaxis.label.set_color(cfg["text"])
        ax.yaxis.label.set_color(cfg["text"])
        ax.tick_params(axis="both", labelsize=tick_font, colors=cfg["text"])
        for spine in ax.spines.values():
            spine.set_color(cfg["spine"])
            spine.set_linewidth(max(0.8, lw * 0.7))
        for line in ax.lines:
            line.set_linewidth(max(line.get_linewidth(), lw))
        for patch in ax.patches:
            try:
                patch.set_alpha(0.88)
            except Exception:
                pass
        leg = ax.get_legend()
        if leg is not None:
            leg.get_frame().set_alpha(0.85)
            for txt in leg.get_texts():
                txt.set_fontsize(base_font)
                txt.set_color(cfg["text"])
    try:
        fig.tight_layout(pad=0.6)
    except Exception:
        pass
    return fig


def display_matplotlib(fig, use_container_width=True):
    """그래프 스타일을 적용한 뒤 Streamlit에 출력합니다.

    v7에서 이 함수가 자기 자신을 다시 호출하는 재귀 구조가 되어
    RecursionError가 발생하고 Streamlit 세션이 끊기는 문제가 있었습니다.
    실제 출력은 반드시 st.pyplot()로 수행합니다.
    """
    try:
        apply_graph_design(fig)
    except Exception as e:
        st.warning(f"그래프 디자인 적용 중 경고: {e}")

    try:
        st.pyplot(fig, use_container_width=use_container_width)
    except TypeError:
        # 구버전 Streamlit 호환
        st.pyplot(fig)

    try:
        plt.close(fig)
    except Exception:
        pass

def display_plotly(fig, use_container_width=True):
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
        config={
            "scrollZoom": True,
            "displaylogo": False,
            "modeBarButtonsToAdd": ["zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d"],
        },
    )


def style_dataframe(df):
    """표 스타일을 적용해 pandas Styler를 반환합니다. 오류 시 원본 DataFrame 반환."""
    return df


def pretty_time_text(value):
    """보고서/그래프 설명에 표시되는 시간 문자열을 사람이 읽기 쉬운 형태로 변환합니다."""
    if value is None:
        return value
    txt = str(value)
    replacements = {
        "(0818시)": "(08~18시)",
        "(08~18시)": "(08~18시)",
        "(08018시)": "(08~18시)",
        "(1907시)": "(19~07시)",
        "(19~07시)": "(19~07시)",
        "(19007시)": "(19~07시)",
        "(0618시)": "(06~18시)",
        "(06~18시)": "(06~18시)",
        "0818시": "08~18시",
        "1907시": "19~07시",
        "0618시": "06~18시",
    }
    for old, new in replacements.items():
        txt = txt.replace(old, new)
    return txt


def format_interval_text(intervals, limit=3):
    """ALE/PDP 구간을 '23.15 ~ 31.16' 형식으로 안전하게 표시합니다."""
    if not intervals:
        return "없음"
    out = []
    for item in intervals[:limit]:
        try:
            a, b = item[0], item[1]
            out.append(f"{float(a):.2f} ~ {float(b):.2f}")
        except Exception:
            continue
    return ", ".join(out) if out else "없음"


def parse_week_and_base_feature(feature_name: str):
    m = re.search(r"(\d+)주(.+)", str(feature_name))
    if m:
        return int(m.group(1)), m.group(2)
    return None, str(feature_name)


def build_temporal_shap_tables(shap_values, features):
    rows = []
    mean_abs = np.abs(shap_values.values).mean(axis=0)
    mean_signed = shap_values.values.mean(axis=0)

    for feat, abs_val, signed_val in zip(features, mean_abs, mean_signed):
        week, base_feat = parse_week_and_base_feature(feat)
        if week is not None:
            rows.append({
                "Feature": feat,
                "Week": week,
                "BaseFeature": base_feat,
                "Mean(|SHAP|)": float(abs_val),
                "Mean(SHAP)": float(signed_val)
            })

    if len(rows) == 0:
        return None, None, None

    temporal_df = pd.DataFrame(rows)
    week_df = temporal_df.groupby("Week", as_index=False).agg(
        TotalMeanAbsSHAP=("Mean(|SHAP|)", "sum"),
        AvgSignedSHAP=("Mean(SHAP)", "mean"),
        FeatureCount=("Feature", "count")
    ).sort_values("Week")

    heatmap_df = temporal_df.pivot_table(
        index="BaseFeature",
        columns="Week",
        values="Mean(|SHAP|)",
        aggfunc="sum"
    ).fillna(0)

    return temporal_df, week_df, heatmap_df


def explain_shap_summary(shap_df):
    if shap_df is None or shap_df.empty:
        return "SHAP 결과를 요약할 수 없습니다."
    top = shap_df.iloc[0]
    total = shap_df["Mean(|SHAP|)"].sum()
    pct = 100 * top["Mean(|SHAP|)"] / total if total > 0 else 0
    direction = "증가" if top["Mean(SHAP)"] > 0 else "감소"
    return (
        f"가장 영향력이 큰 변수는 '{top['Feature']}'이며, 평균 절대 SHAP 기여도는 {top['Mean(|SHAP|)']:.3f} 입니다. "
        f"전체 중요도 기준 비중은 약 {pct:.1f}% 입니다. 평균 방향성은 예측 {direction} 쪽입니다."
    )


def explain_feature_importance(fi_df):
    if fi_df is None or fi_df.empty:
        return "Feature Importance를 요약할 수 없습니다."
    top = fi_df.iloc[0]
    total = fi_df["Importance"].sum()
    pct = 100 * top["Importance"] / total if total > 0 else 0
    return f"모델 기반 중요도에서 가장 큰 변수는 '{top['Feature']}'이며 중요도는 {top['Importance']:.3f}, 비중은 약 {pct:.1f}% 입니다."


def explain_temporal_shap(week_df, target_name="예측 대상"):
    if week_df is None or week_df.empty:
        return "Temporal SHAP를 계산할 수 없습니다."
    best = week_df.sort_values("TotalMeanAbsSHAP", ascending=False).iloc[0]
    return (
        f"가장 영향력이 큰 시간 구간은 {int(best['Week'])}주 전이며, 총 Mean(|SHAP|)는 {best['TotalMeanAbsSHAP']:.3f} 입니다. "
        f"즉, 모델은 이 시기의 환경이 현재 예측 대상인 ({target_name})에 가장 크게 작용했다고 해석합니다."
    )


def explain_heatmap(heatmap_df, target_name="예측 대상"):
    if heatmap_df is None or heatmap_df.empty:
        return "Feature × Week Heatmap을 계산할 수 없습니다."
    idx = np.unravel_index(np.argmax(heatmap_df.values), heatmap_df.shape)
    best_feat = heatmap_df.index[idx[0]]
    best_week = heatmap_df.columns[idx[1]]
    best_val = heatmap_df.iloc[idx[0], idx[1]]
    return (
        f"({target_name})에 가장 영향력이 큰 조합은 '{best_feat}' × '{best_week}주' 이며, Mean(|SHAP|)는 {best_val:.3f} 입니다. "
        f"즉, {best_week}주 전의 {best_feat} 관리가 핵심이라는 뜻입니다."
    )


def explain_shap_summary_detail(shap_df, target_name, model_choice):
    if shap_df is None or shap_df.empty:
        return "SHAP 상세 설명을 생성할 수 없습니다."

    top_rows = shap_df.head(5).copy()
    total = shap_df["Mean(|SHAP|)"].sum()
    top = top_rows.iloc[0]

    lines = []
    lines.append(
        f"선택한 모델은 {model_choice}이며, 예측 대상은 '{target_name}'입니다. "
        "SHAP Summary는 모델이 예측할 때 어떤 환경 변수를 중요하게 사용했는지 보여줍니다."
    )
    lines.append(
        f"가장 영향력이 큰 변수는 '{top['Feature']}'입니다. "
        f"Mean(|SHAP|) 값은 {top['Mean(|SHAP|)']:.4f}로, 전체 변수 중 예측값 변동에 가장 크게 기여했습니다."
    )

    if top["Mean(SHAP)"] > 0:
        direction_text = "평균적으로 예측값을 증가시키는 방향"
    elif top["Mean(SHAP)"] < 0:
        direction_text = "평균적으로 예측값을 감소시키는 방향"
    else:
        direction_text = "평균적으로 증가/감소 방향성이 뚜렷하지 않은 상태"

    lines.append(
        f"Mean(SHAP)은 {top['Mean(SHAP)']:.4f}로, '{top['Feature']}'는 {direction_text}으로 작용했습니다."
    )

    rank_text = []
    for i, r in top_rows.iterrows():
        pct = 100 * r["Mean(|SHAP|)"] / total if total > 0 else 0
        direction = "증가" if r["Mean(SHAP)"] > 0 else "감소" if r["Mean(SHAP)"] < 0 else "중립"
        rank_text.append(
            f"{len(rank_text)+1}순위: {r['Feature']} "
            f"(중요도 비중 {pct:.1f}%, 방향성: {direction})"
        )

    lines.append("상위 변수 해석: " + " / ".join(rank_text))
    lines.append(
        "해석 시 주의할 점은 Mean(|SHAP|)는 영향력의 크기이고, Mean(SHAP)은 평균적인 방향성입니다. "
        "따라서 중요도가 높더라도 개별 샘플에서는 값의 범위와 다른 변수 조합에 따라 반대 방향으로 작용할 수 있습니다."
    )

    return pretty_time_text("<br><br>".join(lines))


def explain_feature_importance_detail(fi_df, target_name, model_choice):
    if fi_df is None or fi_df.empty:
        return "Feature Importance 상세 설명을 생성할 수 없습니다."

    total = fi_df["Importance"].sum()
    top_rows = fi_df.head(5).copy()
    top = top_rows.iloc[0]

    lines = []
    lines.append(
        f"Feature Importance는 {model_choice} 모델이 '{target_name}'을 예측할 때 "
        "분기 또는 학습 과정에서 어떤 변수를 많이 활용했는지를 나타냅니다."
    )
    lines.append(
        f"가장 중요한 변수는 '{top['Feature']}'이며, 중요도 값은 {top['Importance']:.4f}입니다. "
        f"전체 중요도에서 차지하는 비중은 약 {100 * top['Importance'] / total if total > 0 else 0:.1f}%입니다."
    )

    rank_text = []
    for _, r in top_rows.iterrows():
        pct = 100 * r["Importance"] / total if total > 0 else 0
        rank_text.append(f"{r['Feature']}({pct:.1f}%)")

    lines.append("상위 중요 변수는 " + " → ".join(rank_text) + " 순서입니다.")
    lines.append(
        "Feature Importance는 변수의 사용 빈도와 예측 성능 기여를 보여주지만, 값이 커질 때 예측값이 증가하는지 감소하는지는 직접 알려주지 않습니다. "
        "방향성 해석은 SHAP, PDP, ICE, ALE 결과와 함께 보는 것이 적절합니다."
    )

    return "<br><br>".join(lines)


def explain_heatmap_detail(heatmap_df, temporal_df, target_name):
    if heatmap_df is None or heatmap_df.empty:
        return "Feature × Week Heatmap 상세 설명을 생성할 수 없습니다."

    idx = np.unravel_index(np.argmax(heatmap_df.values), heatmap_df.shape)
    best_feat = heatmap_df.index[idx[0]]
    best_week = int(heatmap_df.columns[idx[1]])
    best_val = heatmap_df.iloc[idx[0], idx[1]]

    week_sum = heatmap_df.sum(axis=0).sort_values(ascending=False)
    feat_sum = heatmap_df.sum(axis=1).sort_values(ascending=False)

    lines = []
    lines.append(
        f"Feature × Week Heatmap은 '{target_name}' 예측에서 환경 변수와 시간 구간이 결합되어 "
        "어느 시점의 어떤 환경이 가장 중요했는지를 보여줍니다."
    )
    lines.append(
        f"가장 강한 조합은 '{best_feat}' × '{best_week}주 전'이며, Mean(|SHAP|)는 {best_val:.4f}입니다. "
        f"이는 {best_week}주 전의 {best_feat} 변화가 현재 예측 대상에 가장 크게 반영되었다는 의미입니다."
    )
    lines.append(
        f"주차 기준으로는 {int(week_sum.index[0])}주 전의 총 영향도가 가장 큽니다. "
        f"변수 기준으로는 '{feat_sum.index[0]}'의 누적 영향도가 가장 큽니다."
    )
    lines.append(
        "이 결과는 환경제어 전략을 세울 때 '언제 제어해야 하는가'와 '어떤 환경변수를 우선 관리해야 하는가'를 동시에 판단하는 데 활용할 수 있습니다."
    )

    return "<br><br>".join(lines)


def explain_shap_sample_intro():
    return (
        "SHAP 샘플별 상세 해석은 전체 평균이 아니라 특정 샘플 1개에 대해 각 변수가 예측값을 얼마나 올리거나 내렸는지 보여줍니다. "
        "즉, 같은 변수라도 어떤 조사일자 또는 개체 데이터에서는 예측값을 증가시키고, 다른 샘플에서는 감소시킬 수 있습니다."
    )


def explain_sample_index(sample_idx, X_test):
    return (
        f"현재 선택한 샘플 인덱스는 X_test 기준 {sample_idx}번입니다. "
        "X_test는 전체 데이터 중 모델 평가용으로 분리된 데이터이므로, 인덱스 번호는 원본 CSV 행 번호와 반드시 일치하지 않을 수 있습니다. "
        "이 값은 테스트 데이터 안에서 몇 번째 샘플을 해석할 것인지를 의미합니다."
    )


def explain_shap_sample_result(shap_sample_df, target_name):
    if shap_sample_df is None or shap_sample_df.empty:
        return "선택 샘플의 SHAP 결과를 설명할 수 없습니다."

    top_pos = shap_sample_df.sort_values("SHAP", ascending=False).head(3)
    top_neg = shap_sample_df.sort_values("SHAP", ascending=True).head(3)
    top_abs = shap_sample_df.reindex(shap_sample_df["SHAP"].abs().sort_values(ascending=False).index).head(1).iloc[0]

    pos_text = ", ".join([f"{r['Feature']}({r['SHAP']:.3f})" for _, r in top_pos.iterrows()])
    neg_text = ", ".join([f"{r['Feature']}({r['SHAP']:.3f})" for _, r in top_neg.iterrows()])

    return (
        f"선택한 샘플에서 '{target_name}' 예측에 가장 크게 작용한 변수는 '{top_abs['Feature']}'입니다. "
        f"해당 SHAP 값은 {top_abs['SHAP']:.4f}입니다. "
        f"양의 SHAP 값은 예측값을 증가시키는 방향, 음의 SHAP 값은 예측값을 감소시키는 방향으로 해석합니다.<br><br>"
        f"예측값을 증가시킨 주요 변수는 {pos_text}입니다.\n\n"
        f"예측값을 감소시킨 주요 변수는 {neg_text}입니다."
    )


def explain_ice_pdp_result(feature, mean_slope, std_slope, pdp_summary, target_name="예측 대상"):
    feature_display = pretty_time_text(feature)
    start, end = pdp_summary["best_interval"]
    slope_direction = "증가" if mean_slope > 0 else "감소" if mean_slope < 0 else "거의 변화 없음"

    ice_text = f"""
<div style="background:linear-gradient(135deg,#ffffff,#eef5ff); box-shadow:0 6px 20px rgba(0,0,0,0.06); padding:18px; border-radius:14px; line-height:1.75; font-size:15px; word-break:keep-all; overflow-wrap:break-word;">
<b>ICE 그래프 해석</b><br><br>
ICE 곡선은 개별 샘플마다 <b>{feature_display}</b> 값이 변할 때 예측대상값(<b>{target_name}</b>)이 어떻게 달라지는지 보여줍니다.<br><br>
<table style="width:100%; border-collapse:collapse; font-size:14px;">
<thead><tr style="border-bottom:2px solid #d1d5db;"><th style="text-align:left; padding:8px;">항목</th><th style="text-align:left; padding:8px;">결과 해석</th></tr></thead>
<tbody>
<tr style="border-bottom:1px solid #e5e7eb;"><td style="padding:8px;">선택 Feature</td><td style="padding:8px;">{feature_display}</td></tr>
<tr style="border-bottom:1px solid #e5e7eb;"><td style="padding:8px;">평균 기울기</td><td style="padding:8px;">{mean_slope:.4f} ± {std_slope:.4f}</td></tr>
<tr style="border-bottom:1px solid #e5e7eb;"><td style="padding:8px;">전체 경향</td><td style="padding:8px;">예측값({target_name})이 전반적으로 <b>{slope_direction}</b>하는 경향</td></tr>
<tr><td style="padding:8px;">해석 포인트</td><td style="padding:8px;">곡선들이 서로 많이 벌어져 있으면 개체별 또는 조사일자별 반응 차이가 크다는 의미입니다.</td></tr>
</tbody></table>
</div>
"""

    pdp_text = f"""
<div style="background:linear-gradient(135deg,#ffffff,#f8fbff); box-shadow:0 6px 20px rgba(0,0,0,0.06); padding:18px; border-radius:14px; line-height:1.75; font-size:15px; word-break:keep-all; overflow-wrap:break-word;">
<b>PDP 그래프 해석</b><br><br>
PDP는 모든 샘플에 대해 <b>{feature_display}</b>만 변화시켰을 때 평균 예측값(<b>{target_name} 평균값</b>)이 어떻게 변하는지 보여줍니다.<br><br>
<table style="width:100%; border-collapse:collapse; font-size:14px;">
<thead><tr style="border-bottom:2px solid #d1d5db;"><th style="text-align:left; padding:8px;">항목</th><th style="text-align:left; padding:8px;">결과</th></tr></thead>
<tbody>
<tr style="border-bottom:1px solid #e5e7eb;"><td style="padding:8px;">최적 구간</td><td style="padding:8px;"><b>{start:.3f} ~ {end:.3f}</b></td></tr>
<tr style="border-bottom:1px solid #e5e7eb;"><td style="padding:8px;">구간 평균 예측값</td><td style="padding:8px;">{pdp_summary['mean_val']:.3f}</td></tr>
<tr style="border-bottom:1px solid #e5e7eb;"><td style="padding:8px;">구간 최대 예측값</td><td style="padding:8px;">{pdp_summary['max_val']:.3f}</td></tr>
<tr><td style="padding:8px;">해석 포인트</td><td style="padding:8px;">PDP 최적 구간은 전체 평균 반응 기준으로 예측대상({target_name})이 높게 나타나는 관리 후보 구간입니다.</td></tr>
</tbody></table>
</div>
"""

    combined_text = f"""
<div style="background:linear-gradient(135deg,#ffffff,#eef5ff); box-shadow:0 6px 20px rgba(0,0,0,0.06); padding:18px; border-radius:14px; line-height:1.75; font-size:15px; word-break:keep-all; overflow-wrap:break-word;">
<b>ICE + PDP 통합 해석</b><br><br>
<table style="width:100%; border-collapse:collapse; font-size:14px;">
<thead><tr style="border-bottom:2px solid #d1d5db;"><th style="text-align:left; padding:8px;">구분</th><th style="text-align:left; padding:8px;">의미</th><th style="text-align:left; padding:8px;">의사결정 활용</th></tr></thead>
<tbody>
<tr style="border-bottom:1px solid #e5e7eb;"><td style="padding:8px;">ICE</td><td style="padding:8px;">개별 샘플의 반응</td><td style="padding:8px;">개체별·조사일자별 반응 차이 확인</td></tr>
<tr style="border-bottom:1px solid #e5e7eb;"><td style="padding:8px;">PDP</td><td style="padding:8px;">전체 평균 반응</td><td style="padding:8px;">평균적으로 유리한 제어 구간 파악</td></tr>
<tr><td style="padding:8px;">종합 판단</td><td style="padding:8px;">PDP가 상승하더라도 ICE 편차가 크면 일괄 제어보다 단계적 제어가 적합</td><td style="padding:8px;">최적 구간 {start:.3f} ~ {end:.3f}을 기준으로 현장 조건과 함께 검토</td></tr>
</tbody></table>
</div>
"""

    return ice_text, pdp_text, combined_text
def explain_centered_ale_result(feature, bin_centers, ale_vals, ale_summary, target_name="예측 대상"):
    if bin_centers is None or len(bin_centers) == 0:
        return "Centered ALE 결과를 설명할 수 없습니다."

    bin_centers = np.array(bin_centers, dtype=float)
    ale_vals = np.array(ale_vals, dtype=float)

    max_idx = int(np.argmax(ale_vals))
    min_idx = int(np.argmin(ale_vals))

    pos_mask = ale_vals > 0
    near_zero_mask = np.abs(ale_vals) <= max(0.05, 0.05 * (np.nanmax(np.abs(ale_vals)) + 1e-9))
    neg_mask = ale_vals < 0

    def get_range(mask):
        idxs = np.where(mask)[0]
        if len(idxs) == 0:
            return None
        return float(bin_centers[idxs[0]]), float(bin_centers[idxs[-1]])

    pos_range = get_range(pos_mask)
    neg_range = get_range(neg_mask)
    zero_range = get_range(near_zero_mask)

    if pos_range is not None:
        pos_start, pos_end = pos_range
        first_sentence = (
            f"<b>{pos_start:.2f}~{pos_end:.2f}</b> 구간이 "
            f"<b>{target_name} 증가에 유리한 구간</b>으로 해석할 수 있습니다.<br>"
            f"다만 “값이 계속 높을수록 계속 증가한다”는 뜻은 아닙니다."
        )
    else:
        first_sentence = (
            f"현재 Centered ALE 결과에서는 <b>{target_name} 증가에 유리한 양의 ALE 구간</b>이 명확하지 않습니다."
        )

    if neg_range is not None:
        neg_text = f"약 {neg_range[0]:.2f}~{neg_range[1]:.2f}"
    else:
        neg_text = "뚜렷하지 않음"

    if zero_range is not None:
        zero_text = f"약 {zero_range[0]:.2f}~{zero_range[1]:.2f}"
    else:
        zero_text = "0 근처 구간이 뚜렷하지 않음"

    if pos_range is not None:
        pos_text = f"약 {pos_range[0]:.2f} 이상"
        pos_full = f"약 {pos_range[0]:.2f}~{pos_range[1]:.2f}"
    else:
        pos_text = "뚜렷하지 않음"
        pos_full = "뚜렷하지 않음"

    best_text = f"약 {bin_centers[max_idx]:.2f}"
    high_effect_text = "여전히 양수이나 최고점보다 낮음 → 증가 효과는 유지되나 약해짐"

    return f"""
<div style="background:linear-gradient(135deg,#ffffff,#eef5ff); 
            box-shadow:0 6px 20px rgba(0,0,0,0.06);
            padding:18px;
            border-radius:14px;
            line-height:1.85;
            font-size:16px;
            word-break:keep-all;
            overflow-wrap:break-word;">

{first_sentence}<br><br>

<b>그래프 해석은 다음과 같습니다.</b><br><br>

<b>Centered ALE = 0</b>은 평균적인 기준선입니다.<br>
0보다 아래는 해당 구간이 <b>{target_name} 예측을 평균보다 낮추는 방향</b>, 
0보다 위는 <b>평균보다 높이는 방향</b>으로 작용했다는 의미입니다.<br><br>

<b>그래프를 보면:</b><br><br>

<table style="width:100%; border-collapse:collapse; font-size:15px;">
<thead>
<tr style="border-bottom:2px solid #d1d5db;">
<th style="text-align:left; padding:8px;">{feature}</th>
<th style="text-align:left; padding:8px;">해석</th>
</tr>
</thead>
<tbody>
<tr style="border-bottom:1px solid #e5e7eb;">
<td style="padding:8px;">{neg_text}</td>
<td style="padding:8px;">ALE가 음수 → {target_name} 예측 감소 구간</td>
</tr>
<tr style="border-bottom:1px solid #e5e7eb;">
<td style="padding:8px;">{zero_text}</td>
<td style="padding:8px;">0 근처 → 영향이 거의 중립</td>
</tr>
<tr style="border-bottom:1px solid #e5e7eb;">
<td style="padding:8px;">{pos_text}</td>
<td style="padding:8px;">ALE가 양수 → {target_name} 예측 증가 구간</td>
</tr>
<tr style="border-bottom:1px solid #e5e7eb;">
<td style="padding:8px;">{best_text} 부근</td>
<td style="padding:8px;">ALE가 가장 높음 → 가장 유리한 구간</td>
</tr>
<tr>
<td style="padding:8px;">양의 구간 후반부</td>
<td style="padding:8px;">{high_effect_text}</td>
</tr>
</tbody>
</table>

<br>
따라서 <b>{pos_full} 전체를 “{target_name} 증가구간”이라고 말할 수는 있지만</b>, 더 정확히는:<br><br>

<div style="border-left:5px solid #cbd5e1; padding-left:14px; font-weight:600;">
{feature}가 약 {pos_range[0]:.2f} 이상일 때 {target_name} 예측에 긍정적으로 작용했으며, 
특히 약 {bin_centers[max_idx]:.2f} 부근에서 가장 큰 증가 효과가 나타났다.
</div>

</div>
"""



def _counterfactual_recommendation(feature_name, change):
    """환경변수별 제어 방향 설명"""
    fname = str(feature_name)
    up = change > 0

    if "일사" in fname or "광" in fname:
        return (
            "보광등 점등, 차광 시간 축소, 피복재 세척, 광 투과율 개선"
            if up else
            "차광 스크린 활용, 환기·냉방 강화, 엽온 상승 억제"
        )
    if "주간온도" in fname:
        return (
            "난방·보온 강화 또는 환기 지연으로 주간온도 확보"
            if up else
            "천창 개방, 팬 가동, 차광·냉방으로 주간 고온 완화"
        )
    if "야간온도" in fname:
        return (
            "야간 보온, 난방, 보온커튼 활용"
            if up else
            "야간 환기, 보온커튼 개폐 조정, 과도한 야간온도 완화"
        )
    if "습도" in fname:
        return (
            "가습, 관수량 점검, 과도한 환기 완화"
            if up else
            "환기, 제습, 난방, 순환팬으로 결로·과습 완화"
        )
    if "CO₂" in fname or "CO2" in fname:
        return (
            "주간 CO₂ 시비, 환기 타이밍 조정, 광량과 함께 관리"
            if up else
            "CO₂ 공급량 축소, 환기 강화, 과다 시비 점검"
        )
    return "현장 조건과 생육단계를 함께 검토하여 제어 방향 결정"


def _counterfactual_control_group(feature_name):
    fname = str(feature_name)
    if "일사" in fname or "광" in fname:
        return "광환경"
    if "온도" in fname:
        return "온도"
    if "습도" in fname:
        return "습도/VPD"
    if "CO₂" in fname or "CO2" in fname:
        return "CO₂"
    return "기타"


def generate_counterfactual(
    model,
    x_row,
    X_ref,
    feature_names,
    target_delta=1.0,
    n_iter=2000,
    random_state=42,
    top_n=5,
):
    """
    표준화 기반 Top-N Counterfactual 환경제어 후보 탐색.

    기존 방식은 Original 대비 Counterfactual 값의 절대 변화량이 큰 변수가 상위에 오기 쉬워
    단위가 큰 누적일사량이 반복적으로 선택될 수 있습니다.
    이 함수는 각 변수의 표준편차 기준 변화량(StdChange)과 예측 개선량(PredDelta)을 함께 사용하여
    PriorityScore를 계산하고, Top-N 환경제어 후보를 제시합니다.
    """
    x0 = x_row.copy()
    x0 = x0.reindex(feature_names)

    X_ref_num = X_ref.copy().reindex(columns=feature_names)
    X_ref_num = X_ref_num.apply(pd.to_numeric, errors="coerce")

    base_pred = float(safe_predict(model, x0, feature_names)[0])

    controllable = infer_controllable_features(feature_names)
    if len(controllable) == 0:
        controllable = list(feature_names)

    q05 = X_ref_num.quantile(0.05, numeric_only=True)
    q95 = X_ref_num.quantile(0.95, numeric_only=True)
    means = X_ref_num.mean(numeric_only=True)
    stds = X_ref_num.std(numeric_only=True).replace(0, np.nan)

    step_grid = [-1.0, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1.0]
    rows = []

    for feat in controllable:
        if feat not in feature_names:
            continue

        original = pd.to_numeric(pd.Series([x0.get(feat, np.nan)]), errors="coerce").iloc[0]
        if pd.isna(original):
            original = means.get(feat, np.nan)

        std = stds.get(feat, np.nan)
        lo = q05.get(feat, np.nan)
        hi = q95.get(feat, np.nan)

        if pd.isna(original) or pd.isna(std) or std == 0 or pd.isna(lo) or pd.isna(hi) or lo == hi:
            continue

        best_local = None

        for step in step_grid:
            cand = x0.copy()
            new_val = float(np.clip(original + step * std, lo, hi))
            cand[feat] = new_val

            pred = float(safe_predict(model, cand, feature_names)[0])
            pred_delta = pred - base_pred
            change = new_val - original
            std_change = change / std if std != 0 else 0.0

            # 표준화 기반 점수: 예측개선량을 표준화 변화량으로 나눠 단위가 큰 변수가 과대평가되지 않도록 함
            efficiency = pred_delta / (abs(std_change) + 1e-6)
            priority = pred_delta + 0.25 * efficiency

            candidate = {
                "Feature": feat,
                "ControlGroup": _counterfactual_control_group(feat),
                "Original": original,
                "Counterfactual": new_val,
                "Change": change,
                "AbsChange": abs(change),
                "StdChange": std_change,
                "AbsStdChange": abs(std_change),
                "PredBefore": base_pred,
                "PredAfter": pred,
                "PredDelta": pred_delta,
                "PriorityScore": priority,
                "Direction": "증가" if change > 0 else "감소" if change < 0 else "유지",
                "Recommendation": _counterfactual_recommendation(feat, change),
            }

            if best_local is None or candidate["PriorityScore"] > best_local["PriorityScore"]:
                best_local = candidate

        if best_local is not None:
            rows.append(best_local)

    if len(rows) == 0:
        empty = pd.DataFrame(columns=[
            "Feature", "ControlGroup", "Original", "Counterfactual", "Change",
            "AbsChange", "StdChange", "PredDelta", "PriorityScore", "Recommendation"
        ])
        return {
            "base_pred": base_pred,
            "cf_pred": base_pred,
            "desired": base_pred + target_delta,
            "diff_df": empty,
            "priority_df": empty,
            "method": "standardized_topn",
        }

    priority_df = pd.DataFrame(rows)
    priority_df = priority_df.sort_values(
        ["PredDelta", "PriorityScore", "AbsStdChange"],
        ascending=[False, False, False]
    ).reset_index(drop=True)

    # 예측 개선이 양수인 후보 중심으로 Top-N 선정하되,
    # 동일 제어군(예: 광환경)만 반복 추천되는 것을 줄이기 위해 제어군별 대표 후보를 먼저 뽑습니다.
    positive_df = priority_df[priority_df["PredDelta"] > 0].copy()
    candidate_pool = positive_df if not positive_df.empty else priority_df.copy()

    selected_rows = []
    used_groups = set()

    for _, row in candidate_pool.iterrows():
        group = row.get("ControlGroup", "기타")
        if group not in used_groups:
            selected_rows.append(row)
            used_groups.add(group)
        if len(selected_rows) >= top_n:
            break

    # 제어군이 부족하면 나머지는 점수 순으로 보충합니다.
    if len(selected_rows) < top_n:
        used_features = {r["Feature"] for r in selected_rows}
        for _, row in candidate_pool.iterrows():
            if row["Feature"] not in used_features:
                selected_rows.append(row)
                used_features.add(row["Feature"])
            if len(selected_rows) >= top_n:
                break

    selected_df = pd.DataFrame(selected_rows) if selected_rows else candidate_pool.head(top_n).copy()

    # 복합 counterfactual: Top-N 후보를 동시에 적용하되, 각 변수는 표준화 변화가 큰 값으로 제한
    best_candidate = x0.copy()
    for _, r in selected_df.iterrows():
        best_candidate[r["Feature"]] = r["Counterfactual"]

    cf_pred = float(safe_predict(model, best_candidate, feature_names)[0])

    diff_df = pd.DataFrame({
        "Feature": feature_names,
        "Original": x0[feature_names].values,
        "Counterfactual": best_candidate[feature_names].values,
    })
    diff_df["Original"] = pd.to_numeric(diff_df["Original"], errors="coerce")
    diff_df["Counterfactual"] = pd.to_numeric(diff_df["Counterfactual"], errors="coerce")
    diff_df["Change"] = diff_df["Counterfactual"] - diff_df["Original"]

    std_map = stds.reindex(feature_names)
    diff_df["Std"] = diff_df["Feature"].map(std_map)
    diff_df["StdChange"] = diff_df["Change"] / diff_df["Std"].replace(0, np.nan)
    diff_df["AbsChange"] = diff_df["Change"].abs()
    diff_df["AbsStdChange"] = diff_df["StdChange"].abs()
    diff_df["ControlGroup"] = diff_df["Feature"].apply(_counterfactual_control_group)
    diff_df["Recommendation"] = diff_df.apply(
        lambda r: _counterfactual_recommendation(r["Feature"], r["Change"]),
        axis=1
    )

    score_map = priority_df.set_index("Feature")["PriorityScore"].to_dict()
    pred_map = priority_df.set_index("Feature")["PredDelta"].to_dict()
    diff_df["PredDelta"] = diff_df["Feature"].map(pred_map).fillna(0)
    diff_df["PriorityScore"] = diff_df["Feature"].map(score_map).fillna(0)

    diff_df = diff_df.sort_values(
        ["PredDelta", "PriorityScore", "AbsStdChange"],
        ascending=[False, False, False]
    ).reset_index(drop=True)

    return {
        "base_pred": base_pred,
        "cf_pred": cf_pred,
        "desired": base_pred + target_delta,
        "diff_df": diff_df,
        "priority_df": priority_df,
        "selected_df": selected_df,
        "method": "standardized_topn",
    }


def explain_counterfactual(cf_result, target_name):
    if cf_result is None:
        return "Counterfactual 결과를 생성하지 못했습니다."

    delta = cf_result["cf_pred"] - cf_result["base_pred"]
    direction = "증가" if delta > 0 else "감소" if delta < 0 else "변화 없음"

    return (
        f"Counterfactual 시뮬레이션 결과, 예측 대상({target_name})은 "
        f"{cf_result['base_pred']:.3f}에서 {cf_result['cf_pred']:.3f}로 {direction}했습니다.<br><br>"
        f"변화량은 {delta:.3f}입니다.<br><br>"
        "이번 방식은 단순 Change가 아니라 <b>표준화 변화량(StdChange)</b>과 "
        "<b>예측 개선량(PredDelta)</b>을 함께 고려하여 Top-N 환경제어 후보를 선발합니다. "
        "따라서 누적일사량처럼 단위가 큰 변수가 무조건 1순위가 되는 문제를 줄이고, "
        "온도·습도·CO₂·일사량의 상대적 개선 효과를 함께 비교합니다."
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

def build_monthly_environment_zone_table(df, date_col, feature_name, value_col):
    temp_df = df[[date_col, value_col]].copy()
    temp_df[date_col] = pd.to_datetime(temp_df[date_col], errors="coerce")
    temp_df[value_col] = pd.to_numeric(temp_df[value_col], errors="coerce")
    temp_df = temp_df.dropna(subset=[date_col])

    if temp_df.empty:
        return pd.DataFrame(columns=["월", "평균값", "환경구간", "영향 설명"])

    temp_df["월"] = temp_df[date_col].dt.to_period("M").astype(str)

    monthly = (
        temp_df
        .groupby("월", as_index=False)[value_col]
        .mean()
        .rename(columns={value_col: "평균값"})
    )

    zones = monthly["평균값"].apply(lambda v: classify_environment_zone(feature_name, v))
    monthly["환경구간"] = [z[0] for z in zones]
    monthly["영향 설명"] = [z[1] for z in zones]

    return monthly.round({"평균값": 3})


def environment_zone_reference_table(feature_name):
    rows = []
    fname = str(feature_name)

    if "주간온도" in fname:
        rows = [
            ["최저한계구간", "< 15℃", "생육 정지·저온장해 위험, 보온/난방 필요"],
            ["저온구간", "15~20℃", "광합성·과실 비대 둔화 가능"],
            ["최적구간", "20~24℃", "주간 광합성·증산 균형에 유리"],
            ["고온구간", "24~30℃", "증산·호흡 증가, 환기·수분 관리 필요"],
            ["최고한계구간", "≥ 30℃", "고온 스트레스·착과 불량·품질 저하 위험"],
        ]
    elif "야간온도" in fname:
        rows = [
            ["최저한계구간", "< 10℃", "야간 저온장해·생육 정지 위험, 보온 필요"],
            ["저온구간", "10~15℃", "양분 이동과 생육 회복 둔화 가능"],
            ["최적구간", "15~18℃", "호흡과 당 소모 균형에 유리"],
            ["고온구간", "18~23℃", "야간 호흡 증가로 당 소모 확대"],
            ["최고한계구간", "≥ 23℃", "야간 고온 스트레스·생장 불균형 위험"],
        ]
    elif "온도" in fname:
        rows = [
            ["최저한계구간", "< 15℃", "저온장해·생육 정지 위험"],
            ["저온구간", "15~20℃", "광합성·양분 흡수 둔화 가능"],
            ["최적구간", "20~24℃", "광합성·호흡 균형이 좋아 안정적 생육에 유리"],
            ["고온구간", "24~30℃", "증산·호흡 증가, 환기·수분 관리 필요"],
            ["최고한계구간", "≥ 30℃", "고온 스트레스, 착과 불량, 품질 저하 위험"],
        ]
    elif "습도" in fname:
        rows = [
            ["최저한계구간", "< 40%", "극건조, VPD 과다, 위조 위험"],
            ["저습구간", "40~60%", "건조 스트레스, 증산 과다 가능"],
            ["최적구간", "60~80%", "증산과 기공 조절이 안정적인 구간"],
            ["다습구간", "80~90%", "결로·병해 위험 증가"],
            ["최고한계구간", "≥ 90%", "과습·결로·병해 확산 위험"],
        ]
    elif "CO₂" in fname or "CO2" in fname:
        rows = [
            ["최저한계구간", "< 350ppm", "CO₂ 부족으로 광합성 제한 가능"],
            ["저농도구간", "350~400ppm", "외기 수준 이하, CO₂ 보충 검토"],
            ["중간구간", "400~800ppm", "일반 생육 가능, 시비 효과 제한적"],
            ["최적구간", "800~1200ppm", "광합성 촉진에 유리"],
            ["최고한계구간", "≥ 1200ppm", "과다 공급 또는 환기 부족 가능성"],
        ]
    elif "일사" in fname or "광" in fname:
        rows = [
            ["최저한계구간", "< 300", "광 부족, 동화산물 생산 크게 감소"],
            ["저광구간", "300~500", "보광 검토 필요"],
            ["중간구간", "500~1200", "기본 광합성 가능, 생육단계별 관리 필요"],
            ["최적구간", "1200~2000", "광합성과 당 생산에 유리"],
            ["최고한계구간", "≥ 2000", "고온·건조·엽온 상승 위험, 차광/냉방 검토"],
        ]
    else:
        rows = [["기타", "사용자 정의", "작물·생육단계에 맞는 기준 설정 필요"]]

    return pd.DataFrame(rows, columns=["환경구간", "기준", "영향"])

def compute_rolling_summary(sensor_df, yield_df, date_col_sensor, date_col_yield,
                            temp_col, hum_col, co2_col, solar_col,
                            harvest_count_col, harvest_weight_col,
                            growth_cols, week):
    days = week * 7
    temp_day_col_name = build_window_feature_name(week, "평균주간온도(08~18시)")
    temp_night_col_name = build_window_feature_name(week, "평균야간온도(19~07시)")
    hum_day_col_name = build_window_feature_name(week, "평균주간습도(08~18시)")
    hum_night_col_name = build_window_feature_name(week, "평균야간습도(19~07시)")
    co2_day_col_name = build_window_feature_name(week, "평균주간CO₂(08~18시)")
    co2_night_col_name = build_window_feature_name(week, "평균야간CO₂(19~07시)")
    solar_col_name = build_window_feature_name(week, "평균누적일사량(1일최대값기준)")

    results = []
    sensor_dates = pd.to_datetime(sensor_df[date_col_sensor], errors="coerce")

    for _, row in yield_df.iterrows():
        date = pd.to_datetime(row[date_col_yield], errors="coerce")
        if pd.isna(date):
            continue
        start_date = date - timedelta(days=days)
        mask = (sensor_dates >= start_date) & (sensor_dates <= date)
        subset = sensor_df.loc[mask].copy()

        avg_solar = np.nan
        avg_co2_day = np.nan
        avg_co2_night = np.nan
        avg_temp_day = np.nan
        avg_temp_night = np.nan
        avg_hum_day = np.nan
        avg_hum_night = np.nan

        if not subset.empty:
            # 일별 누적일사량 최대값 사용 (24시간 중 최대값)
            subset[solar_col] = pd.to_numeric(subset[solar_col], errors="coerce")
            daily_max_solar = (
                subset.groupby("date")[solar_col]
                .max()
                .reset_index()
            )
            if not daily_max_solar.empty:
                avg_solar = daily_max_solar[solar_col].mean()

            # 주간 평균 CO₂ (08~18시)
            co2_daytime = subset[
                (subset["hour"] >= 8) &
                (subset["hour"] <= 18)
            ]

            if not co2_daytime.empty:
                co2_day_mean = co2_daytime.groupby("date")[co2_col].mean().reset_index()

                if not co2_day_mean.empty:
                    avg_co2_day = pd.to_numeric(
                        co2_day_mean[co2_col],
                        errors="coerce"
                    ).mean()

            # 야간 평균 CO₂ (19~07시)
            co2_nighttime = subset[
                (subset["hour"] >= 19) |
                (subset["hour"] <= 7)
            ]

            if not co2_nighttime.empty:
                co2_night_mean = co2_nighttime.groupby("date")[co2_col].mean().reset_index()

                if not co2_night_mean.empty:
                    avg_co2_night = pd.to_numeric(
                        co2_night_mean[co2_col],
                        errors="coerce"
                    ).mean()

            # 주간 평균온도 (08~18시)
            temp_daytime = subset[
                (subset["hour"] >= 8) &
                (subset["hour"] <= 18)
            ]

            if not temp_daytime.empty and temp_col in temp_daytime.columns:
                avg_temp_day = pd.to_numeric(
                    temp_daytime[temp_col],
                    errors="coerce"
                ).mean()

            # 야간 평균온도 (19~07시)
            temp_nighttime = subset[
                (subset["hour"] >= 19) |
                (subset["hour"] <= 7)
            ]

            if not temp_nighttime.empty and temp_col in temp_nighttime.columns:
                avg_temp_night = pd.to_numeric(
                    temp_nighttime[temp_col],
                    errors="coerce"
                ).mean()

            # 주간 평균습도 (08~18시)
            hum_daytime = subset[(subset["hour"] >= 8) & (subset["hour"] <= 18)]
            if not hum_daytime.empty and hum_col in hum_daytime.columns:
                avg_hum_day = pd.to_numeric(hum_daytime[hum_col], errors="coerce").mean()

            # 야간 평균습도 (19~07시)
            hum_nighttime = subset[(subset["hour"] >= 19) | (subset["hour"] <= 7)]
            if not hum_nighttime.empty and hum_col in hum_nighttime.columns:
                avg_hum_night = pd.to_numeric(hum_nighttime[hum_col], errors="coerce").mean()

        result_row = {
            "조사일자": date,
            "수확수": row[harvest_count_col] if harvest_count_col in row else np.nan,
            "착과수": row[harvest_weight_col] if harvest_weight_col in row else np.nan,
            temp_day_col_name: avg_temp_day,
            temp_night_col_name: avg_temp_night,
            hum_day_col_name: avg_hum_day,
            hum_night_col_name: avg_hum_night,
            co2_day_col_name: avg_co2_day,
            co2_night_col_name: avg_co2_night,
            solar_col_name: avg_solar,
        }

        for gf, col in growth_cols.items():
            if col and col in row.index:
                result_row[gf] = row[col]
            else:
                result_row[gf] = np.nan

        results.append(result_row)

    out = pd.DataFrame(results)
    if out.empty or "조사일자" not in out.columns:
        base_cols = ["조사일자", "수확수", "착과수", temp_day_col_name, temp_night_col_name,
                     hum_day_col_name, hum_night_col_name, co2_day_col_name, co2_night_col_name, solar_col_name]
        base_cols += [gf for gf in growth_cols]
        return pd.DataFrame(columns=base_cols)
    return out.sort_values("조사일자").reset_index(drop=True)




def explain_environment_timeseries(feature_name, values):
    vals = pd.Series(values).dropna()
    if len(vals) == 0:
        return "데이터가 부족하여 시계열 설명을 생성할 수 없습니다."

    mean_v = vals.mean()
    min_v = vals.min()
    max_v = vals.max()
    std_v = vals.std()
    last_v = vals.iloc[-1]

    lines = [
        f"'{feature_name}' 시계열의 평균은 {mean_v:.2f}, 최소 {min_v:.2f}, 최대 {max_v:.2f}, 표준편차는 {std_v:.2f}입니다.",
        f"최근값은 {last_v:.2f}입니다."
    ]

    if "온도" in feature_name:
        if mean_v < 20:
            lines.append("20℃ 미만은 저온 구간으로 광합성·양분 흡수·과실 비대가 둔화될 수 있습니다.")
        elif mean_v < 24:
            lines.append("20~24℃는 비교적 적정 구간으로 광합성과 호흡 균형이 안정적입니다.")
        elif mean_v < 30:
            lines.append("24~30℃는 생육은 활발할 수 있으나 증산과 호흡이 증가하여 환기·수분 관리가 중요합니다.")
        else:
            lines.append("30℃ 이상은 고온 스트레스 위험 구간으로 착과 불량과 품질 저하가 발생할 수 있습니다.")
    elif "습도" in feature_name:
        if mean_v < 60:
            lines.append("60% 미만은 건조 구간으로 VPD 상승과 수분 스트레스 가능성이 있습니다.")
        elif mean_v < 80:
            lines.append("60~80%는 비교적 적정 습도 구간으로 증산 균형 유지에 유리합니다.")
        else:
            lines.append("80% 이상은 다습 구간으로 결로와 병해 위험이 증가할 수 있습니다.")
    elif "CO₂" in feature_name or "CO2" in feature_name:
        if mean_v < 400:
            lines.append("400ppm 미만은 CO₂ 부족 구간으로 광합성이 제한될 수 있습니다.")
        elif mean_v < 800:
            lines.append("400~800ppm은 일반적인 생육 가능 구간입니다.")
        elif mean_v < 1200:
            lines.append("800~1200ppm은 광합성 촉진에 유리한 구간입니다.")
        else:
            lines.append("1200ppm 이상은 과다 구간으로 환기 부족 또는 CO₂ 낭비 가능성이 있습니다.")
    elif "일사" in feature_name or "광" in feature_name:
        lines.append("일사량은 광합성 에너지 공급량과 연관되며 온도·CO₂·수분 상태와 함께 해석해야 합니다.")

    return "<br><br>".join(lines)


def generate_comprehensive_report(
    model_choice,
    target_col,
    metrics,
    weekly_metrics_df=None,
    shap_df=None,
    fi_df=None,
    week_importance=None,
    heatmap_df=None,
    cf_result=None,
    ice_feature=None,
    ice_mean_slope=None,
    ice_std_slope=None,
    pdp_summary=None,
    ale_summary=None,
    bin_centers=None,
    ale_vals=None,
):
    lines = []

    lines.append(
        f"<b>1. 분석 개요</b><br>"
        f"본 분석은 <b>{model_choice}</b> 모델을 이용하여 "
        f"<b>{target_col}</b>을 예측하고, 모델 성능과 XAI 결과를 종합적으로 해석한 리포트입니다."
    )

    if metrics is not None:
        lines.append(
            f"<b>2. 선택 주차 모델 성능</b><br>"
            f"현재 선택된 주차 기준 모델 성능은 "
            f"MSE=<b>{metrics.get('MSE', np.nan):.4f}</b>, "
            f"MAE=<b>{metrics.get('MAE', np.nan):.4f}</b>, "
            f"R²=<b>{metrics.get('R2', np.nan):.4f}</b>입니다. "
            "MSE와 MAE는 낮을수록 오차가 작고, R²는 높을수록 설명력이 높습니다."
        )

    if weekly_metrics_df is not None and not weekly_metrics_df.empty:
        best_r2 = weekly_metrics_df.sort_values("R2", ascending=False).iloc[0]
        best_mse = weekly_metrics_df.sort_values("MSE", ascending=True).iloc[0]
        best_mae = weekly_metrics_df.sort_values("MAE", ascending=True).iloc[0]

        lines.append(
            f"<b>3. 1~7주 모델 성능 비교</b><br>"
            f"1~7주 전체 비교에서 R²가 가장 높은 구간은 <b>{int(best_r2['Week'])}주</b> "
            f"(R²={best_r2['R2']:.4f})입니다. "
            f"MSE가 가장 낮은 구간은 <b>{int(best_mse['Week'])}주</b> "
            f"(MSE={best_mse['MSE']:.4f})이며, "
            f"MAE가 가장 낮은 구간은 <b>{int(best_mae['Week'])}주</b> "
            f"(MAE={best_mae['MAE']:.4f})입니다. "
            "따라서 성능 기준으로 어떤 기간의 환경 누적 정보가 예측에 가장 적합한지 판단할 수 있습니다."
        )

    if shap_df is not None and not shap_df.empty:
        top_shap = shap_df.iloc[0]
        direction = "증가" if top_shap["Mean(SHAP)"] > 0 else "감소" if top_shap["Mean(SHAP)"] < 0 else "중립"
        lines.append(
            f"<b>4. SHAP Summary 종합 해석</b><br>"
            f"SHAP 기준 가장 영향력이 큰 변수는 <b>{pretty_time_text(top_shap['Feature'])}</b>입니다. "
            f"Mean(|SHAP|)={top_shap['Mean(|SHAP|)']:.4f}, "
            f"Mean(SHAP)={top_shap['Mean(SHAP)']:.4f}로 나타났습니다. "
            f"이는 해당 변수가 예측값에 가장 크게 기여했으며, 평균적으로 예측값을 <b>{direction}</b>시키는 방향으로 작용했음을 의미합니다."
        )

    if fi_df is not None and not fi_df.empty:
        top_fi = fi_df.iloc[0]
        total_fi = fi_df["Importance"].sum()
        pct = 100 * top_fi["Importance"] / total_fi if total_fi > 0 else 0
        lines.append(
            f"<b>5. Feature Importance 종합 해석</b><br>"
            f"모델 기반 Feature Importance에서 가장 중요한 변수는 <b>{pretty_time_text(top_fi['Feature'])}</b>이며, "
            f"중요도는 {top_fi['Importance']:.4f}, 전체 중요도 비중은 약 {pct:.1f}%입니다. "
            "Feature Importance는 모델이 어떤 변수를 많이 활용했는지를 보여주며, 방향성은 SHAP과 함께 해석하는 것이 적절합니다."
        )

    if week_importance is not None and not week_importance.empty:
        best_week = week_importance.sort_values("TotalMeanAbsSHAP", ascending=False).iloc[0]
        signed = best_week["AvgSignedSHAP"]
        signed_text = "긍정적" if signed > 0 else "부정적" if signed < 0 else "중립적"
        lines.append(
            f"<b>6. Temporal SHAP 종합 해석</b><br>"
            f"시간 구간별 SHAP 분석 결과, 가장 영향력이 큰 시점은 <b>{int(best_week['Week'])}주 전</b>입니다. "
            f"이 구간의 TotalMeanAbsSHAP는 {best_week['TotalMeanAbsSHAP']:.4f}, "
            f"AvgSignedSHAP는 {signed:.4f}입니다. "
            f"이는 해당 시기의 환경조건이 예측에 가장 강하게 반영되었고, 평균 방향성은 <b>{signed_text}</b>으로 해석됨을 의미합니다."
        )

    if heatmap_df is not None and not heatmap_df.empty:
        idx = np.unravel_index(np.argmax(heatmap_df.values), heatmap_df.shape)
        best_feat = heatmap_df.index[idx[0]]
        best_week_hm = heatmap_df.columns[idx[1]]
        best_val = heatmap_df.iloc[idx[0], idx[1]]
        lines.append(
            f"<b>7. Feature × Week Heatmap 종합 해석</b><br>"
            f"변수와 주차 조합 중 가장 영향력이 큰 조합은 "
            f"<b>{pretty_time_text(best_feat)} × {int(best_week_hm)}주</b>이며, "
            f"Mean(|SHAP|)={best_val:.4f}입니다. "
            "이는 특정 변수 자체뿐 아니라, 해당 변수가 어느 시점에 누적되었는지가 예측에 중요하다는 것을 보여줍니다."
        )

    if cf_result is not None:
        delta = cf_result["cf_pred"] - cf_result["base_pred"]
        direction = "증가" if delta > 0 else "감소"
        lines.append(
            f"<b>8. Counterfactual 환경제어 시뮬레이션 해석</b><br>"
            f"Counterfactual 분석 결과 예측값은 {cf_result['base_pred']:.4f}에서 "
            f"{cf_result['cf_pred']:.4f}로 {direction}했습니다. "
            f"변화량은 {delta:.4f}입니다. "
            "이는 일부 제어 가능한 환경변수를 조정할 경우 예측 결과 개선 가능성이 있음을 의미합니다."
        )

    if ice_feature is not None and pdp_summary is not None and ice_mean_slope is not None:
        start, end = pdp_summary["best_interval"]
        slope_dir = "증가" if ice_mean_slope > 0 else "감소" if ice_mean_slope < 0 else "변화가 작음"
        lines.append(
            f"<b>9. ICE + PDP 통합 그래프 해석</b><br>"
            f"선택 Feature는 <b>{pretty_time_text(ice_feature)}</b>입니다. "
            f"ICE 평균 기울기는 {ice_mean_slope:.4f} ± {ice_std_slope:.4f}로, "
            f"개별 샘플 기준 예측값은 전반적으로 <b>{slope_dir}</b>하는 경향을 보입니다. "
            f"PDP 기준 예측이 높은 최적 구간은 <b>{start:.3f} ~ {end:.3f}</b>이며, "
            f"이 구간 평균 예측값은 {pdp_summary['mean_val']:.4f}입니다."
        )

    if ale_summary is not None and bin_centers is not None and ale_vals is not None and len(bin_centers) > 0:
        max_idx = int(np.argmax(ale_vals))
        min_idx = int(np.argmin(ale_vals))

        pos_text = "없음"
        neg_text = "없음"

        if ale_summary.get("pos_intervals"):
            pos_text = format_interval_text(ale_summary.get("pos_intervals", []), limit=3)

        if ale_summary.get("neg_intervals"):
            neg_text = format_interval_text(ale_summary.get("neg_intervals", []), limit=3)

        lines.append(
            f"<b>10. Centered ALE 종합 해석</b><br>"
            f"Centered ALE 기준 가장 우호적인 중심값은 약 <b>{bin_centers[max_idx]:.3f}</b>이며 "
            f"ALE={ale_vals[max_idx]:.4f}입니다. "
            f"가장 불리한 중심값은 약 <b>{bin_centers[min_idx]:.3f}</b>이며 "
            f"ALE={ale_vals[min_idx]:.4f}입니다. "
            f"양의 ALE 구간은 {pos_text}, 음의 ALE 구간은 {neg_text}입니다. "
            "이는 선택 Feature의 임계구간 또는 관리 우선구간을 판단하는 데 활용할 수 있습니다."
        )

    lines.append(
        f"""
<div style="background:linear-gradient(135deg,#0f766e,#2563eb); color:white; padding:20px; border-radius:18px; box-shadow:0 10px 28px rgba(37,99,235,0.22); line-height:1.75;">
<h4 style="color:white; margin-top:0;">11. 최종 환경제어 의사결정 요약</h4>
<div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; margin-top:12px;">
  <div style="background:rgba(255,255,255,0.15); padding:14px; border-radius:14px;"><b>① 성능 기준</b><br>모델 성능이 우수한 주차 구간을 우선 확인합니다.</div>
  <div style="background:rgba(255,255,255,0.15); padding:14px; border-radius:14px;"><b>② 주요 변수</b><br>SHAP 상위 변수와 Feature Importance를 함께 검토합니다.</div>
  <div style="background:rgba(255,255,255,0.15); padding:14px; border-radius:14px;"><b>③ 시점 판단</b><br>Feature × Week 조합으로 언제의 환경이 중요한지 확인합니다.</div>
  <div style="background:rgba(255,255,255,0.15); padding:14px; border-radius:14px;"><b>④ 제어 구간</b><br>ICE+PDP 최적 구간과 Centered ALE 임계구간을 비교합니다.</div>
  <div style="background:rgba(255,255,255,0.15); padding:14px; border-radius:14px;"><b>⑤ 최종 전략</b><br>단일 평균값보다 영향 시점·방향성·임계구간을 통합해 제어합니다.</div>
</div>
</div>
"""
    )

    return "<br><br>".join(lines)


# -------------------------------------------------------------
# UI — A-DIMS 4탭 (HTML v0.04) + 상세 XAI
# -------------------------------------------------------------
def _render_advanced_xai_analysis(df, week_dfs, selected_week, growth_features, sensor_df=None, yield_df=None):
    """예측 탭 expander — 기존 XAI·모델 분석 파이프라인."""
    model_options = ["RandomForest", "GradientBoosting", "XGBoost", "LGBM", "GaussianNB"]
    mc1, mc2 = st.columns(2)
    with mc1:
        model_choice = st.selectbox("모델 선택", model_options, key="xai_model")
    with mc2:
        target_col = st.selectbox("예측 대상", ["수확수", "착과수"] + growth_features, key="xai_target")

    features = [col for col in df.columns if col not in ["조사일자", "수확수", "착과수"] + growth_features]
    X = df[features].copy().fillna(df[features].mean(numeric_only=True))
    y = df[target_col].copy()
    valid_mask = y.notna()
    X = X.loc[valid_mask].copy()
    y = y.loc[valid_mask].copy()
    if len(X) < 5:
        st.warning("XAI 분석을 위한 데이터가 부족합니다.")
        return

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = make_model(model_choice)
    model.fit(X_train, y_train)
    y_pred = safe_predict(model, X_test, features)
    metrics = compute_metrics(y_test, y_pred)

    st.markdown(f"**모델 평가** ({selected_week}주 · {target_col})")
    render_kpi_cards([
        ("MSE", f"{metrics['MSE']:.3f}", "#4E79A7"),
        ("MAE", f"{metrics['MAE']:.3f}", "#4F9D5B"),
        ("R²", f"{metrics['R2']:.3f}", "#D99220"),
    ])

    _run_legacy_xai_body(
        df=df, week_dfs=week_dfs, selected_week=selected_week,
        growth_features=growth_features, model_choice=model_choice,
        target_col=target_col, features=features, model=model,
        X_train=X_train, X_test=X_test, metrics=metrics,
    )


def _run_legacy_xai_body(df, week_dfs, selected_week, growth_features, model_choice,
                         target_col, features, model, X_train, X_test, metrics):
    """기존 XAI 분석 본문 (SHAP · Counterfactual · ICE · ALE · 리포트)."""
    crop_name = st.session_state.get("dims_crop", "토마토")
    _ = crop_name  # legacy compat

    # 1~7주 모델 성능 비교
    # -------------------------------------------------------------
    render_section_header("1~7주 모델 성능 비교", "주차별 예측 성능 변화 추이", "📈", accent="teal")

    weekly_metrics = []

    try:

        for wk in range(1, 8):

            wk_df = week_dfs[wk].copy()

            wk_features = [
                c for c in wk_df.columns
                if c not in ["조사일자", "수확수", "착과수"] + growth_features
            ]

            X_wk = wk_df[wk_features].copy()
            X_wk = X_wk.fillna(X_wk.mean(numeric_only=True))

            y_wk = wk_df[target_col].copy()

            valid_mask_wk = y_wk.notna()

            X_wk = X_wk.loc[valid_mask_wk].copy()
            y_wk = y_wk.loc[valid_mask_wk].copy()

            if len(X_wk) < 5:
                continue

            X_train_wk, X_test_wk, y_train_wk, y_test_wk = train_test_split(
                X_wk,
                y_wk,
                test_size=0.2,
                random_state=42
            )

            wk_model = make_model(model_choice)

            wk_model.fit(X_train_wk, y_train_wk)

            preds_wk = safe_predict(
                wk_model,
                X_test_wk,
                wk_features
            )

            mse_wk = mean_squared_error(y_test_wk, preds_wk)
            mae_wk = mean_absolute_error(y_test_wk, preds_wk)
            r2_wk = r2_score(y_test_wk, preds_wk)

            weekly_metrics.append({
                "Week": wk,
                "MSE": mse_wk,
                "MAE": mae_wk,
                "R2": r2_wk
            })

        if len(weekly_metrics) > 0:

            weekly_metrics_df = pd.DataFrame(weekly_metrics)

            # -------------------------------------------------
            # MSE / MAE / R² 그래프 가로 배치
            # -------------------------------------------------
            st.markdown(f"### 📈 주차별 모델 성능 변화 (예측대상: {target_col})")

            col_mse, col_mae, col_r2 = st.columns(3)

            with col_mse:
                display_plotly(build_weekly_metric_chart(weekly_metrics_df, "MSE", "MSE (평균제곱오차)", "#2563eb"))

            with col_mae:
                display_plotly(build_weekly_metric_chart(weekly_metrics_df, "MAE", "MAE (평균절대오차)", "#0d9488"))

            with col_r2:
                display_plotly(build_weekly_metric_chart(weekly_metrics_df, "R2", "R² (결정계수)", "#d97706"))

            st.markdown("### 📋 1~7주 모델 평가지표 표")
            st.dataframe(
                weekly_metrics_df.round(4),
                use_container_width=True
            )

            # -------------------------------------------------
            # 성능 자동 해석
            # -------------------------------------------------
            best_r2_row = weekly_metrics_df.sort_values(
                "R2",
                ascending=False
            ).iloc[0]

            best_mse_row = weekly_metrics_df.sort_values(
                "MSE",
                ascending=True
            ).iloc[0]

            best_mae_row = weekly_metrics_df.sort_values(
                "MAE",
                ascending=True
            ).iloc[0]

            st.markdown('<div class="pretty-box"><h3>🧠 주차별 성능 자동 해석</h3></div>', unsafe_allow_html=True)

            col_metric_left, col_metric_right = st.columns(2)

            with col_metric_left:

                st.markdown(
                    f"""
    <div style="background:linear-gradient(135deg,#ffffff,#eef5ff); box-shadow:0 6px 20px rgba(0,0,0,0.05);
    padding:12px;
    border-radius:10px;
    line-height:1.45;
    font-size:15px">

    <b>최적 R² 구간</b><br><br>

    가장 높은 R² 성능은 <b>{int(best_r2_row['Week'])}주</b>에서 나타났으며,
    R² 값은 <b>{best_r2_row['R2']:.4f}</b>입니다.<br><br>

    이는 해당 기간의 환경 데이터를 사용할 때
    예측 대상({target_col})을 가장 잘 설명할 수 있었음을 의미합니다.<br><br>

    <b>최소 MSE 구간</b><br><br>

    가장 낮은 MSE는 <b>{int(best_mse_row['Week'])}주</b>에서 나타났으며,
    MSE 값은 <b>{best_mse_row['MSE']:.4f}</b>입니다.<br><br>

    즉, 해당 기간의 환경 누적 정보가
    큰 예측 오차를 가장 작게 만든 구간으로 해석할 수 있습니다.<br><br>

    <b>최소 MAE 구간</b><br><br>

    가장 낮은 MAE는 <b>{int(best_mae_row['Week'])}주</b>에서 나타났으며,
    MAE 값은 <b>{best_mae_row['MAE']:.4f}</b>입니다.<br><br>

    이는 실제값과 예측값의 평균적인 차이가 가장 작았던 구간으로,
    현장 해석 관점에서 가장 직관적인 오차 최소 구간입니다.<br><br>

    일반적으로 R²가 높고 MSE/MAE가 낮을수록
    모델 성능이 우수한 것으로 해석합니다.

    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col_metric_right:

                st.markdown(
                    """
    <div style="background:linear-gradient(135deg,#ffffff,#eef5ff); box-shadow:0 6px 20px rgba(0,0,0,0.05);
    padding:12px;
    border-radius:10px;
    line-height:1.45;
    font-size:15px">

    <b>R² 특징 설명</b><br><br>

    R²(결정계수)는 모델이 실제 데이터 변동성을 얼마나 설명할 수 있는지를 나타냅니다.<br>
    1에 가까울수록 설명력이 높으며, 0에 가까우면 평균 예측 수준과 유사한 상태를 의미합니다.<br>
    즉, R²가 높을수록 환경데이터와 생육·수확 데이터 간 관계를 잘 학습했다고 볼 수 있습니다.<br><br>

    <b>MSE 특징 설명</b><br><br>

    MSE(Mean Squared Error)는 실제값과 예측값 차이의 제곱 평균입니다.<br>
    큰 오차에 더 민감하게 반응하므로, 이상치나 큰 예측 실패가 존재할 경우 값이 크게 증가합니다.<br>
    따라서 MSE가 낮다는 것은 모델이 큰 오차 없이 안정적으로 예측했다는 의미입니다.<br><br>

    <b>MAE 특징 설명</b><br><br>

    MAE(Mean Absolute Error)는 실제값과 예측값 차이의 절대값 평균입니다.<br>
    실제 평균적으로 얼마나 차이가 나는지를 직관적으로 보여주는 지표입니다.<br>
    단위가 원래 목표변수와 동일하기 때문에 농업 현장에서는 해석이 비교적 쉬운 장점이 있습니다.

    </div>
                    """,
                    unsafe_allow_html=True
                )

    except Exception as e:
        st.error(f"1~7주 모델 성능 비교 오류: {e}")


    # -------------------------------------------------------------
    # Time-Series Cross Validation (수정 버전)
    # -------------------------------------------------------------
    render_section_header("Time-Series Cross Validation", "시계열 분할 기반 모델 안정성 검증", "🧪", accent="amber")

    try:
        # 시간 순서 정렬 (매우 중요)
        df_cv = df.sort_values("조사일자").reset_index(drop=True)

        features = [col for col in df_cv.columns if col not in ["조사일자", "수확수", "착과수"] + growth_features]

        X_cv = df_cv[features].copy().fillna(df_cv[features].mean(numeric_only=True))
        y_cv = df_cv[target_col].copy()

        valid_mask = y_cv.notna()
        X_cv = X_cv.loc[valid_mask].reset_index(drop=True)
        y_cv = y_cv.loc[valid_mask].reset_index(drop=True)

        # 최소 데이터 체크
        if len(X_cv) < 6:
            st.warning("CV 수행을 위한 데이터가 부족합니다.")
        else:
            mse_list, mae_list, r2_list = [], [], []

            # 🔥 핵심 수정: test 데이터 2개 확보
            for i in range(3, len(X_cv) - 1):

                X_train_cv = X_cv.iloc[:i]
                y_train_cv = y_cv.iloc[:i]

                X_test_cv = X_cv.iloc[i:i + 2]
                y_test_cv = y_cv.iloc[i:i + 2]

                model_cv = make_model(model_choice)
                model_cv.fit(X_train_cv, y_train_cv)

                preds_cv = safe_predict(model_cv, X_test_cv, features)

                mse_list.append(mean_squared_error(y_test_cv, preds_cv))
                mae_list.append(mean_absolute_error(y_test_cv, preds_cv))

                # 🔥 R² 안전 계산
                if len(y_test_cv) > 1:
                    r2_list.append(r2_score(y_test_cv, preds_cv))
                else:
                    r2_list.append(np.nan)

            # 🔥 NaN 제거 후 평균 계산
            cv_mse = float(np.mean(mse_list))
            cv_mae = float(np.mean(mae_list))
            cv_r2 = float(np.nanmean(r2_list))

            st.markdown("### 🧪 Time-Series CV 평균 성능")
            render_kpi_cards([
                ("MSE", f"{cv_mse:.3f}", "#2563eb"),
                ("MAE", f"{cv_mae:.3f}", "#0d9488"),
                ("R²", f"{cv_r2:.3f}", "#d97706"),
            ])

            st.markdown(
                f"""
    <div style="background:linear-gradient(135deg,#ffffff,#eef5ff);
            box-shadow:0 6px 20px rgba(0,0,0,0.06);
            padding:16px;
            border-radius:14px;
            line-height:1.8;
            font-size:15px;">
    <b>Time-Series Cross Validation 해석</b><br><br>
    시간 순서를 유지한 상태에서 과거 데이터를 학습하고 이후 시점 데이터를 평가한 결과입니다.<br>
    평균 MSE는 <b>{cv_mse:.3f}</b>, 평균 MAE는 <b>{cv_mae:.3f}</b>, 평균 R²는 <b>{cv_r2:.3f}</b>입니다.<br>
    이는 무작위 분할보다 실제 생육·수확 예측 흐름에 가까운 검증 방식으로, 시계열 기반 예측 안정성을 확인하는 데 활용됩니다.
    </div>
                """,
                unsafe_allow_html=True
            )

    except Exception as e:
        st.error(f"CV 실행 오류: {e}")

    render_section_header(
        "XAI 자동 리포트",
        "SHAP · Feature Importance · ICE · PDP · ALE 통합 분석",
        "🧠",
        accent="purple",
    )

    shap_values = None
    shap_df = None
    fi_df = None
    temporal_df = None
    week_importance = None
    heatmap_df = None
    weekly_metrics_df = None
    cf_result = None
    ice_mean_slope = None
    ice_std_slope = None
    pdp_summary = None
    ale_summary = None
    bin_centers = None
    ale_vals = None

    top_col1, top_col2 = st.columns([1, 1])

    with top_col1:
        st.markdown(f"### 🔍 SHAP Summary (예측 대상: {target_col})")
        if model_choice == "GaussianNB":
            st.info("GaussianNB 모델은 SHAP 사용이 제한적입니다.")
        else:
            try:
                explainer = shap.Explainer(model, X_train)
                shap_values = explainer(X_test, check_additivity=False)

                fig_shap = plt.figure(figsize=(6, 4))
                shap.summary_plot(shap_values.values, X_test, show=False)
                display_matplotlib(fig_shap)
                plt.close(fig_shap)

                shap_df = summarize_shap_results(shap_values, features)
                st.dataframe(shap_df[["Feature", "Mean(|SHAP|)", "Mean(SHAP)"]].head(12).round(6), use_container_width=True)
                st.markdown("**SHAP Summary 최종 결과**")
                st.info(explain_shap_summary(shap_df))
                st.markdown("**SHAP Summary 상세 설명**")
                render_insight(explain_shap_summary_detail(shap_df, target_col, model_choice), variant="purple")

            except Exception as e:
                st.error(f"SHAP 계산/시각화 오류: {e}")

    with top_col2:
        st.markdown(f"### 📊 Feature Importance (Model-based) (예측대상: {target_col})")
        try:
            fi_df = feature_importance_table(model, features)
            fig_fi, ax_fi = plt.subplots(figsize=(6, 4))
            ax_fi.barh(fi_df["Feature"], fi_df["Importance"])
            ax_fi.invert_yaxis()
            ax_fi.set_title("Feature Importance")
            display_matplotlib(fig_fi)
            plt.close(fig_fi)

            st.markdown("**Feature Importance 요약**")
            top = fi_df.head(5)
            tot = fi_df["Importance"].sum()
            for _, r in top.iterrows():
                pct = 100.0 * r["Importance"] / tot if tot > 0 else 0.0
                st.write(f"• {r['Feature']}: {pct:.1f}%")
            st.info(explain_feature_importance(fi_df))
            st.markdown("**Feature Importance 상세 설명**")
            st.markdown(f"""<div style="background:linear-gradient(135deg,#ffffff,#eef5ff); box-shadow:0 6px 20px rgba(0,0,0,0.05);padding:14px;border-radius:10px;line-height:1.8;font-size:16px">{explain_feature_importance_detail(fi_df, target_col, model_choice)}</div>""", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Feature Importance 처리 오류: {e}")

    # Temporal SHAP + Heatmap
    st.subheader("⏱ Temporal SHAP")
    if shap_values is not None:
        try:
            # 1~7주 전체 feature로 재학습하여 주차 설명력 계산
            merged_df = week_dfs[1][["조사일자", "수확수", "착과수"] + growth_features].copy()
            for week in range(1, 8):
                wk_df = week_dfs[week].copy()
                add_cols = [c for c in wk_df.columns if c not in ["조사일자", "수확수", "착과수"] + growth_features]
                merged_df = merged_df.merge(wk_df[["조사일자"] + add_cols], on="조사일자", how="left")

            temporal_features = [c for c in merged_df.columns if c not in ["조사일자", "수확수", "착과수"] + growth_features]
            mX = merged_df[temporal_features].copy().fillna(merged_df[temporal_features].mean(numeric_only=True))
            my = merged_df[target_col].copy()
            valid_mask2 = my.notna()
            mX = mX.loc[valid_mask2].copy()
            my = my.loc[valid_mask2].copy()

            mX_train, mX_test, my_train, my_test = train_test_split(mX, my, test_size=0.2, random_state=42)
            temporal_model = make_model(model_choice)
            temporal_model.fit(mX_train, my_train)
            temporal_explainer = shap.Explainer(temporal_model, mX_train)
            temporal_shap_values = temporal_explainer(mX_test, check_additivity=False)

            temporal_df, week_importance, heatmap_df = build_temporal_shap_tables(temporal_shap_values, temporal_features)

            if week_importance is not None and not week_importance.empty:
                fig_ts = fig_temporal_shap_bar(week_importance)
                display_matplotlib(fig_ts)
                plt.close(fig_ts)

                st.dataframe(week_importance.round(5), use_container_width=True)
                st.markdown("**Temporal SHAP 최종 결과**")
                st.info(explain_temporal_shap(week_importance, target_col))

                st.markdown("**Temporal SHAP 지표 상세 설명**")

                st.markdown(
                    """
    <div style="background:linear-gradient(135deg,#ffffff,#eef5ff); box-shadow:0 6px 20px rgba(0,0,0,0.05);
    padding:14px;
    border-radius:10px;
    line-height:1.8;
    font-size:16px">

    <b>TotalMeanAbsSHAP 설명</b><br><br>

    TotalMeanAbsSHAP는 해당 주차의 모든 변수들의 평균 절대 SHAP 값을 합산한 값입니다.<br>
    즉, 특정 주차의 환경 정보가 전체 예측 결과에 얼마나 강하게 영향을 주었는지를 의미합니다.<br>
    값이 클수록 해당 시기의 환경조건이 현재 생육 또는 수확 예측에 매우 중요하게 작용했다는 뜻입니다.<br><br>

    <b>AvgSignedSHAP 설명</b><br><br>

    AvgSignedSHAP는 해당 주차 변수들의 SHAP 방향성 평균입니다.<br>
    양수이면 평균적으로 예측값을 증가시키는 방향으로 작용했고,<br>
    음수이면 평균적으로 예측값을 감소시키는 방향으로 작용했음을 의미합니다.<br>
    즉, 해당 시기의 환경이 생육/수확에 긍정적이었는지 부정적이었는지를 해석할 수 있습니다.

    </div>
                    """,
                    unsafe_allow_html=True
                )


            else:
                st.warning("Temporal SHAP를 계산할 수 없습니다. 주차 feature가 충분하지 않습니다.")

            st.subheader("🔥 Feature × Week Heatmap")
            if heatmap_df is not None and not heatmap_df.empty:
                fig_hm = fig_feature_week_heatmap(heatmap_df, target_col)
                display_matplotlib(fig_hm)
                plt.close(fig_hm)

                heatmap_table = temporal_df[["Feature", "Mean(|SHAP|)"]].sort_values("Mean(|SHAP|)", ascending=False)
                st.dataframe(heatmap_table.round(5), use_container_width=True)
                st.markdown("**Feature × Week Heatmap 최종 결과**")

                st.markdown(
                    f"""<div style="background:linear-gradient(135deg,#ffffff,#eef5ff); box-shadow:0 6px 20px rgba(0,0,0,0.05);
                    padding:14px;
                    border-radius:10px;
                    line-height:1.8;
                    font-size:16px">{explain_heatmap(heatmap_df, target_col)}</div>""",
                    unsafe_allow_html=True
                )
                st.markdown("**Feature × Week Heatmap 상세 설명**")
                st.markdown(f"""<div style="background:linear-gradient(135deg,#ffffff,#eef5ff); box-shadow:0 6px 20px rgba(0,0,0,0.05);padding:14px;border-radius:10px;line-height:1.8;font-size:16px">{explain_heatmap_detail(heatmap_df, temporal_df, target_col)}</div>""", unsafe_allow_html=True)
            else:
                st.warning("Heatmap을 계산할 수 없습니다.")

        except Exception as e:
            st.warning(f"Temporal SHAP / Heatmap 오류: {e}")

    # Counterfactual
    st.subheader("🔧 Counterfactual (환경 제어 시뮬레이션)")

    try:
        if len(X_test) == 0:
            st.warning("Counterfactual을 계산할 테스트 샘플이 없습니다.")
        else:
            x0 = X_test.iloc[0].copy()

            cf_result = generate_counterfactual(
                model=model,
                x_row=x0,
                X_ref=X_train,
                feature_names=features,
                target_delta=1.0,
                n_iter=2000,
                random_state=42,
                top_n=5,
            )

            if cf_result is None:
                st.warning("Counterfactual 결과를 생성하지 못했습니다.")
            else:
                before_pred = float(cf_result.get("base_pred", np.nan))
                after_pred = float(cf_result.get("cf_pred", np.nan))
                delta_pred = after_pred - before_pred

                priority_df = cf_result.get("priority_df", pd.DataFrame()).copy()
                selected_df = cf_result.get("selected_df", pd.DataFrame()).copy()
                diff_df = cf_result.get("diff_df", pd.DataFrame()).copy()

                if not selected_df.empty:
                    top_feature = str(selected_df.iloc[0].get("Feature", "없음"))
                    top_group = str(selected_df.iloc[0].get("ControlGroup", "없음"))
                elif not priority_df.empty:
                    top_feature = str(priority_df.iloc[0].get("Feature", "없음"))
                    top_group = str(priority_df.iloc[0].get("ControlGroup", "없음"))
                else:
                    top_feature = "없음"
                    top_group = "없음"

                render_alert_card(
                    "단위가 큰 누적일사량이 반복적으로 선택되는 문제를 줄이기 위해 "
                    "표준화 변화량(StdChange), 예측 개선량(PredDelta), PriorityScore를 함께 사용했습니다. "
                    "또한 동일 제어군만 반복 추천되지 않도록 제어군별 대표 후보를 우선 선발합니다.",
                    variant="info",
                )

                render_kpi_cards([
                    ("현재 예측값", f"{before_pred:.3f}", "#2563eb"),
                    ("Counterfactual 예측값", f"{after_pred:.3f}", "#059669"),
                    ("변화량", f"{delta_pred:+.3f}", "#d97706"),
                    ("1순위 제어 후보", top_group, "#7c3aed"),
                ])

                st.markdown("### 📋 Top-N 환경제어 우선순위")

                if not priority_df.empty:
                    priority_cols = [
                        "Feature", "ControlGroup", "Original", "Counterfactual",
                        "Change", "StdChange", "PredDelta", "PriorityScore",
                        "Direction", "Recommendation"
                    ]
                    priority_cols = [c for c in priority_cols if c in priority_df.columns]

                    priority_view = (
                        priority_df[priority_cols]
                        .head(10)
                        .copy()
                    )

                    numeric_cols = priority_view.select_dtypes(include=[np.number]).columns
                    priority_view[numeric_cols] = priority_view[numeric_cols].round(4)

                    st.dataframe(
                        priority_view,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.warning("표시할 Counterfactual 우선순위 후보가 없습니다.")

                st.markdown("### 🧭 환경제어 추천 카드")

                card_col1, card_col2 = st.columns(2)

                with card_col1:
                    render_alert_card(
                        f"<b>1순위 제어군:</b> {top_group}<br><br>"
                        f"<b>대표 변수:</b> {top_feature}<br><br>"
                        f"이 후보는 현재 모델이 {target_col} 예측값을 높일 가능성이 있다고 판단한 "
                        "우선 검토 대상입니다.",
                        variant="success",
                    )

                with card_col2:
                    if not selected_df.empty and "Recommendation" in selected_df.columns:
                        first_rec = str(selected_df.iloc[0].get("Recommendation", "현장 조건과 함께 검토하세요."))
                    elif not priority_df.empty and "Recommendation" in priority_df.columns:
                        first_rec = str(priority_df.iloc[0].get("Recommendation", "현장 조건과 함께 검토하세요."))
                    else:
                        first_rec = "현장 조건과 생육단계를 함께 검토하여 제어 방향을 결정하세요."

                    render_alert_card(
                        f"<b>권장 제어 방향</b><br><br>{first_rec}<br><br>"
                        "Counterfactual은 실제 정답 제어값이 아니라, 학습 데이터 범위에서 계산된 "
                        "가설적 제어 후보입니다.",
                        variant="warning",
                    )

                st.markdown("### 🔎 선택된 복합 Counterfactual 변화량")

                if not diff_df.empty:
                    diff_cols = [
                        "Feature", "ControlGroup", "Original", "Counterfactual",
                        "Change", "StdChange", "PredDelta", "PriorityScore",
                        "Recommendation"
                    ]
                    diff_cols = [c for c in diff_cols if c in diff_df.columns]

                    diff_view = diff_df[diff_cols].head(10).copy()
                    numeric_cols = diff_view.select_dtypes(include=[np.number]).columns
                    diff_view[numeric_cols] = diff_view[numeric_cols].round(4)

                    st.dataframe(
                        diff_view,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.warning("표시할 Counterfactual 변화량 데이터가 없습니다.")

                st.markdown("### 📌 지표 해석")

                interpret_col1, interpret_col2 = st.columns(2)

                with interpret_col1:
                    render_alert_card(
                        "<b>Change</b>: 현재값과 Counterfactual 값의 원 단위 차이입니다.<br><br>"
                        "<b>StdChange</b>: 표준편차 기준으로 환산한 변화량입니다. "
                        "온도·습도·CO₂·일사량처럼 단위가 다른 변수를 공정하게 비교하는 데 사용합니다.",
                        variant="info",
                    )

                with interpret_col2:
                    render_alert_card(
                        "<b>PredDelta</b>: 해당 변수 조정 시 예측값이 얼마나 개선되는지 나타냅니다.<br><br>"
                        "<b>PriorityScore</b>: PredDelta와 표준화 효율을 함께 반영한 환경제어 우선순위 점수입니다.",
                        variant="info",
                    )

                if not priority_df.empty:
                    st.markdown("### ✅ 환경제어 의사결정 요약")

                    top_rows = priority_df.head(5).copy()
                    decision_cols = st.columns(5)
                    for idx, (_, r) in enumerate(top_rows.iterrows(), start=1):
                        group = r.get("ControlGroup", "기타")
                        feature = pretty_time_text(r.get("Feature", ""))
                        direction = r.get("Direction", "")
                        pred_delta = r.get("PredDelta", np.nan)
                        rec = r.get("Recommendation", "")

                        with decision_cols[(idx - 1) % 5]:
                            st.markdown(
                                f"""
    <div style="background:linear-gradient(135deg,#ffffff,#eef5ff); border:1px solid #dbeafe; box-shadow:0 6px 16px rgba(15,23,42,0.08); border-radius:16px; padding:14px; min-height:190px; line-height:1.55; word-break:keep-all; overflow-wrap:break-word;">
    <div style="font-size:13px; color:#64748b; font-weight:700;">{idx}순위 · {group}</div>
    <div style="font-size:15px; font-weight:800; color:#183b56; margin-top:6px;">{feature}</div>
    <div style="margin-top:8px; font-size:14px;">방향: <b>{direction}</b></div>
    <div style="font-size:14px;">예측 개선량: <b>{pred_delta:.3f}</b></div>
    <div style="margin-top:8px; font-size:13px; color:#334155;">{rec}</div>
    </div>
    """,
                                unsafe_allow_html=True
                            )

                    st.markdown(
                        """
    <div style="background:linear-gradient(135deg,#0f766e,#2563eb); color:white; padding:16px; border-radius:16px; box-shadow:0 8px 22px rgba(37,99,235,0.22); line-height:1.7; margin-top:12px;">
    <b style="color:white;">제어 전략 해석</b><br>
    누적일사량이 계속 1순위로 보이면 모델이 광환경을 강하게 학습했을 가능성이 있습니다. 개선된 방식에서는 제어군별 대표 후보를 함께 보여주므로, 온도·습도·CO₂·광환경 후보를 조합해 현실적인 제어전략을 수립하는 것이 좋습니다.
    </div>
    """,
                        unsafe_allow_html=True
                    )

    except Exception as e:
        st.error(f"Counterfactual 오류: {e}")

    # SHAP 상세 해석
    st.markdown("### 🔎 SHAP 샘플별 상세 해석")
    st.markdown(f"""<div style="background:linear-gradient(135deg,#ffffff,#eef5ff); box-shadow:0 6px 20px rgba(0,0,0,0.05);padding:14px;border-radius:10px;line-height:1.8;font-size:16px">{explain_shap_sample_intro()}</div>""", unsafe_allow_html=True)
    sample_idx = st.number_input("샘플 인덱스 (X_test 기준)", min_value=0, max_value=max(0, len(X_test) - 1), value=0, step=1)
    st.markdown(f"""<div style="background:linear-gradient(135deg,#ffffff,#eef5ff); box-shadow:0 6px 20px rgba(0,0,0,0.05);padding:14px;border-radius:10px;line-height:1.8;font-size:16px">{explain_sample_index(sample_idx, X_test)}</div>""", unsafe_allow_html=True)
    if shap_values is not None and model_choice != "GaussianNB":
        try:
            shp_s = shap_values[sample_idx].values
            shap_sample_df = pd.DataFrame({"Feature": features, "SHAP": shp_s}).sort_values(
                by="SHAP", key=lambda s: np.abs(s), ascending=False
            )
            st.dataframe(shap_sample_df.head(20).round(4), use_container_width=True)
            st.markdown("**선택 샘플 SHAP 결과 설명**")
            st.markdown(f"""<div style="background:linear-gradient(135deg,#ffffff,#eef5ff); box-shadow:0 6px 20px rgba(0,0,0,0.05);padding:14px;border-radius:10px;line-height:1.8;font-size:16px">{explain_shap_sample_result(shap_sample_df, target_col)}</div>""", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"SHAP 샘플 분석 오류: {e}")

    # ICE / PDP / ALE
    st.subheader("ICE + PDP 통합 / Centered ALE — 그래프 + 최적 구간 리포트")
    ice_feature = st.selectbox("분석할 Feature 선택 (ICE/PDP/ALE)", features, key="xai_feature")
    st.info(
        f"현재 선택한 분석 Feature는 **{ice_feature}**입니다. "
        "아래 ICE+PDP와 Centered ALE 그래프는 이 변수 하나의 변화가 예측 결과에 어떤 영향을 주는지 해석합니다."
    )
    n_samples = st.slider("ICE 샘플 수", 1, max(1, len(X_test)), value=min(50, len(X_test)), key="ice_samples")
    ale_bins = st.slider("ALE bins 수", 4, 30, 10)

    def compute_centered_ale(model, X, feature, bins=10):
        x = X[feature].values
        mask = ~np.isnan(x)
        x = x[mask]

        X_valid = X.loc[mask].reset_index(drop=True)

        percentiles = np.linspace(0, 100, bins + 1)
        cutpoints = np.unique(np.percentile(x, percentiles))

        if len(cutpoints) < 2:
            return np.array([np.mean(x)]), np.array([0.0])

        local_effects = []
        bin_centers = []

        for i in range(len(cutpoints) - 1):

            lo = cutpoints[i]
            hi = cutpoints[i + 1]

            in_bin = (
                (X_valid[feature] >= lo) &
                (X_valid[feature] <= hi)
            )

            if in_bin.sum() == 0:
                local_effects.append(0.0)
                bin_centers.append((lo + hi) / 2.0)
                continue

            X_lo = X_valid.copy()
            X_hi = X_valid.copy()

            X_lo.loc[in_bin, feature] = lo
            X_hi.loc[in_bin, feature] = hi

            preds_hi = safe_predict(model, X_hi, features)
            preds_lo = safe_predict(model, X_lo, features)

            diff = preds_hi - preds_lo

            local_effect = (
                diff[in_bin.values].mean()
                if in_bin.sum() > 0 else 0.0
            )

            local_effects.append(local_effect)
            bin_centers.append((lo + hi) / 2.0)

        ale = np.cumsum(local_effects)

        # --------------------------------
        # Centered ALE
        # --------------------------------
        ale = ale - np.mean(ale)

        return np.array(bin_centers), ale

    def summarize_ale_intervals(bin_centers, ale_vals):
        bc = np.array(bin_centers)
        av = np.array(ale_vals)
        deriv = np.gradient(av, bc)
        thr = 1.5 * (np.std(deriv) + 1e-9)
        steep_idx = np.where(np.abs(deriv) > thr)[0]

        def contiguous_ranges(mask):
            ranges = []
            i = 0
            while i < len(mask):
                if mask[i]:
                    j = i
                    while j < len(mask) and mask[j]:
                        j += 1
                    ranges.append((i, j - 1))
                    i = j
                else:
                    i += 1
            return ranges

        pos_ranges = contiguous_ranges(av > 0)
        neg_ranges = contiguous_ranges(av < 0)
        pos_intervals = [(float(bc[s]), float(bc[t]), float(np.mean(av[s:t + 1]))) for s, t in pos_ranges]
        neg_intervals = [(float(bc[s]), float(bc[t]), float(np.mean(av[s:t + 1]))) for s, t in neg_ranges]
        steep_points = [(int(i), float(bc[i]), float(deriv[i])) for i in steep_idx]
        return {"pos_intervals": pos_intervals, "neg_intervals": neg_intervals, "steep_points": steep_points}

    def find_top_contiguous_interval(x, y, top_frac=0.9, min_width=1):
        thresh = np.quantile(y, top_frac)
        mask = y >= thresh
        segments = []
        i = 0
        while i < len(mask):
            if mask[i]:
                j = i
                while j < len(mask) and mask[j]:
                    j += 1
                if (j - i) >= min_width:
                    segments.append((i, j - 1))
                i = j
            else:
                i += 1
        if not segments:
            idx = int(np.argmax(y))
            left = max(0, idx - 1)
            right = min(len(x) - 1, idx + 1)
            return x[left], x[right], float(np.mean(y[left:right + 1])), float(np.max(y[left:right + 1]))
        best = None
        best_score = -1e9
        for s, t in segments:
            score = float(np.mean(y[s:t + 1]))
            if score > best_score:
                best_score = score
                best = (s, t)
        s, t = best
        return x[s], x[t], float(np.mean(y[s:t + 1])), float(np.max(y[s:t + 1]))

    def summarize_pdp(model, X, feature, grid_resolution=50):
        col = X[feature]
        x = np.linspace(col.min(), col.max(), grid_resolution)
        y = []
        Xbase = X.copy()
        for val in x:
            Xtmp = Xbase.copy()
            Xtmp[feature] = val
            preds = safe_predict(model, Xtmp, features)
            y.append(np.mean(preds))
        x = np.array(x)
        y = np.array(y)
        start, end, mean_y, max_y = find_top_contiguous_interval(x, y, top_frac=0.9)
        return x, y, {"best_interval": (start, end), "mean_val": float(mean_y), "max_val": float(max_y)}

    def summarize_ice_linear_slope(model, X, feature, n_samples=50):
        Xs = X.sample(n=min(n_samples, len(X)), random_state=42)
        xs = np.linspace(X[feature].min(), X[feature].max(), 30)
        slopes = []
        for _, row in Xs.iterrows():
            Xtmp = pd.DataFrame(np.tile(row.values, (len(xs), 1)), columns=X.columns)
            Xtmp[feature] = xs
            preds = safe_predict(model, Xtmp, features)
            lr = LinearRegression()
            lr.fit(xs.reshape(-1, 1), preds)
            slopes.append(lr.coef_[0])
        slopes = np.array(slopes)
        return float(np.mean(slopes)), float(np.std(slopes)), len(slopes)

    col_ice_pdp, col_ale = st.columns(2)

    with col_ice_pdp:

        st.markdown("**ICE + PDP 통합 그래프 & 최적 구간**")

        try:

            Xs = X_test.sample(
                n=min(n_samples, len(X_test)),
                random_state=42
            )

            xs = np.linspace(
                X_test[ice_feature].min(),
                X_test[ice_feature].max(),
                50
            )

            ice_curves_y = []
            for _, row in Xs.iterrows():
                Xtmp = pd.DataFrame(
                    np.tile(row.values, (len(xs), 1)),
                    columns=X_test.columns
                )
                Xtmp[ice_feature] = xs
                ice_curves_y.append(safe_predict(model, Xtmp, features))

            xvals, yvals, pdp_summary = summarize_pdp(
                model,
                X_test,
                ice_feature,
                grid_resolution=50
            )

            fig_mix = fig_ice_pdp(
                xs,
                ice_curves_y,
                xvals,
                yvals,
                pretty_time_text(ice_feature),
                best_interval=pdp_summary.get("best_interval"),
            )
            display_matplotlib(fig_mix)
            plt.close(fig_mix)

            # 최적 구간
            start, end = pdp_summary["best_interval"]

            st.write(
                f"예측대상({target_col})의 최적(예측이 큰) 구간: "
                f"{start:.3f} ~ {end:.3f}"
            )

            st.write(
                f"구간 평균 예측값: "
                f"{pdp_summary['mean_val']:.3f}"
            )

            st.write(
                f"구간 최대값: "
                f"{pdp_summary['max_val']:.3f}"
            )

            ice_mean_slope, ice_std_slope, cnt = summarize_ice_linear_slope(
                model,
                X_test,
                ice_feature,
                n_samples=min(n_samples, len(X_test))
            )

            st.write(
                f"ICE 평균 기울기: "
                f"{ice_mean_slope:.4f} ± {ice_std_slope:.4f}"
            )

            ice_desc, pdp_desc, combined_desc = explain_ice_pdp_result(
                ice_feature,
                ice_mean_slope,
                ice_std_slope,
                pdp_summary,
                target_col
            )

            st.markdown("**ICE 그래프 결과 설명**")
            st.markdown(ice_desc, unsafe_allow_html=True)

            st.markdown("**PDP 그래프 결과 설명**")
            st.markdown(pdp_desc, unsafe_allow_html=True)

            st.markdown("**ICE + PDP 전체 그래프 결과 설명**")
            st.markdown(combined_desc, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"ICE + PDP 처리 오류: {e}")



    with col_ale:
        st.markdown("**Centered ALE & 임계구간 탐지**")
        try:
            bin_centers, ale_vals = compute_centered_ale(model, X_test.reset_index(drop=True), ice_feature, bins=ale_bins)
            ale_summary = summarize_ale_intervals(bin_centers, ale_vals)
            fig_ale = fig_centered_ale(
                bin_centers,
                ale_vals,
                pretty_time_text(ice_feature),
                pos_intervals=ale_summary.get("pos_intervals"),
                neg_intervals=ale_summary.get("neg_intervals"),
            )
            display_matplotlib(fig_ale)
            plt.close(fig_ale)
            if ale_summary["pos_intervals"]:
                st.write("모델이 우호적으로 보는 구간(양의 ALE):")
                for a, b, mv in ale_summary["pos_intervals"]:
                    st.write(f"• {a:.2f} ~ {b:.2f} (평균 ALE: {mv:.3f})")
            if ale_summary["neg_intervals"]:
                st.write("모델이 불리하게 보는 구간(음의 ALE):")
                for a, b, mv in ale_summary["neg_intervals"]:
                    st.write(f"• {a:.2f} ~ {b:.2f} (평균 ALE: {mv:.3f})")

            st.markdown("**Centered ALE 그래프 결과 설명**")
            st.markdown(
                f"""<div style="background:linear-gradient(135deg,#ffffff,#eef5ff); box-shadow:0 6px 20px rgba(0,0,0,0.05);padding:14px;border-radius:10px;line-height:1.8;font-size:16px">{explain_centered_ale_result(
                    ice_feature,
                    bin_centers,
                    ale_vals,
                    ale_summary,
                    target_col
                )}</div>""",
                unsafe_allow_html=True
            )
        except Exception as e:
            st.error(f"ALE 처리 오류: {e}")

    st.markdown("## 9) 종합 리포트")

    try:
        comprehensive_report = generate_comprehensive_report(
            model_choice=model_choice,
            target_col=target_col,
            metrics=metrics,
            weekly_metrics_df=weekly_metrics_df,
            shap_df=shap_df,
            fi_df=fi_df,
            week_importance=week_importance,
            heatmap_df=heatmap_df,
            cf_result=cf_result,
            ice_feature=ice_feature if "ice_feature" in locals() else None,
            ice_mean_slope=ice_mean_slope,
            ice_std_slope=ice_std_slope,
            pdp_summary=pdp_summary,
            ale_summary=ale_summary,
            bin_centers=bin_centers,
            ale_vals=ale_vals,
        )

        st.markdown(
            f"""
    <div style="background:linear-gradient(135deg,#ffffff,#eef5ff); box-shadow:0 6px 20px rgba(0,0,0,0.05);
    padding:18px;
    border-radius:12px;
    line-height:2.0;
    font-size:16px;
    word-break:normal;
    overflow-wrap:break-word">

    {comprehensive_report}

    </div>
            """,
            unsafe_allow_html=True
        )

    except Exception as e:
        st.warning(f"종합 리포트 생성 오류: {e}")

    st.success("통합 XAI 분석이 완료되었습니다.")


# streamlit run app.py — Cloud에서는 __name__ 가드 없이 매 rerun마다 UI 실행
if os.environ.get("PAI_APP_MODE") != "mobile":
    from dims_ui import run_desktop_ui
    run_desktop_ui(_render_advanced_xai_analysis)

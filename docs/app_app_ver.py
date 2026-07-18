"""
모바일 최적화 스마트팜 대시보드
실행: streamlit run app_app.py
"""
import os

os.environ["PAI_APP_MODE"] = "mobile"

import streamlit as st
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

st.set_page_config(
    page_title="스마트팜 대시보드",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# 분석 로직은 app.py에서 재사용 (데스크톱 UI는 실행되지 않음)
import app as core

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem !important;
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        max-width: 100% !important;
    }
    .m-hero {
        background: linear-gradient(135deg, #0f766e, #2563eb);
        color: #fff;
        border-radius: 18px;
        padding: 18px 16px;
        margin-bottom: 12px;
        box-shadow: 0 8px 24px rgba(37,99,235,0.25);
    }
    .m-hero h1 { color: #fff !important; font-size: 1.25rem !important; margin: 0 0 6px !important; }
    .m-hero p { color: #e0f2fe !important; font-size: 0.85rem !important; margin: 0 !important; line-height: 1.5; }
    .m-chip {
        display: inline-block;
        background: rgba(255,255,255,0.2);
        border-radius: 999px;
        padding: 4px 10px;
        font-size: 0.75rem;
        margin: 4px 4px 0 0;
        color: #fff !important;
    }
    [data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-size: 1.4rem !important;
    }
    [data-testid="stMetricLabel"] { color: #64748b !important; }
    div[data-testid="stSelectbox"] span,
    div[data-testid="stMultiSelect"] span {
        color: #1e293b !important;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.82rem !important;
        padding: 8px 10px !important;
        min-height: 44px;
    }
    div[data-testid="stFileUploader"] button {
        min-height: 44px !important;
    }
    [data-testid="stExpander"] summary {
        font-weight: 700 !important;
        color: #1e40af !important;
        font-size: 0.95rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def m_kpi_row(items):
    """모바일 KPI — 2열 그리드."""
    for i in range(0, len(items), 2):
        c1, c2 = st.columns(2)
        pair = items[i : i + 2]
        with c1:
            if len(pair) > 0:
                label, val, color = pair[0]
                core.render_kpi_cards([(label, val, color)])
        with c2:
            if len(pair) > 1:
                label, val, color = pair[1]
                core.render_kpi_cards([(label, val, color)])


def m_plotly(fig):
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=30))
    core.display_plotly(fig, use_container_width=True)


def m_chart_timeseries(df, x_col, y_col, title=None):
    fig = core.build_interactive_timeseries(df, x_col, y_col, title=title)
    m_plotly(fig)


# ── 헤더 ──────────────────────────────────────────────
crop_name = st.selectbox("🌱 작물 선택", ["토마토", "오이"], key="m_crop")
icon = "🍅" if crop_name == "토마토" else "🥒"
st.markdown(
    f"""
    <div class="m-hero">
        <h1>{icon} {crop_name} 생육·수확 분석</h1>
        <p>환경·생육 데이터 업로드 후 모바일에서 바로 분석합니다.</p>
        <span class="m-chip">7주 롤링</span>
        <span class="m-chip">예측 모델</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("#### 📁 데이터 업로드")
sensor_file = st.file_uploader("🌡️ 환경센서 CSV", type=["csv"], key="m_sensor")
yield_file = st.file_uploader("🌱 생육·수확 CSV", type=["csv"], key="m_yield")

if not (sensor_file and yield_file):
    st.info("두 CSV 파일을 모두 업로드하면 분석 탭이 열립니다.")
    st.stop()

# ── 데이터 로드 ──────────────────────────────────────
sensor_df = pd.read_csv(sensor_file)
yield_df = pd.read_csv(yield_file)
yield_df = core.aggregate_fruit_level_yield(
    yield_df,
    "조사일자" if "조사일자" in yield_df.columns else yield_df.columns[0],
)

growth_features = (
    ["초장", "생장길이", "엽수", "엽장", "엽폭", "줄기굵기", "화방높이"]
    if crop_name == "토마토"
    else ["초장", "엽수", "엽장", "엽폭", "줄기굵기", "화방높이"]
)

tab_map, tab_data, tab_model = st.tabs(
    ["🔗 매핑", "📊 데이터", "🤖 모델"]
)

# ══════════════════════════════════════════════════════
# TAB: 매핑
# ══════════════════════════════════════════════════════
with tab_map:
    with st.expander("1️⃣ 환경 센서 컬럼", expanded=True):
        date_col_sensor = st.selectbox(
            "날짜시간",
            sensor_df.columns,
            index=core.pick_column_index(
                sensor_df.columns,
                ["측정시간", "측정 일자", "날짜시간", "일시", "날짜", "Date", "datetime"],
            ),
            key="m_date_s",
        )
        temp_col = st.selectbox(
            "온도", sensor_df.columns,
            index=core.pick_column_index(sensor_df.columns, ["온도_내부", "내부온도", "온도"]),
            key="m_temp",
        )
        hum_col = st.selectbox(
            "습도", sensor_df.columns,
            index=core.pick_column_index(sensor_df.columns, ["상대습도_내부", "습도_내부", "습도"]),
            key="m_hum",
        )
        co2_col = st.selectbox(
            "CO₂", sensor_df.columns,
            index=core.pick_column_index(sensor_df.columns, ["잔존CO2", "CO2", "CO₂", "co2"]),
            key="m_co2",
        )
        solar_col = st.selectbox(
            "일사량", sensor_df.columns,
            index=core.pick_column_index(sensor_df.columns, ["누적일사량_외부", "일사량_외부", "일사량", "누적일사량"]),
            key="m_solar",
        )

    with st.expander("2️⃣ 수확/생육 컬럼", expanded=True):
        date_col_yield = st.selectbox(
            "조사일자", yield_df.columns,
            index=core.pick_column_index(yield_df.columns, ["조사일자", "날짜", "Date", "date"]),
            key="m_date_y",
        )
        harvest_count_col = st.selectbox(
            "수확수", yield_df.columns,
            index=core.pick_column_index(yield_df.columns, ["화방별수확수", "수확수", "수확과수"]),
            key="m_hcnt",
        )
        harvest_weight_col = st.selectbox(
            "착과수", yield_df.columns,
            index=core.pick_column_index(yield_df.columns, ["화방별착과수", "착과수", "수확과중"]),
            key="m_hw",
        )

    with st.expander("3️⃣ 추가 생육 지표", expanded=False):
        growth_cols = {}
        for gf in growth_features:
            options = [None] + yield_df.columns.tolist()
            default_idx = yield_df.columns.get_loc(gf) + 1 if gf in yield_df.columns else 0
            growth_cols[gf] = st.selectbox(gf, options, index=default_idx, key=f"m_gf_{gf}")

    selected_week = st.slider(
        "롤링 평균 기간 (주)",
        1, 7, st.session_state.get("m_weeks", 7),
        key="m_weeks_slider",
        help="조사일 기준 과거 N주 환경 평균",
    )
    st.session_state.m_weeks = selected_week

# 전처리 (탭 공통)
sensor_df[date_col_sensor] = pd.to_datetime(sensor_df[date_col_sensor], errors="coerce")
yield_df[date_col_yield] = pd.to_datetime(yield_df[date_col_yield], errors="coerce")
sensor_df = sensor_df.dropna(subset=[date_col_sensor]).copy()
yield_df = yield_df.dropna(subset=[date_col_yield]).copy()
sensor_df["date"] = sensor_df[date_col_sensor].dt.date
sensor_df["hour"] = sensor_df[date_col_sensor].dt.hour

for col in [temp_col, hum_col, co2_col, solar_col]:
    sensor_df[col] = pd.to_numeric(sensor_df[col], errors="coerce")
date_cols = {date_col_yield, date_col_sensor}
for col in [harvest_count_col, harvest_weight_col] + [c for c in growth_cols.values() if c]:
    if col and col in yield_df.columns and col not in date_cols:
        yield_df[col] = pd.to_numeric(yield_df[col], errors="coerce")

week_dfs = {}
for week in range(1, 8):
    week_dfs[week] = core.compute_rolling_summary(
        sensor_df=sensor_df, yield_df=yield_df,
        date_col_sensor=date_col_sensor, date_col_yield=date_col_yield,
        temp_col=temp_col, hum_col=hum_col, co2_col=co2_col, solar_col=solar_col,
        harvest_count_col=harvest_count_col, harvest_weight_col=harvest_weight_col,
        growth_cols=growth_cols, week=week,
    )

df = week_dfs[selected_week].copy()
env_feature_cols = [
    core.build_window_feature_name(selected_week, s)
    for s in [
        "평균주간온도(08~18시)", "평균야간온도(19~07시)",
        "평균주간습도(08~18시)", "평균야간습도(19~07시)",
        "평균주간CO₂(08~18시)", "평균야간CO₂(19~07시)",
        "평균누적일사량(1일최대값기준)",
    ]
]
env_feature_cols = [c for c in env_feature_cols if c in df.columns]
env_filled = int(df[env_feature_cols].notna().all(axis=1).sum()) if env_feature_cols else 0

env_mapping = {c: c for c in env_feature_cols}
growth_options = ["수확수", "착과수"] + growth_features

weekly_metrics_df = None
metrics = None
model = None
model_choice = None
target_col = None
features = []
X_train = X_test = None
shap_values = shap_df = fi_df = None
week_importance = heatmap_df = temporal_df = None
cf_result = None
ice_mean_slope = ice_std_slope = 0.0
pdp_summary = ale_summary = None
bin_centers = ale_vals = None
ice_feature = None

# ══════════════════════════════════════════════════════
# TAB: 데이터
# ══════════════════════════════════════════════════════
with tab_data:
    m_kpi_row([
        ("조사 건수", f"{len(df):,}", "#2563eb"),
        ("센서 행", f"{len(sensor_df):,}", "#0d9488"),
        ("선택 주차", f"{selected_week}주", "#7c3aed"),
        ("환경 매핑", f"{env_filled}/{len(df)}", "#059669"),
    ])

    with st.expander("📋 매핑 테이블 미리보기", expanded=False):
        st.dataframe(df.head(20), use_container_width=True, hide_index=True)

    st.markdown("##### 🌤️ 환경 시계열")
    env_pick = st.multiselect(
        "표시 항목",
        list(env_mapping.keys()),
        default=list(env_mapping.keys())[:3] if env_mapping else [],
        key="m_env_pick",
    )
    for label in env_pick:
        col = env_mapping[label]
        if col in df.columns:
            with st.expander(label, expanded=len(env_pick) <= 2):
                m_chart_timeseries(df, "조사일자", col, title=label)

    st.markdown("##### 📈 생육·수확 시계열")
    growth_pick = st.multiselect(
        "표시 항목",
        [c for c in growth_options if c in df.columns],
        default=[c for c in ["수확수", "착과수"] if c in df.columns],
        key="m_growth_pick",
    )
    for col_name in growth_pick:
        if col_name in df.columns:
            with st.expander(col_name, expanded=len(growth_pick) <= 2):
                m_chart_timeseries(df, "조사일자", col_name, title=col_name)

# ══════════════════════════════════════════════════════
# TAB: 모델
# ══════════════════════════════════════════════════════
with tab_model:
    model_choice = st.selectbox(
        "모델", ["RandomForest", "GradientBoosting", "XGBoost", "LGBM", "GaussianNB"],
        key="m_model",
    )
    target_col = st.selectbox(
        "예측 대상", ["수확수", "착과수"] + growth_features,
        key="m_target",
    )

    features = [c for c in df.columns if c not in ["조사일자", "수확수", "착과수"] + growth_features]
    X = df[features].copy().fillna(df[features].mean(numeric_only=True))
    y = df[target_col].copy()
    valid_mask = y.notna()
    X, y = X.loc[valid_mask].copy(), y.loc[valid_mask].copy()

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = core.make_model(model_choice)
    model.fit(X_train, y_train)
    y_pred = core.safe_predict(model, X_test, features)
    metrics = core.compute_metrics(y_test, y_pred)

    st.markdown("##### 📊 모델 성능")
    m_kpi_row([
        ("MSE", f"{metrics['MSE']:.3f}", "#2563eb"),
        ("MAE", f"{metrics['MAE']:.3f}", "#0d9488"),
        ("R²", f"{metrics['R2']:.3f}", "#d97706"),
    ])

    st.markdown("##### 📈 주차별 성능")
    weekly_metrics = []
    for wk in range(1, 8):
        wk_df = week_dfs[wk].copy()
        wk_features = [c for c in wk_df.columns if c not in ["조사일자", "수확수", "착과수"] + growth_features]
        X_wk = wk_df[wk_features].fillna(wk_df[wk_features].mean(numeric_only=True))
        y_wk = wk_df[target_col].dropna()
        X_wk = X_wk.loc[y_wk.index]
        if len(X_wk) < 5:
            continue
        Xt, Xv, yt, yv = train_test_split(X_wk, y_wk, test_size=0.2, random_state=42)
        wm = core.make_model(model_choice)
        wm.fit(Xt, yt)
        pv = core.safe_predict(wm, Xv, wk_features)
        weekly_metrics.append({
            "Week": wk,
            "MSE": mean_squared_error(yv, pv),
            "MAE": mean_absolute_error(yv, pv),
            "R2": r2_score(yv, pv),
        })

    weekly_metrics_df = pd.DataFrame(weekly_metrics) if weekly_metrics else None
    if weekly_metrics_df is not None and not weekly_metrics_df.empty:
        metric_view = st.radio("지표", ["MSE", "MAE", "R2"], horizontal=True, key="m_metric_view")
        colors = {"MSE": "#2563eb", "MAE": "#0d9488", "R2": "#d97706"}
        m_plotly(core.build_weekly_metric_chart(
            weekly_metrics_df, metric_view, metric_view, colors[metric_view]
        ))
        with st.expander("주차별 수치 표"):
            st.dataframe(weekly_metrics_df.round(4), use_container_width=True)

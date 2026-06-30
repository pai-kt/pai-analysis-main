"""
모바일 최적화 스마트팜 XAI 대시보드
실행: streamlit run app_app.py
"""
import os

os.environ["PAI_APP_MODE"] = "mobile"

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import shap
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.linear_model import LinearRegression

st.set_page_config(
    page_title="스마트팜 XAI",
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
        <h1>{icon} {crop_name} XAI 분석</h1>
        <p>환경·생육 데이터 업로드 후 모바일에서 바로 분석합니다.</p>
        <span class="m-chip">7주 롤링</span>
        <span class="m-chip">SHAP · ALE</span>
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

tab_map, tab_data, tab_model, tab_xai, tab_report = st.tabs(
    ["🔗 매핑", "📊 데이터", "🤖 모델", "🧠 XAI", "📄 리포트"]
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
                core.render_insight(core.explain_environment_timeseries(label, df[col]), variant="teal")

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

# ══════════════════════════════════════════════════════
# TAB: XAI
# ══════════════════════════════════════════════════════
with tab_xai:
    if model is None:
        st.warning("모델 탭에서 분석이 완료된 후 이용하세요.")
    else:
        st.caption(f"모델: {model_choice} · 대상: {target_col}")
        ice_feature = features[0] if features else None

        with st.expander("🔍 SHAP Summary", expanded=True):
            if model_choice == "GaussianNB":
                st.info("GaussianNB는 SHAP이 제한됩니다.")
            else:
                try:
                    explainer = shap.Explainer(model, X_train)
                    shap_values = explainer(X_test, check_additivity=False)
                    fig_shap = plt.figure(figsize=(5, 4))
                    shap.summary_plot(shap_values.values, X_test, show=False)
                    core.display_matplotlib(fig_shap)
                    plt.close(fig_shap)
                    shap_df = core.summarize_shap_results(shap_values, features)
                    st.info(core.explain_shap_summary(shap_df))
                except Exception as e:
                    st.error(f"SHAP 오류: {e}")

        with st.expander("📊 Feature Importance", expanded=False):
            try:
                fi_df = core.feature_importance_table(model, features)
                fig_fi, ax = plt.subplots(figsize=(5, 4))
                top = fi_df.head(10)
                ax.barh(top["Feature"], top["Importance"], color="#8b5cf6")
                ax.invert_yaxis()
                ax.set_title("Top 10")
                core.display_matplotlib(fig_fi)
                plt.close(fig_fi)
                st.info(core.explain_feature_importance(fi_df))
            except Exception as e:
                st.error(str(e))

        with st.expander("⏱ Temporal SHAP & Heatmap", expanded=False):
            if shap_values is not None:
                try:
                    merged_df = week_dfs[1][["조사일자", "수확수", "착과수"] + growth_features].copy()
                    for week in range(1, 8):
                        wk_df = week_dfs[week]
                        add_cols = [c for c in wk_df.columns if c not in ["조사일자", "수확수", "착과수"] + growth_features]
                        merged_df = merged_df.merge(wk_df[["조사일자"] + add_cols], on="조사일자", how="left")
                    temporal_features = [c for c in merged_df.columns if c not in ["조사일자", "수확수", "착과수"] + growth_features]
                    mX = merged_df[temporal_features].fillna(merged_df[temporal_features].mean(numeric_only=True))
                    my = merged_df[target_col].dropna()
                    mX = mX.loc[my.index]
                    mXt, mXv, myt, myv = train_test_split(mX, my, test_size=0.2, random_state=42)
                    tm = core.make_model(model_choice)
                    tm.fit(mXt, myt)
                    tsv = shap.Explainer(tm, mXt)(mXv, check_additivity=False)
                    temporal_df, week_importance, heatmap_df = core.build_temporal_shap_tables(tsv, temporal_features)
                    if week_importance is not None and not week_importance.empty:
                        fig_ts = core.fig_temporal_shap_bar(week_importance)
                        core.display_matplotlib(fig_ts)
                        plt.close(fig_ts)
                        st.info(core.explain_temporal_shap(week_importance, target_col))
                    if heatmap_df is not None and not heatmap_df.empty:
                        fig_hm = core.fig_feature_week_heatmap(heatmap_df, target_col)
                        core.display_matplotlib(fig_hm)
                        plt.close(fig_hm)
                        st.info(core.explain_heatmap(heatmap_df, target_col))
                except Exception as e:
                    st.warning(f"Temporal SHAP 오류: {e}")

        with st.expander("🔧 Counterfactual (환경 제어)", expanded=False):
            try:
                if len(X_test) == 0:
                    st.warning("테스트 샘플 없음")
                else:
                    cf_result = core.generate_counterfactual(
                        model=model, x_row=X_test.iloc[0].copy(), X_ref=X_train,
                        feature_names=features, target_delta=1.0, n_iter=2000,
                        random_state=42, top_n=5,
                    )
                    if cf_result:
                        before = float(cf_result.get("base_pred", 0))
                        after = float(cf_result.get("cf_pred", 0))
                        m_kpi_row([
                            ("현재 예측", f"{before:.2f}", "#2563eb"),
                            ("CF 예측", f"{after:.2f}", "#059669"),
                        ])
                        priority_df = cf_result.get("priority_df", pd.DataFrame())
                        if not priority_df.empty:
                            show_cols = [c for c in ["Feature", "ControlGroup", "PredDelta", "Recommendation"] if c in priority_df.columns]
                            st.dataframe(priority_df[show_cols].head(5), use_container_width=True, hide_index=True)
                        core.render_alert_card(core.explain_counterfactual(cf_result, target_col), variant="info")
            except Exception as e:
                st.error(str(e))

        with st.expander("📉 ICE + PDP / Centered ALE", expanded=False):
            ice_feature = st.selectbox("분석 변수", features, key="m_ice_feat")
            n_samples = st.slider("ICE 샘플", 1, max(1, len(X_test)), min(30, len(X_test)), key="m_ice_n")
            ale_bins = st.slider("ALE bins", 4, 20, 8, key="m_ale_bins")

            try:
                Xs = X_test.sample(n=min(n_samples, len(X_test)), random_state=42)
                xs = np.linspace(X_test[ice_feature].min(), X_test[ice_feature].max(), 40)
                ice_curves = []
                for _, row in Xs.iterrows():
                    Xtmp = pd.DataFrame(np.tile(row.values, (len(xs), 1)), columns=X_test.columns)
                    Xtmp[ice_feature] = xs
                    ice_curves.append(core.safe_predict(model, Xtmp, features))

                col = X_test[ice_feature]
                xgrid = np.linspace(col.min(), col.max(), 40)
                pdp_y = []
                Xbase = X_test.copy()
                for val in xgrid:
                    Xtmp = Xbase.copy()
                    Xtmp[ice_feature] = val
                    pdp_y.append(np.mean(core.safe_predict(model, Xtmp, features)))
                pdp_y = np.array(pdp_y)

                threshold = np.quantile(pdp_y, 0.9) if len(pdp_y) else 0
                mask = pdp_y >= threshold
                idx = np.where(mask)[0]
                best_interval = (xgrid[idx[0]], xgrid[idx[-1]]) if len(idx) else (xgrid[0], xgrid[-1])
                pdp_summary = {
                    "best_interval": best_interval,
                    "mean_val": float(np.mean(pdp_y[mask]) if mask.any() else 0),
                    "max_val": float(np.max(pdp_y)),
                }

                fig_mix = core.fig_ice_pdp(xs, ice_curves, xgrid, pdp_y, core.pretty_time_text(ice_feature), best_interval)
                core.display_matplotlib(fig_mix)
                plt.close(fig_mix)
                st.caption(f"최적 구간: {best_interval[0]:.2f} ~ {best_interval[1]:.2f}")
            except Exception as e:
                st.error(f"ICE+PDP 오류: {e}")

            try:
                x = X_test[ice_feature].values
                edges = np.unique(np.quantile(x, np.linspace(0, 1, ale_bins + 1)))
                centers, ale = [], []
                for i in range(len(edges) - 1):
                    lo, hi = edges[i], edges[i + 1]
                    m = (x >= lo) & (x <= hi) if i == len(edges) - 2 else (x >= lo) & (x < hi)
                    if not m.any():
                        continue
                    Xlo, Xhi = X_test.copy(), X_test.copy()
                    Xlo[ice_feature], Xhi[ice_feature] = lo, hi
                    delta = np.mean(core.safe_predict(model, Xhi, features) - core.safe_predict(model, Xlo, features))
                    ale.append(delta)
                    centers.append((lo + hi) / 2)
                bin_centers = np.array(centers)
                ale_vals = np.array(ale) - np.mean(ale)
                pos, neg = [], []
                for i, v in enumerate(ale_vals):
                    a, b = bin_centers[max(0, i - 1)], bin_centers[min(len(bin_centers) - 1, i + 1)]
                    if v > 0:
                        pos.append((a, b, v))
                    elif v < 0:
                        neg.append((a, b, v))
                ale_summary = {"pos_intervals": pos[:3], "neg_intervals": neg[:3]}

                fig_ale = core.fig_centered_ale(
                    bin_centers, ale_vals, core.pretty_time_text(ice_feature),
                    pos_intervals=ale_summary.get("pos_intervals"),
                    neg_intervals=ale_summary.get("neg_intervals"),
                )
                core.display_matplotlib(fig_ale)
                plt.close(fig_ale)
            except Exception as e:
                st.error(f"ALE 오류: {e}")

# ══════════════════════════════════════════════════════
# TAB: 리포트
# ══════════════════════════════════════════════════════
with tab_report:
    if metrics is None:
        st.warning("모델 탭에서 분석을 먼저 실행해 주세요.")
    else:
        try:
            report = core.generate_comprehensive_report(
                model_choice=model_choice,
                target_col=target_col,
                metrics=metrics,
                weekly_metrics_df=weekly_metrics_df,
                shap_df=shap_df,
                fi_df=fi_df,
                week_importance=week_importance,
                heatmap_df=heatmap_df,
                cf_result=cf_result,
                ice_feature=ice_feature,
                ice_mean_slope=ice_mean_slope,
                ice_std_slope=ice_std_slope,
                pdp_summary=pdp_summary,
                ale_summary=ale_summary,
                bin_centers=bin_centers,
                ale_vals=ale_vals,
            )
            st.markdown(
                f'<div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:14px;line-height:1.7;font-size:0.9rem;color:#334155;">{report}</div>',
                unsafe_allow_html=True,
            )
        except Exception as e:
            st.warning(f"리포트 생성 오류: {e}")

        st.success("✅ 모바일 분석 완료")

"""Desktop UI orchestrator — 4개 탭 조합."""
from __future__ import annotations

import streamlit as st
import pandas as pd

from src import core
from src.ui.common import (
    _focus_main_tab,
    _yield_cumulative_totals,
    build_growth_chart_df,
    build_status_env_kpis,
    render_dims_header,
    render_disclaimer,
)
from src.ui.styles import ADIMS_CSS, DARK_MODE_CSS, MAIN_TAB_LABELS
from src.ui.tabs.data import render_data_tab
from src.ui.tabs.forecast import render_forecast_tab
from src.ui.tabs.growth import render_rda_flow_tab
from src.ui.tabs.status import render_status_tab


def run_desktop_ui():
    st.markdown(ADIMS_CSS, unsafe_allow_html=True)

    if "dims_ready" not in st.session_state:
        st.session_state.dims_ready = False
    if "dims_analyzing" not in st.session_state:
        st.session_state.dims_analyzing = False
    if "weeks" not in st.session_state:
        st.session_state.weeks = 7
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False
    if st.session_state.dark_mode:
        st.markdown(DARK_MODE_CSS, unsafe_allow_html=True)

    with st.container(key="theme_toggle"):
        theme_icon = "☀" if st.session_state.dark_mode else "☾"
        theme_help = "라이트 모드로 전환" if st.session_state.dark_mode else "다크 모드로 전환"
        if st.button(theme_icon, key="theme_toggle_button", help=theme_help):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

    render_dims_header(st.session_state.get("dims_asof", "—"))

    tab_data, tab_env, tab_status, tab_forecast = st.tabs(MAIN_TAB_LABELS)

    with tab_data:
        mapping = render_data_tab()

    has_data = mapping["has_data"]
    can_analyze = bool(mapping.get("can_analyze"))
    sensor_df = mapping["sensor_df"]
    yield_df = mapping["yield_df"]

    if not has_data or not can_analyze:
        status_unlocked = bool(st.session_state.get("rda_env_detail_show"))
        with tab_env:
            # 필수 변수 일부가 있어도 농진청 조회는 가능하면 연결
            render_rda_flow_tab(
                sensor_df=sensor_df if can_analyze else None,
                date_col_sensor=mapping.get("date_col_sensor") if can_analyze else None,
                temp_col=mapping.get("temp_col") if can_analyze else None,
                hum_col=mapping.get("hum_col") if can_analyze else None,
                co2_col=mapping.get("co2_col") if can_analyze else None,
                solar_col=mapping.get("solar_col") if can_analyze else None,
                yield_df=yield_df if can_analyze else None,
                date_col_yield=mapping.get("date_col_yield") if can_analyze else None,
            )
        with tab_status:
            if has_data and not can_analyze:
                missing = mapping.get("missing_required") or []
                msg = "데이터 탭에서 필수 변수를 모두 매핑한 뒤 「분석 결과 보기」를 실행하세요."
                if missing:
                    msg += f" (누락: {', '.join(missing)})"
                st.info(msg)
            elif not status_unlocked:
                st.info("환경 설정 탭에서 「조회」를 눌러야 내 농가 진단 탭이 활성화됩니다.")
            else:
                render_status_tab(
                    dims_ready=False, has_data=False, env_kpis=[], growth_summary=None, growth_chart_df=None
                )
        with tab_forecast:
            render_forecast_tab(
                dims_ready=False,
                df=None,
                week_dfs={},
                selected_week=st.session_state.weeks,
                growth_features=[],
                fruit_total=0,
                delay_days=0,
            )
        render_disclaimer()
        return

    date_col_sensor = mapping["date_col_sensor"]
    temp_col = mapping["temp_col"]
    hum_col = mapping["hum_col"]
    co2_col = mapping["co2_col"]
    solar_col = mapping["solar_col"]
    date_col_yield = mapping["date_col_yield"]
    harvest_count_col = mapping["harvest_count_col"]
    harvest_weight_col = mapping["harvest_weight_col"]
    growth_cols = mapping["growth_cols"]
    growth_features = mapping["growth_features"]

    # 전처리
    analyzing = bool(st.session_state.get("dims_analyzing"))
    progress = mapping.get("progress_bar")

    def _set_progress(ratio: float) -> None:
        if progress is not None:
            progress.progress(min(1.0, max(0.0, ratio)))

    _set_progress(0.05)
    sensor_df[date_col_sensor] = pd.to_datetime(sensor_df[date_col_sensor], errors="coerce")
    yield_df[date_col_yield] = pd.to_datetime(yield_df[date_col_yield], errors="coerce")
    sensor_df = sensor_df.dropna(subset=[date_col_sensor]).copy()
    yield_df = yield_df.dropna(subset=[date_col_yield]).copy()
    sensor_df["date"] = sensor_df[date_col_sensor].dt.date
    sensor_df["hour"] = sensor_df[date_col_sensor].dt.hour
    for col in [temp_col, hum_col, co2_col, solar_col]:
        sensor_df[col] = pd.to_numeric(sensor_df[col], errors="coerce")
    for col in [harvest_count_col, harvest_weight_col] + [c for c in growth_cols.values() if c]:
        if col and col in yield_df.columns:
            yield_df[col] = pd.to_numeric(yield_df[col], errors="coerce")

    selected_week = st.session_state.weeks
    week_dfs = {}
    model_weeks = list(range(3, 13))
    for i, wk in enumerate(model_weeks):
        _set_progress(0.1 + 0.55 * ((i + 1) / len(model_weeks)))
        week_dfs[wk] = core.compute_rolling_summary(
            sensor_df,
            yield_df,
            date_col_sensor,
            date_col_yield,
            temp_col,
            hum_col,
            co2_col,
            solar_col,
            harvest_count_col,
            harvest_weight_col,
            growth_cols,
            wk,
        )
    df = week_dfs[selected_week].copy()
    if df.empty or "조사일자" not in df.columns:
        st.session_state.dims_show_complete_msg = False
        st.session_state.dims_analyzing = False
        st.error("생육·수확 데이터를 처리하지 못했습니다. **조사일자** 컬럼과 날짜 형식을 확인해 주세요.")
        with tab_env:
            render_rda_flow_tab(
                sensor_df=sensor_df,
                date_col_sensor=date_col_sensor,
                temp_col=temp_col,
                hum_col=hum_col,
                co2_col=co2_col,
                solar_col=solar_col,
                yield_df=yield_df,
                date_col_yield=date_col_yield,
            )
        render_disclaimer()
        return

    df = df.sort_values("조사일자")
    latest = df.iloc[-1] if len(df) else None
    asof = pd.to_datetime(latest["조사일자"]).strftime("%Y-%m-%d") if latest is not None else "—"
    st.session_state.dims_asof = asof

    dims_ready = st.session_state.dims_ready

    _set_progress(0.72)
    yield_chart_df = build_growth_chart_df(
        yield_df, date_col_yield, harvest_count_col, harvest_weight_col, growth_cols
    )
    harvest_total, fruit_total = _yield_cumulative_totals(
        yield_df, date_col_yield, harvest_count_col, harvest_weight_col, growth_cols
    )

    _set_progress(0.82)

    from src.growth_standards import summarize_growth_vs_standard

    _set_progress(0.92)
    if dims_ready and not df.empty:
        growth_chart_df = build_growth_chart_df(
            df, growth_cols={gf: gf for gf in growth_features if gf in df.columns}
        )
    else:
        growth_chart_df = yield_chart_df
    growth_summary = summarize_growth_vs_standard(growth_chart_df)
    delay_days = growth_summary["delay_days"]

    if analyzing:
        _set_progress(1.0)
        st.session_state.dims_analyzing = False

    if dims_ready and st.session_state.get("dims_show_complete_msg"):
        with tab_data:
            st.success("분석이 완료되었습니다. 결과를 확인하세요.")
        st.session_state.dims_show_complete_msg = False

    # 환경관리 조회를 현황 KPI 계산보다 먼저 처리해 「조회」 결과가 같은 런에 반영되게 함
    with tab_env:
        render_rda_flow_tab(
            sensor_df=sensor_df,
            date_col_sensor=date_col_sensor,
            temp_col=temp_col,
            hum_col=hum_col,
            co2_col=co2_col,
            solar_col=solar_col,
            yield_df=yield_df,
            date_col_yield=date_col_yield,
        )

    status_unlocked = bool(st.session_state.get("rda_env_detail_show"))

    env_kpis = build_status_env_kpis(
        sensor_df=sensor_df,
        date_col_sensor=date_col_sensor,
        temp_col=temp_col,
        hum_col=hum_col,
        solar_col=solar_col,
        co2_col=co2_col,
        latest_row=latest if dims_ready else None,
        selected_week=selected_week,
        core=core if dims_ready else None,
        yield_df=yield_df,
        date_col_yield=date_col_yield,
    )

    with tab_status:
        if not status_unlocked:
            st.info("환경 설정 탭에서 「조회」를 눌러야 내 농가 진단 탭이 활성화됩니다.")
        else:
            render_status_tab(
                dims_ready=dims_ready,
                has_data=True,
                env_kpis=env_kpis,
                growth_summary=growth_summary,
                growth_chart_df=growth_chart_df,
                harvest_total=harvest_total,
                fruit_total=fruit_total,
                env_weeks=selected_week,
            )

    with tab_forecast:
        render_forecast_tab(
            dims_ready=dims_ready,
            df=df,
            week_dfs=week_dfs,
            selected_week=selected_week,
            growth_features=growth_features,
            fruit_total=fruit_total,
            delay_days=delay_days,
        )

    goto_tab = st.session_state.pop("dims_goto_tab", None)
    if goto_tab is not None:
        _focus_main_tab(int(goto_tab))

    render_disclaimer()

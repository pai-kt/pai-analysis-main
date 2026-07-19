"""Tab 3 · 환경관리 (농진청 표준 조회)."""
from __future__ import annotations

import html

import streamlit as st
import pandas as pd
import numpy as np

from src.ui.common import (
    build_recent_env_measures,
    build_env_kpis_from_measures,
    render_env_detail_section,
    render_tab_hero,
)

_RDA_STAGE_SHORT_LABELS = {
    "생육초기": "생육초기",
    "생육중기(9~10월)": "중기(9~10)",
    "생육중기(11~12월)": "중기(11~12)",
    "생육중기(1~2월)": "중기(1~2)",
    "생육중기(3~6월)": "중기(3~6)",
    "생육말기(7~8월)": "말기(7~8)",
    "생육말기(7~8월, 상대 주차 < 10)": "말기(7~8)",
}


def _build_rda_stage_bar_html(selected: str, stages: list[str], kind: str) -> str:
    """농진청 생육단계 바 HTML (기존 stage-bar / stage-seg 형태)."""
    from src.rda_standards import RDA_STAGE_COLORS

    n = len(stages)
    segs = []
    for i, stage in enumerate(stages):
        color = RDA_STAGE_COLORS.get(stage, "#4E79A7")
        opacity = "1" if stage == selected else "0.45"
        border = "2px solid var(--ink)" if stage == selected else "2px solid transparent"
        cls = "stage-seg stage-seg--s1" if i == 0 else "stage-seg"
        label = html.escape(_RDA_STAGE_SHORT_LABELS.get(stage, stage))
        segs.append(
            f'<div class="{cls}" style="width:{100 / n:.4f}%;min-width:{100 / n:.4f}%;'
            f'background:{color};opacity:{opacity};border:{border};">{label}</div>'
        )
    return f'<div class="stage-bar stage-bar-rda-{html.escape(kind)}">{"".join(segs)}</div>'


def render_rda_stage_picker(kind: str, selected: str, stages: list[str]) -> None:
    """생육단계 컬러 바 (라디오 선택과 동기화된 시각 표시)."""
    st.markdown(_build_rda_stage_bar_html(selected, stages, kind), unsafe_allow_html=True)


def _format_rda_cell(col, v) -> str:
    """표 셀 표시: 기본 소수점 1자리, CO₂·급액량은 정수."""
    col_name = str(col)
    as_int = any(
        key in col_name
        for key in ("잔존CO₂", "잔존 CO₂", "1회 급액량", "1일 공급량", "1일 급액량")
    )

    def _fmt_num(n: float) -> str:
        if as_int:
            return str(int(round(n)))
        return f"{n:.1f}"

    if pd.isna(v):
        return "—"
    if isinstance(v, (int, float, np.integer, np.floating)):
        return _fmt_num(float(v))
    text = str(v).strip()
    if "~" in text:
        lo_s, hi_s = text.split("~", 1)
        try:
            return f"{_fmt_num(float(lo_s.strip()))}~{_fmt_num(float(hi_s.strip()))}"
        except ValueError:
            return text
    try:
        return _fmt_num(float(text))
    except ValueError:
        return text


def render_rda_result_table(view: pd.DataFrame, highlight_indices: list[int] | None = None):
    highlights = set(highlight_indices or [])
    headers = "".join(f"<th>{html.escape(str(c))}</th>" for c in view.columns)
    rows = []
    for i in range(len(view)):
        row = view.iloc[i]
        cls = ' class="rda-row-match"' if i in highlights else ""
        cells = []
        for c in view.columns:
            text = _format_rda_cell(c, row[c])
            cells.append(f"<td>{html.escape(text)}</td>")
        rows.append(f"<tr{cls}>{''.join(cells)}</tr>")
    st.markdown(
        f'<div class="card rda-result-scroll">'
        f'<table class="stage-tbl rda-result-tbl"><thead><tr>{headers}</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>',
        unsafe_allow_html=True,
    )


def _rda_environment_ranges(match_row: dict | pd.Series | None) -> dict[str, tuple[float, float]]:
    """농진청 비교표의 권장 범위를 환경 게이지 키로 변환."""
    from src.rda_standards import parse_range

    if match_row is None:
        return {}
    mapping = {
        "일사량": "누적일사량(범위)",
        "주간온도": "주간 평균온도(℃)",
        "야간온도": "야간 평균온도(℃)",
    }
    ranges: dict[str, tuple[float, float]] = {}
    for env_key, rda_col in mapping.items():
        value = match_row.get(rda_col)
        lo, hi = parse_range(value)
        if lo is not None and hi is not None:
            ranges[env_key] = (lo, hi)
    return ranges


def _parse_geolocation(location) -> dict | None:
    """streamlit_geolocation 반환값 정규화 (dict / JSON str / None)."""
    if location is None:
        return None
    if isinstance(location, dict):
        return location
    if isinstance(location, str):
        text = location.strip()
        if not text:
            return None
        import ast
        import json

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            try:
                parsed = ast.literal_eval(text)
            except (ValueError, SyntaxError):
                return None
        if isinstance(parsed, dict):
            return parsed
        return None
    return None


def _sync_gps_outdoor_temp() -> tuple[float | None, str | None]:
    """브라우저 GPS → Open-Meteo 현재 기온. session_state에 캐시."""
    from src.geo_weather import fetch_current_temperature, reverse_geocode_label
    from streamlit_geolocation import streamlit_geolocation

    btn_col, label_col = st.columns([1, 5], gap="small")
    with btn_col:
        location = _parse_geolocation(streamlit_geolocation())
    with label_col:
        st.markdown(
            '<div class="gps-allow-label">위치 접근 허용</div>',
            unsafe_allow_html=True,
        )
    if not location or location.get("latitude") is None or location.get("longitude") is None:
        return st.session_state.get("rda_gps_temp"), st.session_state.get("rda_gps_label")

    lat = float(location["latitude"])
    lon = float(location["longitude"])
    coords = (round(lat, 5), round(lon, 5))

    if st.session_state.get("rda_gps_coords") == coords:
        return st.session_state.get("rda_gps_temp"), st.session_state.get("rda_gps_label")

    temp = fetch_current_temperature(lat, lon)
    label = reverse_geocode_label(lat, lon)
    st.session_state.rda_gps_coords = coords
    st.session_state.rda_gps_temp = temp
    st.session_state.rda_gps_label = label

    if temp is not None:
        _apply_rda_outdoor_temp(temp, label)

    return temp, label


def _apply_rda_outdoor_temp(temp: float | None, label: str | None) -> None:
    st.session_state.rda_outdoor_temp = temp
    st.session_state.rda_outdoor_label = label
    st.session_state.rda_gps_temp = temp
    st.session_state.rda_gps_label = label
    if temp is not None:
        outdoor_str = f"{temp:.1f}"
        for kind in ("solar", "growth"):
            st.session_state[f"rda_outdoor_{kind}"] = outdoor_str


def render_rda_outdoor_location() -> tuple[float | None, str | None]:
    """GPS 또는 시·도/시·군·구 선택으로 외기기온 조회."""
    from src.geo_weather import fetch_outdoor_temp_for_region
    from src.korea_regions import list_sido, list_sigungu

    with st.container(key="rda_location_card"):
        st.markdown(
            """
            <div class="rda-section-head">
              <div class="rda-step">01</div>
              <div>
                <div class="rda-section-kicker">Location · 위치</div>
                <div class="rda-section-title">외기기온을 불러올 위치</div>
                <div class="rda-section-desc">현재 위치를 사용하거나 지역을 직접 선택하세요.</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        mode = st.radio(
            "외기기온 입력 방식",
            ["GPS 현재 위치", "지역 직접 선택"],
            horizontal=True,
            key="rda_loc_mode",
        )

        if mode == "GPS 현재 위치":
            gps_temp, gps_label = _sync_gps_outdoor_temp()
            if gps_temp is not None and gps_label:
                st.success(f"📍 현재 위치 **{gps_label}** · 외기기온 **{gps_temp:.1f}°C** (GPS 기준)")
            else:
                st.info("📍 브라우저에서 **위치 접근을 허용**하면 현재 위치의 외기기온을 자동으로 불러옵니다.")
            return gps_temp, gps_label

        sidos = list_sido()
        c1, c2 = st.columns(2)
        with c1:
            sido = st.selectbox("시·도", sidos, key="rda_manual_sido")
        sigungu_options = list_sigungu(sido)
        with c2:
            sigungu = st.selectbox(
                "시·군·구",
                sigungu_options,
                key=f"rda_manual_sigungu_{sido}",
            )

        temp, label = fetch_outdoor_temp_for_region(sido, sigungu)
        if temp is not None and label:
            _apply_rda_outdoor_temp(temp, label)
            st.success(f"📍 **{label}** · 외기기온 **{temp:.1f}°C** (선택 지역 기준)")
        else:
            st.warning("선택한 지역의 기온을 불러오지 못했습니다. 다른 지역을 선택해 보세요.")
        return temp, label


def render_rda_gps_location() -> tuple[float | None, str | None]:
    """하위 호환 alias."""
    return render_rda_outdoor_location()


def render_rda_flow_tab(
    sensor_df=None,
    date_col_sensor=None,
    temp_col=None,
    hum_col=None,
    solar_col=None,
    co2_col=None,
    yield_df=None,
    date_col_yield=None,
):
    from src.rda_standards import (
        RDA_STAGES_GROWTH,
        RDA_STAGES_SOLAR,
        estimate_cumulative_solar,
        estimate_outdoor_temp,
        find_best_match_group,
        format_display_table,
        GROWTH_DISPLAY_COLS,
        infer_stage_from_month,
        load_growth_standard,
        load_solar_standard,
        SOLAR_DISPLAY_COLS,
    )

    render_tab_hero(
        "Env · 환경관리",
        "농진청 표준으로 환경을 맞춰보세요",
        "일사량·생육단계별 농진청 최적환경 표준을 조회하고, 최근 실측과 비교합니다.",
    )

    gps_temp, gps_label = render_rda_outdoor_location()

    default_stage = "생육중기(3~6월)"
    if yield_df is not None and date_col_yield and date_col_yield in yield_df.columns:
        dates = pd.to_datetime(yield_df[date_col_yield], errors="coerce").dropna()
        if not dates.empty:
            default_stage = infer_stage_from_month(int(dates.max().month))

    default_solar = None
    default_outdoor = gps_temp or st.session_state.get("rda_outdoor_temp")
    if default_outdoor is None and sensor_df is not None and date_col_sensor:
        if temp_col:
            default_outdoor = estimate_outdoor_temp(sensor_df, date_col_sensor, temp_col)

    outdoor_prefill = f"{default_outdoor:.1f}" if default_outdoor is not None else ""
    for kind in ("solar", "growth"):
        key = f"rda_outdoor_{kind}"
        if key not in st.session_state:
            st.session_state[key] = outdoor_prefill

    if sensor_df is not None and date_col_sensor:
        if solar_col:
            default_solar = estimate_cumulative_solar(sensor_df, date_col_sensor, solar_col)

    sub_solar, sub_growth = st.tabs(["일사량별 최적환경", "생육상태별 최적생산량"])

    for sub, kind in ((sub_solar, "solar"), (sub_growth, "growth")):
        with sub:
            with st.container(key=f"rda_setup_{kind}"):
                st.markdown(
                    """
                    <div class="rda-section-head">
                      <div class="rda-step">02</div>
                      <div>
                        <div class="rda-section-kicker">Condition · 조건</div>
                        <div class="rda-section-title">시설과 생육단계 선택</div>
                        <div class="rda-section-desc">재배 조건에 맞는 농진청 권장 기준을 찾습니다.</div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                facility = st.radio(
                    "시설유형", ["비닐", "유리"], horizontal=True, key=f"rda_facility_{kind}"
                )
                stages = RDA_STAGES_SOLAR if kind == "solar" else RDA_STAGES_GROWTH
                stage_key = f"rda_stage_{kind}"
                if stage_key not in st.session_state:
                    st.session_state[stage_key] = (
                        default_stage if default_stage in stages else stages[4]
                    )
                stage = st.radio(
                    "생육단계 선택",
                    stages,
                    horizontal=True,
                    key=stage_key,
                )
                render_rda_stage_picker(kind, stage, stages)

            with st.container(key=f"rda_search_card_{kind}"):
                st.markdown(
                    """
                    <div class="rda-section-head rda-section-head--compact">
                      <div class="rda-step">03</div>
                      <div>
                        <div class="rda-section-kicker">Search · 조회</div>
                        <div class="rda-section-title">맞춤형 최적환경 설정</div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                c1, c2, c3 = st.columns([1, 1, 0.55])
                with c1:
                    solar_str = st.text_input(
                        "누적일사량 (J/㎠/day)",
                        value=f"{default_solar:,.0f}".replace(",", "") if default_solar else "",
                        placeholder="예: 2000",
                        key=f"rda_solar_{kind}",
                    )
                with c2:
                    outdoor_str = st.text_input(
                        "외기기온 (℃)",
                        placeholder="예: 18.0",
                        key=f"rda_outdoor_{kind}",
                        help="GPS 또는 선택 지역 기온이 자동 입력됩니다. 필요하면 직접 수정할 수 있습니다.",
                    )
                with c3:
                    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                    can_search = bool(solar_str.strip())
                    search = st.button(
                        "조회",
                        type="primary",
                        use_container_width=True,
                        disabled=not can_search,
                        key=f"rda_search_{kind}",
                    )

            if kind == "solar":
                raw = load_solar_standard(facility, stage)
                display_cols = SOLAR_DISPLAY_COLS
                title = f"{stage} 최적 생산환경 설정"
            else:
                raw = load_growth_standard(facility, stage)
                display_cols = GROWTH_DISPLAY_COLS
                title = f"{stage} 최적 생산·생육 설정"

            if raw.empty:
                st.warning("농진청 표준 데이터 파일을 찾을 수 없습니다. `data/농진청 표준/` 폴더의 xlsx 파일을 확인해 주세요.")
                continue

            solar_q = outdoor_q = None
            match_group_idx: list[int] = []
            aggregated_rec = None
            if search:
                st.session_state["rda_env_detail_show"] = True
                try:
                    if solar_str.strip():
                        solar_q = float(solar_str.replace(",", ""))
                        st.session_state["rda_last_solar_q"] = solar_q
                    else:
                        st.session_state.pop("rda_last_solar_q", None)
                except ValueError:
                    st.warning("누적일사량은 숫자로 입력해 주세요.")
                try:
                    if outdoor_str.strip():
                        outdoor_q = float(outdoor_str.replace(",", ""))
                except ValueError:
                    st.warning("외기기온은 숫자로 입력해 주세요.")

            if search and (solar_q is not None or outdoor_q is not None):
                shown = raw.copy()
                match_group_idx, aggregated_rec = find_best_match_group(shown, solar_q, outdoor_q)
                if kind == "solar":
                    if aggregated_rec is not None:
                        st.session_state["rda_last_environment_rec"] = aggregated_rec.to_dict()
                    else:
                        st.session_state.pop("rda_last_environment_rec", None)
                st.info("입력한 누적일사량·외기기온에 해당하는 권장 설정을 노란색으로 표시합니다.")
            else:
                shown = raw.copy()

            view = format_display_table(shown, display_cols)
            st.markdown(f'<div class="eyebrow">Result · <span class="ko">{title}</span></div>', unsafe_allow_html=True)
            if default_solar and not search:
                loc_label = st.session_state.get("rda_outdoor_label") or gps_label
                loc_temp = gps_temp or st.session_state.get("rda_outdoor_temp")
                outdoor_note = (
                    f"외기기온: **{loc_temp:.1f}°C** ({loc_label})"
                    if loc_temp is not None and loc_label
                    else "외기기온: 위치 미확인 — 온실 내부 온도로 대용 추정 가능"
                )
                st.caption(
                    f"센서 데이터 기준 최근 7일 일별 누적일사량 최댓값 중 최댓값: **{default_solar:,.0f}** J/㎠/day · {outdoor_note}"
                )
            if not view.empty:
                highlight = match_group_idx if search else None
                render_rda_result_table(view, highlight_indices=highlight)

    if st.session_state.get("rda_env_detail_show"):
        if sensor_df is not None and date_col_sensor and temp_col:
            solar_override = st.session_state.get("rda_last_solar_q")
            measures = build_recent_env_measures(
                sensor_df,
                date_col_sensor,
                temp_col,
                hum_col,
                solar_col,
                co2_col=co2_col,
                solar_override=solar_override,
            )
            rda_ranges = _rda_environment_ranges(
                st.session_state.get("rda_last_environment_rec")
            )
            rda_kpis = build_env_kpis_from_measures(
                measures,
                optimal_ranges=rda_ranges,
            )
            render_env_detail_section(
                rda_kpis,
                sensor_df=sensor_df,
                date_col=date_col_sensor,
                temp_col=temp_col,
                hum_col=hum_col,
                context_note=(
                    "※ 누적일사량·주간 온도·야간 온도의 적정 구간은 위 농진청 권장 조회 결과 기준입니다. "
                    "그 외 항목은 작기 전체 기본 기준입니다. "
                    "<b style=\"color:var(--ink-2)\">업로드한 환경센서 최근 7일</b> 데이터로 계산했습니다. "
                    "현재 생육단계 목표 환경을 확인하세요."
                ),
            )
        else:
            st.markdown(
                '<div class="eyebrow">Env · <span class="ko">환경 상세 — 지금 값·적정 구간·제어 품질</span></div>',
                unsafe_allow_html=True,
            )
            st.info("환경센서 데이터를 업로드하면 조회 결과와 함께 환경 상세를 확인할 수 있습니다.")

    st.markdown('<div class="tab-bottom-spacer"></div>', unsafe_allow_html=True)


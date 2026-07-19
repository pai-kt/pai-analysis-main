"""Tab 1 · 데이터 (업로드 · 보안키 · 컬럼 매핑)."""
from __future__ import annotations

import html

import streamlit as st

import src.column_mapping as colmap
from src import core
from src.ui.common import read_uploaded_table, read_table_path, render_tab_hero
from src.ui.styles import (
    DEFAULT_SENSOR_FILE,
    DEFAULT_YIELD_FILE,
    DIMS_SECURITY_KEY,
    MAIN_TAB_STATUS,
)

# 필수 입력 변수 정의: (표시명, 후보 컬럼명 목록)
SENSOR_REQUIRED = [
    ("측정일자", ["측정시간", "측정 일자", "날짜시간", "일시", "날짜", "Date", "datetime"]),
    ("온도", ["온도(℃)", "온도_내부", "내부온도", "온도"]),
    ("습도", ["상대 습도(%)", "상대습도_내부", "습도_내부", "습도"]),
    ("CO₂", ["CO2(ppm)", "잔존CO2", "CO2", "CO₂", "co2"]),
    ("외부누적일사량", []),  # 전용 matcher 사용
]

YIELD_BASE_REQUIRED = [
    ("조사일자", ["조사일자", "조사 일자", "날짜", "Date", "date"]),
    ("수확수", ["화방별수확수", "수확수", "수확과수"]),
    ("착과수", ["화방별착과수", "착과수", "수확과중"]),
]


def _growth_features(crop_name: str) -> list[str]:
    if crop_name == "토마토":
        return ["초장", "생장길이", "엽수", "엽장", "엽폭", "줄기굵기", "화방높이"]
    return ["초장", "엽수", "엽장", "엽폭", "줄기굵기", "화방높이"]


def _yield_required(crop_name: str) -> list[tuple[str, list[str]]]:
    growth = [(name, [name]) for name in _growth_features(crop_name)]
    return YIELD_BASE_REQUIRED + growth


def _find_column(columns, candidates) -> str | None:
    """후보와 일치하는 컬럼을 찾고, 없으면 None."""
    cols = list(columns)
    if not cols or not candidates:
        return None
    for name in candidates:
        if name in cols:
            return name
    for name in candidates:
        for col in cols:
            if name in str(col):
                return col
    return None


def _resolve_sensor_required(columns) -> list[tuple[str, str | None]]:
    resolved = []
    for label, candidates in SENSOR_REQUIRED:
        if label == "외부누적일사량":
            matched = colmap.list_external_cumulative_solar_columns(columns)
            resolved.append((label, matched[0] if matched else None))
        else:
            resolved.append((label, _find_column(columns, candidates)))
    return resolved


def _resolve_yield_required(columns, crop_name: str) -> list[tuple[str, str | None]]:
    return [
        (label, _find_column(columns, candidates))
        for label, candidates in _yield_required(crop_name)
    ]


def _render_required_list(labels: list[str]):
    chips = "".join(f'<span class="mchip req">{html.escape(x)}</span>' for x in labels)
    st.markdown(
        f'<div class="req-vars"><div class="req-label">필수 입력 변수</div>'
        f'<div class="mchips">{chips}</div></div>',
        unsafe_allow_html=True,
    )


def _render_mapping_chips(resolved: list[tuple[str, str | None]]):
    parts = []
    for label, matched in resolved:
        if matched:
            tip = html.escape(str(matched))
            parts.append(
                f'<span class="mchip ok" title="매핑: {tip}">{html.escape(label)} ✓</span>'
            )
        else:
            parts.append(f'<span class="mchip miss">{html.escape(label)} ✗</span>')
    st.markdown(f'<div class="mchips">{"".join(parts)}</div>', unsafe_allow_html=True)


def _render_upload_panel(title: str, labels: list[str]):
    st.markdown(
        f"""
        <div class="upload-panel-head">
          <div class="upload-panel-title">{html.escape(title)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _render_required_list(labels)


def render_data_tab() -> dict:
    """데이터 탭 UI. 매핑·데이터프레임·실행 여부를 dict로 반환."""
    render_tab_hero(
        "Data · 데이터 준비",
        "분석할 데이터를 올려주세요",
        "보안키 또는 파일 업로드 중 <b>하나</b>를 선택해 분석을 진행하세요.",
    )

    top1, top2 = st.columns([1.1, 2], gap="large")
    with top1:
        st.markdown('<div class="data-field-label">작물 선택</div>', unsafe_allow_html=True)
        crop_name = st.selectbox(
            "작물",
            ["토마토", "딸기", "파프리카", "오이"],
            key="dims_crop",
            label_visibility="collapsed",
        )
    with top2:
        st.markdown('<div class="data-field-label">데이터 입력 방식</div>', unsafe_allow_html=True)
        if "dims_data_source_mode" not in st.session_state:
            st.session_state.dims_data_source_mode = "파일 업로드"
        prev_mode = st.session_state.get("dims_data_source_mode")
        data_source_mode = st.radio(
            "데이터 입력 방식",
            ["보안키 사용", "파일 업로드"],
            horizontal=True,
            key="dims_data_source_mode",
            label_visibility="collapsed",
        )
    if prev_mode and prev_mode != data_source_mode:
        if data_source_mode == "보안키 사용":
            st.session_state.pop("dims_sensor", None)
            st.session_state.pop("dims_yield", None)
        else:
            st.session_state["dims_security_key"] = ""

    demo_unlocked = False
    has_uploads = False
    sensor_file = yield_file = None
    growth_features = _growth_features(crop_name)
    sensor_req_labels = [label for label, _ in SENSOR_REQUIRED]
    yield_req_labels = [label for label, _ in _yield_required(crop_name)]

    if data_source_mode == "보안키 사용":
        st.markdown(
            '<div class="data-note-card">데모용 보안키를 입력하면 샘플 데이터로 바로 분석할 수 있습니다.</div>',
            unsafe_allow_html=True,
        )
        security_key = st.text_input(
            "보안키",
            type="password",
            key="dims_security_key",
            placeholder="데모 분석용 보안키 입력",
        )
        demo_unlocked = bool(security_key) and security_key == DIMS_SECURITY_KEY
        if security_key and not demo_unlocked:
            st.warning("보안키가 올바르지 않습니다.")
        elif demo_unlocked:
            st.caption(
                f"데모 데이터 사용: {DEFAULT_SENSOR_FILE.name} · {DEFAULT_YIELD_FILE.name}"
            )
        if demo_unlocked and not (
            DEFAULT_SENSOR_FILE.exists() and DEFAULT_YIELD_FILE.exists()
        ):
            st.error("데모 데이터 파일을 찾을 수 없습니다. `data/test/` 폴더를 확인해 주세요.")

        c1, c2 = st.columns(2, gap="small")
        with c1:
            with st.container(key="upload_panel_yield_demo"):
                _render_upload_panel("수확·생육 데이터", yield_req_labels)
        with c2:
            with st.container(key="upload_panel_sensor_demo"):
                _render_upload_panel("환경센서 데이터", sensor_req_labels)
                st.markdown('<div class="env-card-spacer"></div>', unsafe_allow_html=True)
    else:
        c1, c2 = st.columns(2, gap="small")
        with c1:
            with st.container(key="upload_panel_yield"):
                _render_upload_panel("수확·생육 데이터", yield_req_labels)
                yield_file = st.file_uploader(
                    "수확·생육", type=["csv", "xlsx"], label_visibility="collapsed", key="dims_yield"
                )
        with c2:
            with st.container(key="upload_panel_sensor"):
                _render_upload_panel("환경센서 데이터", sensor_req_labels)
                st.markdown('<div class="env-card-spacer"></div>', unsafe_allow_html=True)
                sensor_file = st.file_uploader(
                    "환경센서", type=["csv", "xlsx"], label_visibility="collapsed", key="dims_sensor"
                )
        has_uploads = bool(sensor_file and yield_file)

    has_demo = (
        data_source_mode == "보안키 사용"
        and demo_unlocked
        and DEFAULT_SENSOR_FILE.exists()
        and DEFAULT_YIELD_FILE.exists()
    )
    has_data = has_demo if data_source_mode == "보안키 사용" else has_uploads
    can_analyze = False
    missing_required: list[str] = []

    sensor_df = yield_df = None
    if data_source_mode == "보안키 사용" and has_demo:
        sensor_df = read_table_path(DEFAULT_SENSOR_FILE)
        yield_df = read_table_path(DEFAULT_YIELD_FILE)
    elif data_source_mode == "파일 업로드" and has_uploads:
        sensor_df = read_uploaded_table(sensor_file)
        yield_df = read_uploaded_table(yield_file)

    mapping = {
        "has_data": has_data,
        "can_analyze": False,
        "missing_required": [],
        "crop_name": crop_name,
        "sensor_df": None,
        "yield_df": None,
        "growth_features": [],
        "date_col_sensor": None,
        "temp_col": None,
        "hum_col": None,
        "co2_col": None,
        "solar_col": None,
        "date_col_yield": None,
        "harvest_count_col": None,
        "harvest_weight_col": None,
        "growth_cols": {},
    }

    if has_data and sensor_df is not None and yield_df is not None:
        yield_df = core.aggregate_fruit_level_yield(
            yield_df, "조사일자" if "조사일자" in yield_df.columns else yield_df.columns[0]
        )

        sensor_resolved = _resolve_sensor_required(sensor_df.columns)
        yield_resolved = _resolve_yield_required(yield_df.columns, crop_name)
        sensor_missing = [label for label, col in sensor_resolved if col is None]
        yield_missing = [label for label, col in yield_resolved if col is None]
        missing_required = sensor_missing + yield_missing

        with st.expander("매핑 데이터 확인 · 필수 변수 매칭", expanded=bool(missing_required)):
            st.markdown(
                '<p class="map-legend"><b class="ok">초록</b> = 필수 변수 매핑됨 · '
                '<b class="miss">빨강</b> = 필수 변수 없음</p>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="map-sub" style="font-size:11px;font-weight:700;color:var(--ink-3);">환경센서 · 필수 변수</div>',
                unsafe_allow_html=True,
            )
            _render_mapping_chips(sensor_resolved)
            if sensor_missing:
                st.caption("누락: " + ", ".join(sensor_missing))

            st.markdown(
                '<div class="map-sub" style="font-size:11px;font-weight:700;color:var(--ink-3);margin-top:12px;">수확·생육 · 필수 변수</div>',
                unsafe_allow_html=True,
            )
            _render_mapping_chips(yield_resolved)
            if yield_missing:
                st.caption("누락: " + ", ".join(yield_missing))

        # 인식된 원본 컬럼도 참고용으로 표시
        with st.expander("원본 컬럼 목록", expanded=False):
            st.markdown(
                '<div class="map-sub" style="font-size:11px;font-weight:700;color:var(--ink-3);">환경센서</div>',
                unsafe_allow_html=True,
            )
            env_chips = [html.escape(str(c)) for c in sensor_df.columns]
            st.markdown(
                '<div class="mchips">' + "".join(f'<span class="mchip">{c}</span>' for c in env_chips) + "</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="map-sub" style="font-size:11px;font-weight:700;color:var(--ink-3);margin-top:12px;">수확·생육</div>',
                unsafe_allow_html=True,
            )
            yld_chips = [html.escape(str(c)) for c in yield_df.columns]
            st.markdown(
                '<div class="mchips">' + "".join(f'<span class="mchip">{c}</span>' for c in yld_chips) + "</div>",
                unsafe_allow_html=True,
            )

        manual_map = st.checkbox("컬럼이 맞지 않으면 직접 지정", key="dims_manual_map")
        if manual_map:
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                date_col_sensor = st.selectbox(
                    "센서 날짜",
                    sensor_df.columns,
                    index=core.pick_column_index(
                        sensor_df.columns, ["측정시간", "측정 일자", "날짜시간", "일시", "날짜"]
                    ),
                )
            with c2:
                temp_col = st.selectbox(
                    "온도",
                    sensor_df.columns,
                    index=core.pick_column_index(sensor_df.columns, ["온도_내부", "내부온도", "온도"]),
                )
            with c3:
                hum_col = st.selectbox(
                    "습도",
                    sensor_df.columns,
                    index=core.pick_column_index(sensor_df.columns, ["상대습도_내부", "습도_내부", "습도"]),
                )
            with c4:
                co2_options = list(sensor_df.columns)
                co2_idx = core.pick_column_index(sensor_df.columns, ["잔존CO2", "CO2", "CO₂"])
                # CO₂ 미인식 시에도 선택 가능하도록 유지
                co2_col = st.selectbox("CO₂", co2_options, index=co2_idx)
            with c5:
                solar_options = colmap.list_external_cumulative_solar_columns(sensor_df.columns)
                if not solar_options:
                    solar_options = sensor_df.columns.tolist()
                solar_col = st.selectbox(
                    "외부누적일사량",
                    solar_options,
                    index=colmap.pick_external_cumulative_solar_index(solar_options),
                )
            c6, c7, c8 = st.columns(3)
            with c6:
                date_col_yield = st.selectbox(
                    "조사일자",
                    yield_df.columns,
                    index=core.pick_column_index(yield_df.columns, ["조사일자", "날짜"]),
                )
            with c7:
                harvest_count_col = st.selectbox(
                    "수확수",
                    yield_df.columns,
                    index=core.pick_column_index(yield_df.columns, ["화방별수확수", "수확수"]),
                )
            with c8:
                harvest_weight_col = st.selectbox(
                    "착과수",
                    yield_df.columns,
                    index=core.pick_column_index(yield_df.columns, ["화방별착과수", "착과수"]),
                )
            growth_cols = {}
            for gf in growth_features:
                opts = [None] + yield_df.columns.tolist()
                idx = yield_df.columns.get_loc(gf) + 1 if gf in yield_df.columns else 0
                growth_cols[gf] = st.selectbox(gf, opts, index=idx, key=f"dims_gf_{gf}")

            # 직접 지정 시: 생육 필수 컬럼까지 모두 선택되어야 실행 가능
            manual_missing = [gf for gf, col in growth_cols.items() if not col]
            missing_required = manual_missing
            can_analyze = not manual_missing
        else:
            # 자동 매핑: 필수 변수가 모두 인식된 경우에만 사용 (누락 시 fallback 금지)
            sensor_map = dict(sensor_resolved)
            yield_map = dict(yield_resolved)
            date_col_sensor = sensor_map.get("측정일자")
            temp_col = sensor_map.get("온도")
            hum_col = sensor_map.get("습도")
            co2_col = sensor_map.get("CO₂")
            solar_col = sensor_map.get("외부누적일사량")
            date_col_yield = yield_map.get("조사일자")
            harvest_count_col = yield_map.get("수확수")
            harvest_weight_col = yield_map.get("착과수")
            growth_cols = {gf: yield_map.get(gf) for gf in growth_features}
            can_analyze = not missing_required

        mapping.update(
            {
                "sensor_df": sensor_df,
                "yield_df": yield_df,
                "growth_features": growth_features,
                "date_col_sensor": date_col_sensor,
                "temp_col": temp_col,
                "hum_col": hum_col,
                "co2_col": co2_col,
                "solar_col": solar_col,
                "date_col_yield": date_col_yield,
                "harvest_count_col": harvest_count_col,
                "harvest_weight_col": harvest_weight_col,
                "growth_cols": growth_cols,
                "can_analyze": can_analyze,
                "missing_required": missing_required,
            }
        )
    elif not has_data:
        if data_source_mode == "보안키 사용":
            st.markdown(
                '<div class="data-status-card">올바른 보안키를 입력하면 매핑 확인과 분석 실행이 가능합니다.</div>',
                unsafe_allow_html=True,
            )

    if has_data and missing_required:
        st.warning(
            "필수 변수가 모두 매핑되어야 분석을 실행할 수 있습니다. "
            f"누락: {', '.join(missing_required)}"
        )

    with st.container(key="data_run_card"):
        rb1, rb2, rb3 = st.columns([2, 1, 1], gap="large")
        with rb1:
            st.markdown(
                """
                <div class="data-run-copy">
                  <div class="data-run-title">분석 준비</div>
                  <div class="data-run-desc">환경 평균·예측에 쓸 최근 기간을 설정하세요.</div>
                  <div class="data-run-note">최근 N주 센서 평균으로 환경 상태를 계산합니다. 예: 7주 = 최근 49일.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with rb2:
            weeks_default = int(st.session_state.get("weeks", 7))
            weeks_default = max(3, min(12, weeks_default))
            weeks_val = st.number_input(
                "평균 계산 기간 (주)",
                min_value=3,
                max_value=12,
                value=weeks_default,
                key="dims_weeks",
                help=(
                    "최근 몇 주치 센서 데이터를 평균내 환경 상태를 볼지 정합니다. "
                    "예: 7주면 최근 49일 평균입니다. 예측 모델도 같은 주 단위를 사용합니다."
                ),
            )
            st.caption("최소 3주에서 최대 12주까지 설정 가능.")
            st.session_state.weeks = int(weeks_val)
        with rb3:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            run = st.button(
                "분석 결과 보기 →",
                type="primary",
                use_container_width=True,
                disabled=not can_analyze,
                key="dims_run_btn",
            )
            if run and can_analyze:
                st.session_state.dims_ready = True
                st.session_state.dims_show_complete_msg = True
                st.session_state.dims_goto_tab = MAIN_TAB_STATUS

    return mapping

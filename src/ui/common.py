"""Shared UI helpers for desktop tabs."""
from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from src.ui.styles import (
    APP_TITLE,
    APP_SUBTITLE,
    GROWTH_STAGES,
    STAGE_RECIPE,
    GROWTH_CHART_PRIMARY,
    GROWTH_CHART_EXTRA,
    MAIN_TAB_LABELS,
)

def _clamp(x, a, b):
    return max(a, min(b, x))


def read_uploaded_table(uploaded_file) -> pd.DataFrame:
    """업로드 파일(CSV · XLSX)을 DataFrame으로 읽기."""
    name = (uploaded_file.name or "").lower()
    if name.endswith(".xlsx"):
        return pd.read_excel(uploaded_file, engine="openpyxl")
    return pd.read_csv(uploaded_file)


def read_table_path(path: Path) -> pd.DataFrame:
    """로컬 CSV · XLSX 파일을 DataFrame으로 읽기."""
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(path, engine="openpyxl")
    return pd.read_csv(path)


def render_dims_header(asof_date: str, subtitle: str | None = None):
    sub = subtitle if subtitle is not None else APP_SUBTITLE
    sub_html = (
        f'<div class="dims-brand-sub">{html.escape(sub)}</div>'
        if sub
        else ""
    )
    st.markdown('<div class="dims-top-spacer" aria-hidden="true"></div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="dims-header">
          <div class="dims-header-row">
            <div class="dims-brand">
              <span class="dot"></span>
              <div class="dims-brand-text">
                <div class="dims-brand-title">{html.escape(APP_TITLE)}</div>
                {sub_html}
              </div>
            </div>
            <div class="dims-header-mid">
              <div class="dims-mid-title">생육·환경 의사결정</div>
              <div class="dims-mid-steps">
                <span>데이터 업로드</span>
                <span class="dims-mid-sep">→</span>
                <span>환경 설정</span>
                <span class="dims-mid-sep">→</span>
                <span>내 농가 진단</span>
                <span class="dims-mid-sep">→</span>
                <span>예측</span>
              </div>
            </div>
            <div class="dims-asof">
              <div class="dims-asof-label">최종 조사</div>
              <div class="dims-asof-value">{html.escape(str(asof_date))}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tab_hero(kicker: str, title: str, desc: str):
    """탭 상단 히어로 카드 (데이터/현황/환경관리/예측 공통)."""
    st.markdown(
        f"""
        <div class="data-hero">
          <div class="data-hero-kicker">{html.escape(kicker)}</div>
          <div class="data-head">
            <h1>{html.escape(title)}</h1>
            <p>{desc}</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_triage(message: str, status: str, icon: str = "🔔"):
    """흰색 알림 카드에서 환경 상태와 같은 색으로 변수명만 강조."""
    safe_status = status if status in ("risk", "warn", "ok") else "warn"
    st.markdown(
        f'<div class="triage {safe_status}">'
        f'<span>{icon}</span><div class="tt">{message}</div></div>',
        unsafe_allow_html=True,
    )


def _zone_to_status(zone: str) -> tuple[str, str]:
    if zone in ("최적구간", "중간구간"):
        return "ok", "양호"
    if zone in ("다습구간", "고온구간", "고온", "과다", "저온구간", "저습구간", "저광구간"):
        return "warn", zone.replace("구간", "")
    if zone in ("최고한계구간", "최저한계구간"):
        return "risk", zone.replace("구간", "")
    return "ok", "양호"


def build_env_kpis_from_row(row: pd.Series, week: int, core) -> list[dict]:
    specs = [
        ("누적 일사량", core.build_window_feature_name(week, "평균누적일사량(1일최대값기준)"), "", 0, 2500, 1200, 2000),
        ("주간 온도", core.build_window_feature_name(week, "평균주간온도(08~18시)"), "℃", 15, 30, 20, 24),
        ("야간 온도", core.build_window_feature_name(week, "평균야간온도(19~07시)"), "℃", 10, 25, 15, 18),
        ("주간 습도", core.build_window_feature_name(week, "평균주간습도(08~18시)"), "%", 40, 100, 60, 80),
        ("야간 습도", core.build_window_feature_name(week, "평균야간습도(19~07시)"), "%", 40, 100, 60, 80),
        ("잔존 CO₂", core.build_window_feature_name(week, "평균주간CO₂(08~18시)"), "ppm", 300, 900, 400, 800),
    ]
    kpis = []
    for name, col, unit, vmin, vmax, opt_lo, opt_hi in specs:
        val = float(row[col]) if col in row.index and pd.notna(row[col]) else np.nan
        if np.isnan(val):
            continue
        zone, _ = core.classify_environment_zone(col, val)
        status, label = _zone_to_status(zone)
        kpis.append({
            "name": name, "unit": unit, "val": val, "status": status, "label": label,
            "min": vmin, "max": vmax, "optLo": opt_lo, "optHi": opt_hi,
        })
    return kpis


def render_gauge_strip(kpis: list[dict]):
    if not kpis:
        st.info("환경 KPI를 계산할 데이터가 없습니다.")
        return
    parts = ['<section class="strip">']
    colors = {"ok": "var(--ok)", "warn": "var(--warn)", "risk": "var(--risk)"}
    for k in kpis:
        span = k["max"] - k["min"]
        pos = _clamp((k["val"] - k["min"]) / span * 100, 2, 98)
        o_l = _clamp((k["optLo"] - k["min"]) / span * 100, 0, 100)
        o_r = _clamp((k["optHi"] - k["min"]) / span * 100, 0, 100)
        o_w = max(0, o_r - o_l)
        c = colors[k["status"]]
        dev = ""
        unit = k["unit"]
        if k["val"] > k["optHi"]:
            delta = k["val"] - k["optHi"]
            dev = f'<div class="g-dev" style="left:{o_r}%;width:{_clamp(pos-o_r,0,100)}%;background:{c}"></div>'
            cmp_txt = f'(적정보다 {delta:.1f}{unit} 높음)'
            out = ""
        elif k["val"] < k["optLo"]:
            delta = k["optLo"] - k["val"]
            dev = f'<div class="g-dev" style="left:{pos}%;width:{_clamp(o_l-pos,0,100)}%;background:{c}"></div>'
            cmp_txt = f'(적정보다 {delta:.1f}{unit} 낮음)'
            out = ""
        else:
            cmp_txt = ""
            out = f'<div class="g-out" style="color:var(--ok);font-size:10.5px;font-weight:700;margin-top:7px;">적정 범위 안 ✓</div>'
        cmp_html = (
            f'<span class="u" style="margin-left:4px;color:{c};font-weight:700;">{cmp_txt}</span>'
            if cmp_txt
            else ""
        )
        val_fmt = (
            f'{k["val"]:,.1f}' if unit in ("℃", "%", "kPa")
            else f'{k["val"]:,.0f}'
        )
        hint = k.get("hint")
        hint_html = (
            f'<div style="font-size:10.5px;color:var(--ink-3);margin-top:6px;line-height:1.35;">{hint}</div>'
            if hint
            else ""
        )
        parts.append(f"""
        <div class="kpi">
          <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
            <span class="kpi-name">{k["name"]}</span>
            <span class="badge {k["status"]}">{k["label"]}</span>
          </div>
          <div class="kpi-val"><span class="v">{val_fmt}</span><span class="u">{unit}</span>{cmp_html}</div>
          <div class="g-track">
            <div class="g-opt" style="left:{o_l}%;width:{o_w}%"></div>{dev}
            <div class="g-pin" style="left:{pos}%;background:{c}"></div>
          </div>
          <div style="display:flex;justify-content:space-between;font-size:10px;color:var(--ink-3);margin-top:10px;">
            <span>{k["min"]}</span><span style="font-weight:700;color:var(--ok)">적정 {k["optLo"]}~{k["optHi"]}</span><span>{k["max"]}</span>
          </div>{out}{hint_html}
        </div>""")
    parts.append("</section>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def _status_from_opt_range(val: float, opt_lo: float, opt_hi: float, env_key: str = "") -> tuple[str, str]:
    if opt_lo <= val <= opt_hi:
        return "ok", "양호"
    if val > opt_hi:
        if env_key == "일사량":
            return "risk", "최고한계"
        status = "risk" if env_key == "야간습도" else "warn"
        return status, "높음"
    return "warn", "낮음"


def build_env_kpis_from_measures(
    measures: dict[str, float],
    optimal_ranges: dict[str, tuple[float, float]] | None = None,
) -> list[dict]:
    specs = [
        ("누적 일사량", "일사량", "", 0, 2500, 1200, 2000),
        ("주간 온도", "주간온도", "℃", 15, 30, 20, 24),
        ("야간 온도", "야간온도", "℃", 10, 25, 15, 18),
        ("주간 습도", "주간습도", "%", 40, 100, 60, 80),
        ("야간 습도", "야간습도", "%", 40, 100, 60, 80),
        ("잔존 CO₂", "주간CO2", "ppm", 300, 900, 400, 800),
    ]
    kpis = []
    optimal_ranges = optimal_ranges or {}
    for name, key, unit, vmin, vmax, opt_lo, opt_hi in specs:
        val = measures.get(key)
        if val is None or (isinstance(val, float) and np.isnan(val)):
            continue
        override = optimal_ranges.get(key)
        if override is not None:
            range_lo, range_hi = override
            if np.isfinite(range_lo) and np.isfinite(range_hi) and range_lo <= range_hi:
                opt_lo, opt_hi = float(range_lo), float(range_hi)
                vmin = min(vmin, opt_lo, float(val))
                vmax = max(vmax, opt_hi, float(val))
        status, label = _status_from_opt_range(float(val), opt_lo, opt_hi, key)
        if opt_lo <= float(val) <= opt_hi:
            label = "양호"
        elif float(val) > opt_hi:
            if key == "야간습도":
                label = "다습"
            elif key in ("주간온도", "야간온도"):
                label = "고온"
            elif key == "일사량":
                label = "최고한계"
            else:
                label = "높음"
            if key == "야간습도" and status == "risk":
                status = "warn"
        else:
            label = "낮음"
        kpis.append({
            "name": name, "unit": unit, "val": float(val), "status": status, "label": label,
            "min": vmin, "max": vmax, "optLo": opt_lo, "optHi": opt_hi,
        })
    return kpis


def rda_environment_ranges_from_rec(match_row: dict | pd.Series | None) -> dict[str, tuple[float, float]]:
    """농진청 비교표의 권장 범위를 환경 KPI 키로 변환."""
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
        value = match_row.get(rda_col) if isinstance(match_row, dict) else match_row.get(rda_col)
        lo, hi = parse_range(value)
        if lo is not None and hi is not None:
            ranges[env_key] = (lo, hi)
    return ranges


def _alert_priority_kpis(kpis: list[dict]) -> list[dict]:
    """상단 알림 순서 — 심각도(위험→주의) 우선, 같으면 주요 항목 순."""
    name_order = {
        "누적 일사량": 0,
        "주간 온도": 1,
        "야간 온도": 2,
        "주간 습도": 3,
        "야간 습도": 4,
        "잔존 CO₂": 5,
    }
    severity_order = {"risk": 0, "warn": 1}
    flagged = [k for k in kpis if k["status"] != "ok"]
    return sorted(
        flagged,
        key=lambda k: (
            severity_order.get(k["status"], 9),
            name_order.get(k["name"], 9),
        ),
    )


def _sort_env_kpis(kpis: list[dict]) -> list[dict]:
    order = {"risk": 0, "warn": 1, "ok": 2}
    return sorted(kpis, key=lambda k: order.get(k["status"], 9))


def _format_kpi_value(k: dict) -> str:
    if k["unit"] in ("℃", "%"):
        return f'{k["val"]:.1f}{k["unit"]}'
    if k["unit"] == "ppm":
        return f'{k["val"]:.0f}{k["unit"]}'
    return f'{k["val"]:.1f}'


def _env_primary_alert(k: dict) -> str:
    if k["val"] > k["optHi"]:
        detail = "적정 구간을 초과했습니다"
    elif k["val"] < k["optLo"]:
        detail = "적정 구간보다 낮습니다"
    else:
        detail = f'{k["label"]} 상태입니다'
    name = str(k["name"])
    last = ord(name[-1]) if name else 0
    has_final_consonant = 0xAC00 <= last <= 0xD7A3 and (last - 0xAC00) % 28 != 0
    particle = "이" if has_final_consonant else "가"
    return f'오늘 꼭 볼 것 — <b>{name}</b>{particle} {detail}. 환경 제어를 점검하세요.'


def _env_secondary_alert(kpis: list[dict]) -> str:
    """주의 항목을 하나의 알림으로 묶음 (이름만, 수치 제외)."""
    names = [k["name"] for k in kpis if k.get("name")]
    joined = ", ".join(f"<b>{n}</b>" for n in names)
    return f"이상 지속 알림 — {joined} 상태가 지속되고 있습니다."


def build_status_env_kpis(
    sensor_df=None,
    date_col_sensor=None,
    temp_col=None,
    hum_col=None,
    solar_col=None,
    co2_col=None,
    latest_row=None,
    selected_week: int = 7,
    core=None,
    yield_df=None,
    date_col_yield=None,
    optimal_ranges: dict[str, tuple[float, float]] | None = None,
) -> list[dict]:
    """현황 탭 환경 KPI.

    환경관리 탭에서 「조회」 후 저장된 KPI가 있으면
    「지금 환경 상태」 게이지와 동일한 기준·값을 사용한다.
    """
    cached = st.session_state.get("status_env_kpis")
    if st.session_state.get("rda_env_detail_show") and cached:
        return list(cached)

    days = max(1, int(selected_week) * 7)
    if optimal_ranges is None:
        optimal_ranges = {}
        if st.session_state.get("rda_env_detail_show"):
            optimal_ranges = rda_environment_ranges_from_rec(
                st.session_state.get("rda_last_environment_rec")
            )
    if sensor_df is not None and date_col_sensor and temp_col:
        measures = build_recent_env_measures(
            sensor_df,
            date_col_sensor,
            temp_col,
            hum_col,
            solar_col,
            co2_col=co2_col,
            days=days,
            solar_override=st.session_state.get("rda_last_solar_q")
            if st.session_state.get("rda_env_detail_show")
            else None,
        )
        if measures:
            return build_env_kpis_from_measures(measures, optimal_ranges=optimal_ranges)
    if latest_row is not None and core is not None:
        return build_env_kpis_from_row(latest_row, selected_week, core)
    return []


def _yield_cumulative_totals(
    yield_df,
    date_col_yield,
    harvest_count_col,
    harvest_weight_col,
    growth_cols,
) -> tuple[int, int]:
    chart = build_growth_chart_df(
        yield_df, date_col_yield, harvest_count_col, harvest_weight_col, growth_cols
    )
    harvest_total = int(pd.to_numeric(chart["수확수"], errors="coerce").fillna(0).sum()) if "수확수" in chart.columns else 0
    fruit_total = int(pd.to_numeric(chart["착과수"], errors="coerce").fillna(0).sum()) if "착과수" in chart.columns else 0
    return harvest_total, fruit_total


def build_recent_env_measures(
    sensor_df,
    date_col: str,
    temp_col: str,
    hum_col: str | None,
    solar_col: str | None,
    co2_col: str | None = None,
    days: int = 7,
    solar_override: float | None = None,
) -> dict[str, float]:
    from src.rda_standards import build_rda_recent_actuals

    measures = build_rda_recent_actuals(
        sensor_df, date_col, temp_col, solar_col, days=days, solar_override=solar_override
    )
    if sensor_df is None or date_col not in sensor_df.columns:
        return measures
    if hum_col and hum_col in sensor_df.columns:
        subset_h = sensor_df[[date_col, hum_col]].copy()
        subset_h[date_col] = pd.to_datetime(subset_h[date_col], errors="coerce")
        subset_h[hum_col] = pd.to_numeric(subset_h[hum_col], errors="coerce")
        subset_h = subset_h.dropna()
        if not subset_h.empty:
            subset_h["hour"] = subset_h[date_col].dt.hour
            latest_h = subset_h[date_col].max()
            start_h = pd.Timestamp(latest_h.date()) - pd.Timedelta(days=days - 1)
            sub_h = subset_h[subset_h[date_col] >= start_h]
            day_h = sub_h[(sub_h["hour"] >= 8) & (sub_h["hour"] <= 18)]
            night_h = sub_h[(sub_h["hour"] >= 19) | (sub_h["hour"] <= 7)]
            if not day_h[hum_col].empty:
                measures["주간습도"] = float(day_h[hum_col].mean())
            if not night_h[hum_col].empty:
                measures["야간습도"] = float(night_h[hum_col].mean())
    if co2_col and co2_col in sensor_df.columns:
        subset_c = sensor_df[[date_col, co2_col]].copy()
        subset_c[date_col] = pd.to_datetime(subset_c[date_col], errors="coerce")
        subset_c[co2_col] = pd.to_numeric(subset_c[co2_col], errors="coerce")
        subset_c = subset_c.dropna()
        if not subset_c.empty:
            subset_c["hour"] = subset_c[date_col].dt.hour
            latest_c = subset_c[date_col].max()
            start_c = pd.Timestamp(latest_c.date()) - pd.Timedelta(days=days - 1)
            sub_c = subset_c[subset_c[date_col] >= start_c]
            day_c = sub_c[(sub_c["hour"] >= 8) & (sub_c["hour"] <= 18)]
            if not day_c[co2_col].empty:
                measures["주간CO2"] = float(day_c[co2_col].mean())
    return measures


def _calc_vpd_kpa(temp_c: float, rh_pct: float) -> float:
    svp = 0.6108 * np.exp(17.27 * temp_c / (temp_c + 237.3))
    return float(svp * (1.0 - rh_pct / 100.0))


def build_control_quality_from_sensor(
    sensor_df,
    date_col: str,
    temp_col: str,
    hum_col: str | None,
    days: int = 7,
) -> dict | None:
    if sensor_df is None or not date_col or not temp_col or not hum_col:
        return None
    if hum_col not in sensor_df.columns or temp_col not in sensor_df.columns:
        return None
    tmp = sensor_df[[date_col, temp_col, hum_col]].copy()
    tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
    tmp[temp_col] = pd.to_numeric(tmp[temp_col], errors="coerce")
    tmp[hum_col] = pd.to_numeric(tmp[hum_col], errors="coerce")
    tmp = tmp.dropna()
    if tmp.empty:
        return None
    tmp["hour"] = tmp[date_col].dt.hour
    tmp["date"] = tmp[date_col].dt.date
    latest_date = tmp["date"].max()
    start = pd.Timestamp(latest_date) - pd.Timedelta(days=days - 1)
    subset = tmp[tmp[date_col] >= start]
    if subset.empty:
        return None

    night = subset[(subset["hour"] >= 19) | (subset["hour"] <= 7)]
    day = subset[(subset["hour"] >= 8) & (subset["hour"] <= 18)]

    night_hum_oos_pct = None
    night_vpd = None
    if not night.empty:
        out = (night[hum_col] > 80) | (night[hum_col] < 60)
        night_hum_oos_pct = float(out.mean() * 100)
        night_vpd = float(night.apply(lambda r: _calc_vpd_kpa(r[temp_col], r[hum_col]), axis=1).mean())

    swing_days = 0
    if not day.empty:
        daily = day.groupby("date")[temp_col].agg(["min", "max"])
        swing_days = int((daily["max"] - daily["min"] > 5).sum())

    return {
        "night_hum_oos_pct": night_hum_oos_pct,
        "night_vpd": night_vpd,
        "day_temp_swing_days": swing_days,
        "days": days,
    }


def build_control_quality_kpis(stats: dict) -> list[dict]:
    """제어 품질 지표 → 게이지(KPI) 형식."""
    kpis: list[dict] = []
    days = int(stats.get("days") or 7)
    oos = stats.get("night_hum_oos_pct")
    vpd = stats.get("night_vpd")
    swings = int(stats.get("day_temp_swing_days") or 0)

    if oos is not None:
        if oos >= 50:
            status, label = "risk", "주의"
        elif oos >= 30:
            status, label = "warn", "보통"
        else:
            status, label = "ok", "양호"
        kpis.append({
            "name": "적정 이탈 시간",
            "unit": "%",
            "val": float(oos),
            "status": status,
            "label": label,
            "min": 0,
            "max": 100,
            "optLo": 0,
            "optHi": 30,
            "hint": "야간습도가 적정(60~80%)을 벗어난 시간 비율",
        })

    if vpd is not None:
        if 0.6 <= vpd <= 1.2:
            status, label = "ok", "양호"
        elif vpd < 0.6:
            status, label = "warn", "낮음"
        else:
            status, label = "warn", "높음"
        kpis.append({
            "name": "야간 VPD",
            "unit": "kPa",
            "val": float(vpd),
            "status": status,
            "label": label,
            "min": 0,
            "max": max(2.0, float(vpd) * 1.15),
            "optLo": 0.6,
            "optHi": 1.2,
            "hint": "수증기압차 · 토마토 제어 품질 핵심 지표",
        })

    if swings >= 3:
        status, label = "warn", "보통"
    else:
        status, label = "ok", "양호"
    kpis.append({
        "name": "환경 안정성",
        "unit": "회",
        "val": float(swings),
        "status": status,
        "label": label,
        "min": 0,
        "max": max(days, swings, 1),
        "optLo": 0,
        "optHi": 2,
        "hint": "주간온도 급변 횟수(일교차 5℃ 초과 일수)",
    })
    return kpis


def render_control_quality_stats(stats: dict):
    kpis = build_control_quality_kpis(stats)
    if not kpis:
        return
    days = int(stats.get("days") or 7)
    render_gauge_strip(kpis)
    st.markdown(
        f'<p class="subnote">※ 최근 {days}일 기준. 한 시점 값이 아니라 ‘얼마나 오래·안정적으로 적정을 유지했는가’를 봅니다. '
        f"VPD는 수증기압차로, 토마토 제어 품질의 핵심 지표입니다.</p>",
        unsafe_allow_html=True,
    )


def render_env_detail_section(
    kpis: list[dict] | None,
    sensor_df=None,
    date_col: str | None = None,
    temp_col: str | None = None,
    hum_col: str | None = None,
    context_note: str | None = None,
):
    """지금 값·적정 구간·제어 품질."""
    st.markdown(
        '<div class="eyebrow">Env · <span class="ko">환경 상세 — 지금 값·적정 구간·제어 품질</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="eyebrow" style="margin-top:4px;">Now · <span class="ko">지금 환경 상태 — 지금 값(●)과 적정 구간(초록)</span></div>',
        unsafe_allow_html=True,
    )
    if kpis:
        render_gauge_strip(kpis)
    else:
        st.info("환경센서 데이터 업로드 후 「분석 결과 보기」를 실행하면 지금 환경 상태를 확인할 수 있습니다.")

    note = context_note or (
        "※ 적정 구간은 작기 전체 기준입니다. "
        "<b style=\"color:var(--ink-2)\">농진청 표준 조회</b> 결과와 함께 현재 생육단계 목표 환경을 확인하세요."
    )
    st.markdown(f'<p class="subnote">{note}</p>', unsafe_allow_html=True)

    st.markdown(
        '<div class="eyebrow">Control · <span class="ko">환경 제어가 잘 되고 있나 — 지금 값(●)과 적정 구간(초록)</span></div>',
        unsafe_allow_html=True,
    )
    control = build_control_quality_from_sensor(sensor_df, date_col, temp_col, hum_col)
    if control:
        render_control_quality_stats(control)
    else:
        st.caption("온도·습도 센서 데이터가 있으면 최근 7일 제어 품질을 함께 표시합니다.")


def render_action_item(title, why, desc, urgency, color):
    st.markdown(
        f"""
        <div class="card act">
          <div class="act-body">
            <div class="h">{title} <span style="font-weight:600;font-size:12px;color:var(--ink-3);margin-left:8px;">{why}</span></div>
            <div class="d">{desc}</div>
          </div>
          <div class="act-right"><div style="font-size:10.5px;color:var(--ink-3);font-weight:600;">시급도</div>
          <div class="imp" style="color:{color};">{urgency}</div></div>
        </div>""",
        unsafe_allow_html=True,
    )


def render_stage_bar(n_points: int = None):
    """생육단계 바 — 7구간 타임라인(1:2:2:2) 기준으로 항상 100% 너비."""
    _ = n_points
    spans = [stg["e"] - stg["s"] + 1 for stg in GROWTH_STAGES]
    total = sum(spans)  # 7
    segs = []
    for i, stg in enumerate(GROWTH_STAGES):
        w = spans[i] / total * 100
        cls = "stage-seg stage-seg--s1" if i == 0 else "stage-seg"
        segs.append(
            f'<div class="{cls}" style="width:{w:.6f}%;min-width:{w:.6f}%;background:{stg["color"]}">{stg["name"]}</div>'
        )
    st.markdown(f'<div class="stage-bar">{"".join(segs)}</div>', unsafe_allow_html=True)



def render_recipe_table(measures: dict[str, float]):
    rows = []
    for env, (lo, hi) in STAGE_RECIPE.items():
        val = measures.get(env)
        if val is None or np.isnan(val):
            continue
        if lo <= val <= hi:
            judge, jcls = "양호", "ok"
        elif val > hi:
            judge, jcls = "높음 ↑", "warn" if env != "야간습도" else "risk"
        else:
            judge, jcls = "낮음 ↓", "warn"
        unit = "℃" if "온도" in env else ("%" if "습도" in env else "")
        rows.append(
            f"<tr><td>{env}</td><td>{lo}~{hi}{unit}</td>"
            f'<td style="font-weight:600;">{val:.1f}{unit}</td>'
            f'<td class="judge {jcls}">{judge}</td></tr>'
        )
    if rows:
        st.markdown(
            f'<div class="card"><table class="stage-tbl"><tr><th>환경</th><th>권장 (예시)</th><th>최근 실측</th><th>판정</th></tr>{"".join(rows)}</table></div>',
            unsafe_allow_html=True,
        )


def build_actions_from_kpis(kpis: list[dict]) -> list[dict]:
    """위험·주의 KPI마다 개선 방향 1건을 생성한다."""
    advice = {
        "누적 일사량": {
            "high": (
                "일사량 차광·엽온 관리",
                "차광 스크린·환기·세무 냉방으로 정오 전후 엽온 상승을 억제하세요.",
            ),
            "low": (
                "일사량 확보",
                "과도한 차광을 줄이고 측창·피복 상태를 점검해 광량을 확보하세요.",
            ),
        },
        "주간 온도": {
            "high": (
                "주간 온도 완화",
                "정오 환기 강화로 적정 온도 구간으로 복귀시키세요.",
            ),
            "low": (
                "주간 온도 확보",
                "난방·보온 커튼으로 주간 저온을 보완하세요.",
            ),
        },
        "야간 온도": {
            "high": (
                "야간 온도 관리",
                "야간 환기로 권장 온도 구간을 유지하세요.",
            ),
            "low": (
                "야간 온도 확보",
                "야간 난방·보온으로 저온 스트레스를 줄이세요.",
            ),
        },
        "주간 습도": {
            "high": (
                "주간 습도 조절",
                "환기·제습으로 과습을 낮춰 병해 위험을 줄이세요.",
            ),
            "low": (
                "주간 습도 확보",
                "포그·관수로 과도한 건조를 완화하세요.",
            ),
        },
        "야간 습도": {
            "high": (
                "야간 제습·환기",
                "난방배관·환기로 야간 결로를 차단하고 관수량을 점검하세요.",
            ),
            "low": (
                "야간 습도 확보",
                "야간 건조가 심하면 관수·가습으로 적정 습도를 유지하세요.",
            ),
        },
        "잔존 CO₂": {
            "high": (
                "CO₂ 농도 조절",
                "환기를 늘려 과도한 CO₂ 축적을 완화하세요.",
            ),
            "low": (
                "CO₂ 시비 점검",
                "CO₂ 공급량·타이밍을 점검해 광합성에 필요한 농도를 확보하세요.",
            ),
        },
    }
    urgency_map = {
        "risk": ("시급", "var(--risk)"),
        "warn": ("보통", "var(--warn)"),
    }
    actions = []
    for k in _alert_priority_kpis(kpis):
        direction = "high" if k["val"] > k["optHi"] else "low"
        pair = advice.get(k["name"], {}).get(direction)
        if pair is None:
            title = f'{k["name"]} 점검'
            desc = "적정 구간을 벗어나 있으니 환경 제어 설정을 확인하세요."
        else:
            title, desc = pair
        urgency, color = urgency_map.get(k["status"], ("보통", "var(--warn)"))
        why = f'{k["name"]} {_format_kpi_value(k)} ({k["label"]})'
        actions.append(
            {"title": title, "why": why, "desc": desc, "urgency": urgency, "color": color}
        )
    return actions


def render_disclaimer():
    from datetime import datetime

    year = datetime.now().year
    st.markdown(
        """
        <div class="disclaimer"><span>ℹ️</span>
        <div class="dt"><b>참고용 안내.</b> 이 대시보드의 진단·예측·제안은 과거 데이터로 학습한 통계 모델의 추정 결과입니다.
        실제 정답이 아니며 오차가 있을 수 있습니다. <b>현장 관찰과 전문가 판단을 우선하고, 본 결과는 의사결정의 참고 자료로만 활용하세요.</b></div></div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="copyright">
          <div>© {year} <b>PublicAI</b> (PublicAI Inc.). All rights reserved.</div>
          <div style="margin-top:6px;">본 시스템의 소스코드, UI, 분석 결과 및 관련 자료에 대한 저작권은 해당 권리자에게 있으며, 무단 복제·전송·배포·상업적 이용을 금합니다.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _plotly_timeseries(
    df,
    x_col,
    y_col,
    title,
    color="#4E79A7",
    standard_df: pd.DataFrame | None = None,
):
    plot_df = df[[x_col, y_col]].copy()
    plot_df[x_col] = pd.to_datetime(plot_df[x_col], errors="coerce")
    plot_df[y_col] = pd.to_numeric(plot_df[y_col], errors="coerce")
    plot_df = plot_df.dropna().sort_values(x_col)
    if plot_df.empty:
        return None
    dark_mode = bool(st.session_state.get("dark_mode", False))
    paper_color = "#1F2937" if dark_mode else "#FFFFFF"
    plot_color = "#111827" if dark_mode else "#F7F8FA"
    text_color = "#F3F4F6" if dark_mode else "#243240"
    grid_color = "#374151" if dark_mode else "#EEF1F5"
    line_color = "#4B5563" if dark_mode else "#D7DDE4"
    fig = go.Figure()
    if standard_df is not None and not standard_df.empty and {"p25", "p50", "p75"}.issubset(standard_df.columns):
        std = standard_df.copy()
        std[x_col] = pd.to_datetime(std[x_col], errors="coerce")
        std = std.dropna(subset=[x_col, "p50"]).sort_values(x_col)
        if not std.empty:
            fig.add_trace(go.Scatter(
                x=std[x_col], y=std["p75"], mode="lines",
                line=dict(width=0), showlegend=False, hoverinfo="skip",
            ))
            fig.add_trace(go.Scatter(
                x=std[x_col], y=std["p25"], mode="lines",
                line=dict(width=0), fill="tonexty",
                fillcolor="rgba(78, 121, 167, 0.18)",
                name="선도 범위 (p25~p75)", hoverinfo="skip",
            ))
            fig.add_trace(go.Scatter(
                x=std[x_col], y=std["p50"], mode="lines",
                line=dict(color="#8A97A4", width=2, dash="dash"),
                name="선도 중앙값 (p50)",
            ))
    fig.add_trace(go.Scatter(
        x=plot_df[x_col], y=plot_df[y_col], mode="lines+markers",
        line=dict(color=color, width=2), marker=dict(size=5),
        name="내 농가",
    ))
    fig.update_layout(
        title=title, height=220, margin=dict(l=40, r=10, t=36, b=30),
        template="plotly_dark" if dark_mode else "plotly_white",
        showlegend=standard_df is not None and not standard_df.empty,
        legend=dict(
            orientation="h",
            xanchor="right",
            x=1,
            yanchor="bottom",
            y=1.02,
            font=dict(size=10),
        ),
        paper_bgcolor=paper_color, plot_bgcolor=plot_color,
        font=dict(family="Pretendard, sans-serif", size=11, color=text_color),
    )
    fig.update_xaxes(gridcolor=grid_color, linecolor=line_color)
    fig.update_yaxes(gridcolor=grid_color, linecolor=line_color)
    return fig


def build_growth_chart_df(
    source_df,
    date_col: str = "조사일자",
    harvest_count_col: str | None = None,
    harvest_weight_col: str | None = None,
    growth_cols: dict[str, str | None] | None = None,
) -> pd.DataFrame:
    """업로드 생육·수확 파일을 조사일자별 실측 차트용 DataFrame으로 정리."""
    if source_df is None or source_df.empty:
        return pd.DataFrame()

    frame = source_df.copy()
    dcol = date_col if date_col in frame.columns else "조사일자"
    if dcol != "조사일자" and dcol in frame.columns:
        frame = frame.rename(columns={dcol: "조사일자"})
    if "조사일자" not in frame.columns:
        return pd.DataFrame()

    frame["조사일자"] = pd.to_datetime(frame["조사일자"], errors="coerce")
    frame = frame.dropna(subset=["조사일자"])
    if frame.empty:
        return pd.DataFrame()

    sum_cols: list[str] = []
    mean_cols: list[str] = []

    if "수확수" in frame.columns:
        frame["수확수"] = pd.to_numeric(frame["수확수"], errors="coerce")
        sum_cols.append("수확수")
    elif harvest_count_col and harvest_count_col in frame.columns:
        frame["수확수"] = pd.to_numeric(frame[harvest_count_col], errors="coerce")
        sum_cols.append("수확수")

    if "착과수" in frame.columns:
        frame["착과수"] = pd.to_numeric(frame["착과수"], errors="coerce")
        sum_cols.append("착과수")
    elif harvest_weight_col and harvest_weight_col in frame.columns:
        frame["착과수"] = pd.to_numeric(frame[harvest_weight_col], errors="coerce")
        sum_cols.append("착과수")

    for gf, src in (growth_cols or {}).items():
        col = gf if gf in frame.columns else src
        if not col or col not in frame.columns:
            continue
        frame[gf] = pd.to_numeric(frame[col], errors="coerce")
        if gf not in mean_cols:
            mean_cols.append(gf)

    for gf in ["초장", "생장길이", "엽수", "엽장", "엽폭", "줄기굵기", "화방높이"]:
        if gf in frame.columns and gf not in mean_cols:
            frame[gf] = pd.to_numeric(frame[gf], errors="coerce")
            mean_cols.append(gf)

    agg: dict[str, str] = {c: "sum" for c in sum_cols}
    for c in mean_cols:
        if c not in agg:
            agg[c] = "mean"
    if not agg:
        return pd.DataFrame()

    frame["_chart_date"] = frame["조사일자"].dt.normalize()
    out = frame.groupby("_chart_date", as_index=False).agg(agg)
    out = out.rename(columns={"_chart_date": "조사일자"})
    return out.sort_values("조사일자")


def _focus_main_tab(tab_index: int):
    """메인 탭 바에서 지정 인덱스 탭으로 이동."""
    import streamlit.components.v1 as components

    idx = max(0, min(tab_index, len(MAIN_TAB_LABELS) - 1))
    components.html(
        f"""
        <script>
        (function() {{
          const go = () => {{
            const doc = window.parent.document;
            const lists = doc.querySelectorAll('[data-testid="stTabs"] [data-baseweb="tab-list"]');
            if (!lists.length) return false;
            const buttons = lists[0].querySelectorAll('button[data-baseweb="tab"]');
            const target = buttons[{idx}];
            if (!target) return false;
            if (target.getAttribute('aria-selected') !== 'true') target.click();
            window.parent.scrollTo({{ top: 0, behavior: 'smooth' }});
            return true;
          }};
          if (!go()) setTimeout(go, 120);
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def render_growth_timeseries_section(df, date_col: str = "조사일자", key_prefix: str = "growth"):
    """생육·수확 시계열 차트 — 업로드 실측 + 선도 농가(총출하량 상위10) 표준."""
    from src import core
    from src.growth_standards import build_growth_standard_curves

    if df is None or df.empty:
        return

    plot_df = df.copy()
    if date_col != "조사일자" and date_col in plot_df.columns:
        plot_df = plot_df.rename(columns={date_col: "조사일자"})
    if "조사일자" not in plot_df.columns:
        return

    plot_df["조사일자"] = pd.to_datetime(plot_df["조사일자"], errors="coerce")
    plot_df = plot_df.dropna(subset=["조사일자"]).sort_values("조사일자")
    if plot_df.empty:
        return

    plot_cols = [c for c in GROWTH_CHART_PRIMARY if c in plot_df.columns]
    plot_cols += [c for c in GROWTH_CHART_EXTRA if c in plot_df.columns and c not in plot_cols]
    if not plot_cols:
        return

    upload_start = plot_df["조사일자"].min()
    upload_end = plot_df["조사일자"].max()
    max_rel_day = int((upload_end - upload_start).days) + 7
    standard_curves, _n_ref_farms = build_growth_standard_curves(upload_start, max_rel_day=max_rel_day)

    st.markdown(
        '<div class="eyebrow">Growth · <span class="ko">생육·수확이 어떻게 커왔나</span></div>',
        unsafe_allow_html=True,
    )
    st.info(
        "안내: 선도 기준은 총출하량 상위 10개 농가이며, 비교할 때 정식 시기가 "
        "유사한 농가에 더 높은 가중치를 적용합니다."
    )
    colors = {
        "착과수": "#4E79A7", "초장": "#59A14F", "엽수": "#59A14F", "수확수": "#E15759",
        "생장길이": "#76B7B2", "엽장": "#B07AA1", "엽폭": "#9C755F", "줄기굵기": "#EDC948", "화방높이": "#AF7AA1",
    }
    plot_df = plot_df.sort_values("조사일자")
    st.markdown('<div class="chart-grid">', unsafe_allow_html=True)
    for i in range(0, len(plot_cols), 2):
        cols = st.columns(2, gap="medium")
        for j, col_name in enumerate(plot_cols[i : i + 2]):
            with cols[j]:
                std_df = standard_curves.get(col_name)
                fig = _plotly_timeseries(
                    plot_df, "조사일자", col_name, col_name,
                    colors.get(col_name, "#4E79A7"),
                    standard_df=std_df,
                )
                if fig:
                    core.display_plotly(fig, key=f"{key_prefix}_{col_name}")
    st.markdown("</div>", unsafe_allow_html=True)


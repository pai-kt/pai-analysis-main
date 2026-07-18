"""Tab 2 · 현황."""
from __future__ import annotations

import streamlit as st

from src.ui.common import (
    _alert_priority_kpis,
    _env_primary_alert,
    _env_secondary_alert,
    _format_kpi_value,
    _sort_env_kpis,
    build_actions_from_kpis,
    render_action_item,
    render_growth_timeseries_section,
    render_triage,
)


def _sort_growth_kpis(kpis: list[dict]) -> list[dict]:
    order = {"높음": 0, "적정": 1, "낮음": 2}
    return sorted(kpis, key=lambda k: order.get(k.get("label"), 9))


def _growth_tag_class(label: str) -> str:
    if label == "높음":
        return "high"
    if label == "낮음":
        return "low"
    return "ok"


def render_status_tab(
    *,
    dims_ready: bool,
    has_data: bool,
    env_kpis: list[dict],
    growth_summary: dict | None,
    growth_chart_df,
    harvest_total: int = 0,
    fruit_total: int = 0,
    env_weeks: int = 7,
):
    """현황 탭 본문."""
    if not has_data:
        st.info("데이터 탭에서 보안키 또는 파일 업로드 중 하나를 선택한 뒤 「분석 결과 보기」를 실행하세요.")
        return

    if not dims_ready:
        st.info("데이터 탭에서 매핑을 확인한 뒤 「분석 결과 보기」를 누르면 탭이 열립니다.")

    env_weeks = max(3, min(12, int(env_weeks)))
    env_days = env_weeks * 7
    if growth_summary is None:
        growth_summary = {
            "pill_warn": False,
            "pill_label": "—",
            "headline": "생육 상태를 확인하세요.",
            "desc": "",
            "stat_note": "—",
            "stat_value": "—",
            "growth_kpis": [],
            "n_high": 0,
            "n_low": 0,
            "n_ok": 0,
            "leading_harvest_total": None,
            "leading_fruit_total": None,
        }

    alert_kpis = _alert_priority_kpis(env_kpis)
    risk_kpis = [k for k in alert_kpis if k["status"] == "risk"]
    warn_kpis = [k for k in alert_kpis if k["status"] == "warn"]
    n_risk = len([k for k in env_kpis if k["status"] == "risk"])
    n_warn = len([k for k in env_kpis if k["status"] == "warn"])

    st.info(
        "안내: 선도 기준은 총출하량 상위 10개 농가이며, 비교할 때 정식 시기가 "
        "유사한 농가에 더 높은 가중치를 적용합니다."
    )

    for kpi in risk_kpis:
        render_triage(
            _env_primary_alert(kpi),
            status=kpi["status"],
        )
    if warn_kpis:
        render_triage(
            _env_secondary_alert(warn_kpis),
            status="warn",
            icon="⏱️",
        )

    g_high = int(growth_summary.get("n_high") or 0)
    g_low = int(growth_summary.get("n_low") or 0)
    g_ok = int(growth_summary.get("n_ok") or 0)
    growth_kpis = growth_summary.get("growth_kpis") or []

    if growth_kpis:
        growth_tags = "".join(
            f'<span class="tag {_growth_tag_class(k["label"])}">{k["text"]}</span>'
            for k in _sort_growth_kpis(growth_kpis)
        )
    else:
        growth_tags = '<span class="tag w">생육·수확 데이터 없음</span>'

    if env_kpis:
        env_tags = "".join(
            f'<span class="tag {"r" if k["status"]=="risk" else "w" if k["status"]=="warn" else "ok"}">'
            f'{k["name"]} {_format_kpi_value(k)} · {k["label"]}</span>'
            for k in _sort_env_kpis(env_kpis)[:6]
        )
    else:
        env_tags = '<span class="tag w">환경센서 데이터 없음</span>'

    st.markdown(
        f"""
        <div class="hero-grid">
          <div class="card growth-card">
            <h2 style="font-size:18px;font-weight:700;color:var(--ink);">{growth_summary["headline"]}</h2>
            <div style="font-size:12px;color:var(--ink-3);margin-top:8px;">
              생육 <b style="color:var(--warn);">{g_high} 높음</b> ·
              <b style="color:var(--ok);">{g_ok} 적정</b> ·
              <b style="color:var(--accent);">{g_low} 낮음</b>
            </div>
            <div class="card-body" style="margin-top:12px;">{growth_tags}</div>
            <div style="margin-top:auto;padding-top:10px;font-size:11.5px;color:var(--ink-3);">선도 농가 표준(p25~p75) 대비 최근 조사</div>
          </div>
          <div class="card verdict-card">
            <h2 style="font-size:18px;font-weight:700;color:var(--ink);">환경 상태를 확인하세요.</h2>
            <div style="font-size:12px;color:var(--ink-3);margin-top:8px;">
              환경 <b style="color:var(--risk);">{n_risk} 위험</b> ·
              <b style="color:var(--warn);">{n_warn} 주의</b>
            </div>
            <div class="card-body" style="margin-top:12px;">{env_tags}</div>
            <div style="margin-top:auto;padding-top:10px;font-size:11.5px;color:var(--ink-3);line-height:1.45;">
              업로드 센서 최근 {env_weeks}주({env_days}일) 평균 기준
              <br>· 주간(08~18시)·야간(19~07시)으로 온도·습도·CO₂ 는 평균값,
              <br>· 누적 일사량은 일별 최댓값 중 최댓값을 측정
            </div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

    leading_harvest = growth_summary.get("leading_harvest_total")
    leading_fruit = growth_summary.get("leading_fruit_total")
    harvest_leading_html = (
        f'<span style="font-size:13px;color:var(--ink-3);font-weight:600;"> / 선도 {leading_harvest:,}개</span>'
        if leading_harvest is not None
        else ""
    )
    fruit_leading_html = (
        f'<span style="font-size:13px;color:var(--ink-3);font-weight:600;"> / 선도 {leading_fruit:,}개</span>'
        if leading_fruit is not None
        else ""
    )

    st.markdown(
        f"""
        <div class="stat-row cols-2">
          <div class="stat"><div class="sl">누적 수확수</div><div class="sv">{harvest_total:,}<span style="font-size:13px;color:var(--ink-3);"> 개</span>{harvest_leading_html}</div><div class="sx">내 농가 누계 / 선도 농가(p50) 누계</div></div>
          <div class="stat"><div class="sl">누적 착과수</div><div class="sv">{fruit_total:,}<span style="font-size:13px;color:var(--ink-3);"> 개</span>{fruit_leading_html}</div><div class="sx">내 농가 누계 / 선도 농가(p50) 누계</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_growth_timeseries_section(growth_chart_df, key_prefix="status")

    if dims_ready:
        st.markdown('<div class="eyebrow">Act · <span class="ko">개선 방향</span></div>', unsafe_allow_html=True)
        actions = build_actions_from_kpis(env_kpis)
        if actions:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            for act in actions:
                render_action_item(act["title"], act["why"], act["desc"], act["urgency"], act["color"])
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.success("현재 측정값 기준 긴급 조치 항목이 없습니다.")

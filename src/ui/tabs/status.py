"""Tab 3 · 내 농가 진단."""
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
    render_tab_hero,
    render_triage,
)


def _sort_growth_kpis(kpis: list[dict]) -> list[dict]:
    order = {"초과": 0, "적정": 1, "미달": 2}
    return sorted(kpis, key=lambda k: order.get(k.get("label"), 9))


def _growth_tag_class(label: str) -> str:
    if label == "초과":
        return "high"
    if label == "미달":
        return "low"
    return "ok"


def _group_growth_tags(kpis: list[dict]) -> str:
    rows = []
    for label in ("초과", "적정", "미달"):
        tags = "".join(
            f'<span class="tag {_growth_tag_class(label)}">{k["text"]}</span>'
            for k in kpis
            if k.get("label") == label
        )
        if tags:
            rows.append(f'<div class="status-tag-row">{tags}</div>')
    return "".join(rows)


def _group_env_tags(kpis: list[dict]) -> str:
    rows = []
    for status, tag_class in (("risk", "r"), ("warn", "w"), ("ok", "ok")):
        tags = "".join(
            f'<span class="tag {tag_class}">'
            f'{k["name"]} {_format_kpi_value(k)} · {k["label"]}</span>'
            for k in kpis
            if k.get("status") == status
        )
        if tags:
            rows.append(f'<div class="status-tag-row">{tags}</div>')
    return "".join(rows)


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
    """내 농가 진단 탭 본문."""
    render_tab_hero(
        "Status · 내 농가 진단",
        "지금 생육·환경을 확인하세요",
        "선도 농가 기준과 비교해 생육·환경 상태, 누적 지표, 개선 방향을 한눈에 봅니다.",
    )
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
    n_env_ok = len([k for k in env_kpis if k["status"] == "ok"])

    if risk_kpis:
        for kpi in risk_kpis:
            render_triage(
                _env_primary_alert(kpi),
                status=kpi["status"],
            )
    else:
        render_triage(
            "오늘 꼭 볼 것 — 현재 환경 상태가 양호합니다.",
            status="ok",
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
        growth_tags = _group_growth_tags(_sort_growth_kpis(growth_kpis))
    else:
        growth_tags = '<span class="tag w">생육·수확 데이터 없음</span>'

    if env_kpis:
        env_tags = _group_env_tags(_sort_env_kpis(env_kpis))
    else:
        env_tags = '<span class="tag w">환경센서 데이터 없음</span>'

    env_from_rda = bool(st.session_state.get("rda_env_detail_show") and st.session_state.get("status_env_kpis"))
    if env_from_rda:
        env_basis_note = (
            "환경 설정 탭 「조회」 결과와 동일한 기준"
            "<br>· 지금 값·적정 구간은 환경 설정의 「지금 환경 상태」 게이지와 같습니다"
            "<br>· 누적 일사량·주간·야간 온도는 농진청 권장 구간, 그 외는 기본 기준"
        )
    else:
        env_basis_note = (
            f"업로드 센서 최근 {env_weeks}주({env_days}일) 평균 기준"
            "<br>· 환경 설정 탭에서 「조회」하면 농진청 권장 구간으로 갱신됩니다"
            "<br>· 주간(08~18시)·야간(19~07시)으로 온도·습도·CO₂ 는 평균값,"
            "<br>· 누적 일사량은 일별 최댓값 중 최댓값을 측정"
        )

    st.markdown(
        f"""
        <div class="hero-grid">
          <div class="card growth-card">
            <h2 style="font-size:18px;font-weight:700;color:var(--ink);">{growth_summary["headline"]}</h2>
            <div style="font-size:12px;color:var(--ink-3);margin-top:8px;">
              <b style="color:var(--warn);">{g_high} 초과</b> ·
              <b style="color:var(--ok);">{g_ok} 적정</b> ·
              <b style="color:var(--accent);">{g_low} 미달</b>
            </div>
            <div class="card-body" style="margin-top:12px;">{growth_tags}</div>
            <div style="margin-top:auto;padding-top:10px;font-size:11.5px;color:var(--ink-3);">선도 농가 표준(p25~p75) 대비 최근 조사</div>
          </div>
          <div class="card verdict-card">
            <h2 style="font-size:18px;font-weight:700;color:var(--ink);">환경 상태를 확인하세요.</h2>
            <div style="font-size:12px;color:var(--ink-3);margin-top:8px;">
              <b style="color:var(--risk);">{n_risk} 위험</b> ·
              <b style="color:var(--warn);">{n_warn} 주의</b> ·
              <b style="color:var(--ok);">{n_env_ok} 양호</b>
            </div>
            <div class="card-body" style="margin-top:12px;">{env_tags}</div>
            <div style="margin-top:auto;padding-top:10px;font-size:11.5px;color:var(--ink-3);line-height:1.45;">
              {env_basis_note}
            </div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

    leading_harvest = growth_summary.get("leading_harvest_total")
    leading_fruit = growth_summary.get("leading_fruit_total")

    def _leading_compare_html(mine: float | int, leading) -> str:
        if leading is None:
            return ""
        try:
            leading_val = float(leading)
        except (TypeError, ValueError):
            return ""
        if leading_val <= 0:
            pct_html = ""
        else:
            pct = (float(mine) - leading_val) / leading_val * 100
            sign = "+" if pct >= 0 else ""
            color = "var(--risk)" if pct >= 0 else "var(--accent)"
            pct_html = (
                f'<span style="font-size:13px;font-weight:700;color:{color};margin-left:6px;">'
                f"({sign}{pct:.1f}%)</span>"
            )
        return (
            f'<span style="font-size:13px;color:var(--ink-3);font-weight:600;">'
            f" / 선도 {leading_val:,.0f}개</span>{pct_html}"
        )

    harvest_leading_html = _leading_compare_html(harvest_total, leading_harvest)
    fruit_leading_html = _leading_compare_html(fruit_total, leading_fruit)

    st.markdown(
        f"""
        <div class="stat-row cols-2">
          <div class="stat"><div class="sl">누적 착과수</div><div class="sv">{fruit_total:,}<span style="font-size:13px;color:var(--ink-3);"> 개</span>{fruit_leading_html}</div><div class="sx">내 농가 누계 / 선도 농가(p50) 누계</div></div>
          <div class="stat"><div class="sl">누적 수확수</div><div class="sv">{harvest_total:,}<span style="font-size:13px;color:var(--ink-3);"> 개</span>{harvest_leading_html}</div><div class="sx">내 농가 누계 / 선도 농가(p50) 누계</div></div>
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

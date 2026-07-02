"""의사결정지원시스템 desktop UI — HTML 인터페이스(v0.04) 구조."""
from __future__ import annotations

import html
import os
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

import column_mapping as colmap

APP_TITLE = "의사결정지원시스템"
APP_SUBTITLE = "시설원예 생육·환경 데이터 기반 분석·예측"
DIMS_SAMPLE_DIR = Path(__file__).resolve().parent / "sample_data"
DEFAULT_SENSOR_FILE = DIMS_SAMPLE_DIR / "outdoor.indoor_sensor_20260622.csv"
DEFAULT_YIELD_FILE = DIMS_SAMPLE_DIR / "2026-06-22T06-50_export_생육수확통합.csv"
DIMS_SECURITY_KEY = os.environ.get("DIMS_SECURITY_KEY", "abcd")

ADIMS_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.css');
:root{
  --bg:#F7F8FA; --surface:#FFFFFF; --line:#E5E9EE; --line-soft:#EEF1F5;
  --ink:#243240; --ink-2:#5C6B7A; --ink-3:#8A97A4;
  --accent:#4E79A7; --accent-bg:#ECF1F6;
  --ok:#4F9D5B; --ok-bg:#EBF5ED;
  --warn:#D99220; --warn-bg:#FBF3E2;
  --risk:#D6494B; --risk-bg:#FBEAEA;
  --radius:14px;
  --shadow:0 1px 2px rgba(36,50,64,.04),0 6px 18px rgba(36,50,64,.05);
}
.stApp{background:var(--bg)!important;color:var(--ink)!important;font-family:'Pretendard',-apple-system,sans-serif!important;overflow-y:auto!important;height:auto!important;min-height:100vh;}
header[data-testid="stHeader"]{
  background:var(--surface)!important;
  border-bottom:1px solid var(--line);
  z-index:999;
}
/* 페이지 세로 스크롤 복원 (overflow:visible은 스크롤 컨테이너를 깨뜨림) */
html,body{overflow-y:auto!important;height:auto!important;}
[data-testid="stAppViewContainer"]{
  overflow-y:auto!important;
  overflow-x:hidden!important;
  height:auto!important;
  min-height:100vh;
}
section[data-testid="stMain"]{overflow:unset!important;}
.main .block-container,[data-testid="stMainBlockContainer"].block-container{
  max-width:1140px!important;
  padding-top:2.75rem!important;
  padding-bottom:4rem!important;
  padding-left:max(1.25rem,22px)!important;
  padding-right:max(1.25rem,22px)!important;
}
[data-testid="stTabs"] [data-baseweb="tab-panel"]{
  overflow:visible!important;
  height:auto!important;
  max-height:none!important;
}
[data-testid="stVerticalBlock"]{overflow:visible!important;}
.dims-header{
  background:var(--surface);
  border:1px solid var(--line);
  border-radius:var(--radius);
  padding:14px 20px;
  margin:10px 0 12px;
  box-shadow:var(--shadow);
  overflow:visible;
  position:relative;
  z-index:1;
}
.dims-brand{display:flex;align-items:center;gap:10px;}
.dims-brand .dot{width:10px;height:10px;border-radius:3px;background:var(--accent);display:inline-block;flex-shrink:0;}
.dims-brand-text{display:flex;flex-direction:column;gap:1px;min-width:0;}
.dims-brand-title{font-weight:700;font-size:16px;letter-spacing:-.3px;color:var(--ink);line-height:1.25;}
.dims-brand-sub{font-size:12px;font-weight:500;color:var(--ink-3);letter-spacing:-.1px;line-height:1.35;}
.dims-asof{font-size:12px;color:var(--ink-3);text-align:right;flex-shrink:0;}
.dims-asof b{color:var(--ink-2);font-weight:600;}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow);margin-bottom:4px;}
.hero-cols [data-testid="stHorizontalBlock"]{gap:1.5rem!important;margin-top:20px!important;align-items:stretch!important;}
.hero-cols [data-testid="column"]{display:flex!important;flex-direction:column!important;}
.hero-cols [data-testid="column"] > div{width:100%!important;flex:1!important;display:flex!important;flex-direction:column!important;}
.hero-cols [data-testid="column"] [data-testid="stMarkdown"]{flex:1!important;display:flex!important;flex-direction:column!important;}
.hero-cols [data-testid="column"] [data-testid="stMarkdown"] > div{width:100%!important;flex:1!important;display:flex!important;flex-direction:column!important;}
.hero-cols [data-testid="stPlotlyChart"]{margin-top:8px;}
.hero-grid{display:grid;grid-template-columns:1.55fr 1fr;gap:24px;margin-top:20px;align-items:stretch;}
@media(max-width:880px){.hero-grid{grid-template-columns:1fr;}}
.growth-card,.verdict-card{
  padding:24px 26px;position:relative;overflow:hidden;margin-bottom:12px;
  height:100%;min-height:100%;box-sizing:border-box;
  display:flex;flex-direction:column;
}
.growth-card .card-body,.verdict-card .card-body{flex:1;}
.growth-card::before,.verdict-card::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;}
.growth-card::before{background:var(--accent);}
.verdict-card::before{background:var(--warn);}
.chart-grid [data-testid="stHorizontalBlock"]{gap:1.25rem!important;margin-bottom:1rem!important;}
.eyebrow{font-size:11px;font-weight:700;letter-spacing:.12em;color:var(--ink-3);text-transform:uppercase;margin:26px 0 12px;display:flex;align-items:center;gap:8px;}
.eyebrow .ko{font-size:13px;letter-spacing:-.1px;color:var(--ink);text-transform:none;font-weight:700;}
.data-head h1{font-size:22px;font-weight:700;letter-spacing:-.5px;color:var(--ink)!important;margin:0;}
.data-head p{color:var(--ink-2);font-size:13.5px;margin-top:5px;}
.triage{display:flex;gap:12px;align-items:center;margin-top:16px;margin-bottom:4px;padding:14px 18px;background:var(--risk-bg);border-radius:12px;border-left:4px solid var(--risk);}
.triage.warn{background:var(--warn-bg);border-left-color:var(--warn);}
.triage .tt{font-size:13.5px;color:var(--ink);font-weight:600;line-height:1.5;}
.triage .tt b{color:var(--risk);}
.triage.warn .tt b{color:var(--warn);}
.pill{display:inline-flex;align-items:center;gap:8px;font-weight:700;font-size:14px;padding:7px 14px;border-radius:999px;background:var(--warn-bg);color:var(--warn);}
.pill.acc{background:var(--accent-bg);color:var(--accent);}
.pill .bead{width:9px;height:9px;border-radius:50%;background:currentColor;box-shadow:0 0 0 4px color-mix(in srgb,currentColor 18%,transparent);}
.stat-row{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:20px;}
@media(max-width:880px){.stat-row{grid-template-columns:1fr;}}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:15px 17px;box-shadow:var(--shadow);}
.stat .sl{font-size:11px;color:var(--ink-3);font-weight:600;}
.stat .sv{font-size:22px;font-weight:700;margin-top:5px;color:var(--ink);}
.stat .sx{font-size:11.5px;color:var(--ink-2);margin-top:3px;}
.stat .prog{height:6px;border-radius:4px;background:var(--bg);overflow:hidden;margin-top:10px;}
.stat .prog i{display:block;height:100%;border-radius:4px;background:var(--accent);}
.tag{font-size:12px;font-weight:600;padding:5px 10px;border-radius:8px;display:inline-block;margin:3px;}
.tag.r{color:var(--risk);background:var(--risk-bg)} .tag.w{color:var(--warn);background:var(--warn-bg)}
.act{display:grid;grid-template-columns:34px 1fr auto;gap:16px;align-items:center;padding:16px 20px;border-bottom:1px solid var(--line-soft);}
.act:last-child{border-bottom:0}
.rank{width:30px;height:30px;border-radius:9px;background:var(--accent);color:#fff;display:grid;place-items:center;font-weight:700;font-size:14px;}
.act-body .h{font-size:14.5px;font-weight:700;color:var(--ink);}
.act-body .d{font-size:13px;color:var(--ink-2);margin-top:3px;}
.act-right .imp{font-size:15px;font-weight:700;}
.strip{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;}
@media(max-width:880px){.strip{grid-template-columns:1fr;}}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:15px 16px;box-shadow:var(--shadow);margin-bottom:4px;}
.kpi-name{font-size:12.5px;font-weight:600;color:var(--ink-2);}
.badge{font-size:10.5px;font-weight:700;padding:3px 8px;border-radius:6px;display:inline-block;}
.badge.ok{color:var(--ok);background:var(--ok-bg)} .badge.warn{color:var(--warn);background:var(--warn-bg)} .badge.risk{color:var(--risk);background:var(--risk-bg)}
.kpi-val .v{font-size:25px;font-weight:700;color:var(--ink);}
.kpi-val .u{font-size:11.5px;color:var(--ink-3);font-weight:600;}
.g-track{position:relative;height:9px;border-radius:5px;background:#E7EBEF;margin-top:10px;}
.g-opt{position:absolute;top:0;height:100%;border-radius:5px;background:#86C795;}
.g-dev{position:absolute;top:0;height:100%;border-radius:5px;z-index:1;}
.g-pin{position:absolute;top:50%;transform:translate(-50%,-50%);width:15px;height:15px;border-radius:50%;border:3px solid #fff;box-shadow:0 0 0 1.5px rgba(36,50,64,.2);z-index:3;}
.stage-bar{display:flex;width:100%;height:42px;border-radius:10px;overflow:hidden;border:1px solid var(--line);box-shadow:var(--shadow);margin-top:14px;}
.stage-seg{box-sizing:border-box;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:#fff;text-align:center;line-height:1.25;padding:4px 6px;word-break:keep-all;flex-shrink:0;}
.stage-seg--s1{font-size:10.5px;}
.stage-tbl{width:100%;border-collapse:collapse;font-size:12.5px;}
.stage-tbl th,.stage-tbl td{padding:11px 14px;text-align:left;border-bottom:1px solid var(--line-soft);color:var(--ink);}
.stage-tbl th{font-size:11px;font-weight:700;color:var(--ink-3);background:var(--bg);}
.rda-result-tbl tr.rda-row-match td{background:var(--warn-bg);}
.rda-result-scroll{max-height:380px;overflow:auto;border-radius:var(--radius);}
.rda-result-scroll .rda-result-tbl{min-width:960px;}
.rda-result-scroll .rda-result-tbl thead th{position:sticky;top:0;z-index:2;background:var(--bg);box-shadow:0 1px 0 var(--line-soft);white-space:nowrap;}
.rda-result-scroll .rda-result-tbl td{white-space:nowrap;}
.judge.ok{color:var(--ok);font-weight:700} .judge.warn{color:var(--warn);font-weight:700} .judge.risk{color:var(--risk);font-weight:700}
.forecast{border:1.5px dashed var(--line);border-radius:14px;padding:18px;background:#FAFBFC;margin-top:18px;}
.forecast-model{border:1.5px dashed var(--accent);border-radius:14px;padding:18px;background:#F3F7FB;margin-top:22px;}
.forecast-model .model-head{font-size:13px;font-weight:700;color:var(--ink-2);margin:0 0 14px;}
.scard.model .sv{color:#3D6B9A;}
.simple-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;}
@media(max-width:880px){.simple-grid{grid-template-columns:1fr;}}
.scard{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:22px 20px;box-shadow:var(--shadow);text-align:center;}
.scard .sl{font-size:13px;color:var(--ink-2);font-weight:700;margin-top:8px;}
.scard .sv{font-size:30px;font-weight:800;color:var(--accent);margin-top:6px;}
.scard .sx{font-size:12.5px;color:var(--ink-3);margin-top:7px;line-height:1.45;}
.disclaimer{margin:34px 0 12px;padding:16px 20px;background:#EEF1F5;border-radius:12px;display:flex;gap:12px;}
.disclaimer .dt{font-size:12.5px;color:var(--ink-2);line-height:1.6;}
.copyright{margin:0 0 28px;padding:14px 4px 6px;text-align:center;font-size:11.5px;color:var(--ink-3);line-height:1.65;border-top:1px solid var(--line-soft);}
.copyright b{color:var(--ink-2);font-weight:600;}
.run-bar{display:flex;align-items:center;gap:18px;margin-top:18px;padding:16px 22px;background:var(--accent-bg);border-radius:var(--radius);}
.mchips{display:flex;flex-wrap:wrap;gap:7px;margin:8px 0;}
.mchip{font-size:12px;font-weight:600;color:var(--ink-2);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:7px 12px;}
.dims-top-spacer{height:6px;}
.subnote{font-size:11.5px;color:var(--ink-3);margin:9px 2px 0;}
[data-testid="stTabs"] [data-baseweb="tab-list"]{gap:2px;border-bottom:1px solid var(--line);margin-top:4px;}
[data-testid="stTabs"] [data-baseweb="tab"]{font-size:13.5px;font-weight:600;color:var(--ink-3)!important;padding:12px 16px 10px!important;min-height:46px;}
[data-testid="stTabs"] [aria-selected="true"]{color:var(--accent)!important;border-bottom:2.5px solid var(--accent)!important;}
[data-testid="stTabs"]{margin-top:6px;margin-bottom:2rem;}
[data-testid="stPlotlyChart"]{margin-bottom:12px;}
.tab-bottom-spacer{height:48px;}
.stButton>button[kind="primary"]{background:var(--accent)!important;color:#fff!important;font-weight:700!important;border-radius:10px!important;padding:12px 24px!important;box-shadow:0 4px 12px rgba(78,121,167,.3)!important;border:none!important;}
.stButton>button[kind="primary"]:disabled,.stButton>button:disabled{background:#C5CDD6!important;color:#fff!important;box-shadow:none!important;cursor:not-allowed!important;opacity:1!important;border:none!important;}
.data-source-note{font-size:12px;color:var(--ink-2);margin:4px 0 14px;}
div[data-testid="stFileUploader"] section{border:1.5px dashed var(--line)!important;border-radius:var(--radius)!important;background:var(--surface)!important;}
div[data-testid="stFileUploader"] section:hover{border-color:var(--accent)!important;}
</style>
"""

GROWTH_STAGES = [
    {"name": "정식·영양생장", "s": 0, "e": 0, "color": "#59A14F"},
    {"name": "개화기", "s": 1, "e": 2, "color": "#4E79A7"},
    {"name": "착과기", "s": 3, "e": 4, "color": "#E8A33D"},
    {"name": "비대·수확기", "s": 5, "e": 6, "color": "#E15759"},
]

STAGE_RECIPE = {
    "주간온도": (23, 26),
    "야간온도": (13, 16),
    "주간습도": (65, 80),
    "야간습도": (60, 80),
    "일사량": (1200, 2000),
}


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
          <div style="display:flex;align-items:center;gap:16px;">
            <div class="dims-brand">
              <span class="dot"></span>
              <div class="dims-brand-text">
                <div class="dims-brand-title">{html.escape(APP_TITLE)}</div>
                {sub_html}
              </div>
            </div>
            <div style="flex:1"></div>
            <div class="dims-asof">최종 조사 <b>{html.escape(str(asof_date))}</b></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_triage(message: str, kind: str = "risk", icon: str = "🔔"):
    cls = "triage warn" if kind == "warn" else "triage"
    st.markdown(f'<div class="{cls}"><span>{icon}</span><div class="tt">{message}</div></div>', unsafe_allow_html=True)


def _zone_to_status(zone: str) -> tuple[str, str]:
    if zone in ("최적구간", "중간구간"):
        return "ok", "적정"
    if zone in ("다습구간", "고온구간", "고온", "과다", "저온구간", "저습구간", "저광구간"):
        return "warn", zone.replace("구간", "")
    if zone in ("최고한계구간", "최저한계구간"):
        return "risk", zone.replace("구간", "")
    return "ok", "적정"


def build_env_kpis_from_row(row: pd.Series, week: int, core) -> list[dict]:
    specs = [
        ("야간 습도", core.build_window_feature_name(week, "평균야간습도(19~07시)"), "%", 40, 100, 60, 80),
        ("한낮 일사량", core.build_window_feature_name(week, "평균누적일사량(1일최대값기준)"), "", 0, 2500, 1200, 2000),
        ("주간 온도", core.build_window_feature_name(week, "평균주간온도(08~18시)"), "℃", 15, 30, 20, 24),
        ("야간 온도", core.build_window_feature_name(week, "평균야간온도(19~07시)"), "℃", 10, 25, 15, 18),
        ("주간 습도", core.build_window_feature_name(week, "평균주간습도(08~18시)"), "%", 40, 100, 60, 80),
        ("주간 CO₂", core.build_window_feature_name(week, "평균주간CO₂(08~18시)"), "ppm", 300, 900, 400, 800),
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
        out = f'<div class="g-out" style="color:var(--ok);font-size:10.5px;font-weight:700;margin-top:7px;">적정 범위 안 ✓</div>'
        if k["val"] > k["optHi"]:
            dev = f'<div class="g-dev" style="left:{o_r}%;width:{_clamp(pos-o_r,0,100)}%;background:{c}"></div>'
            out = f'<div class="g-out" style="color:{c};font-size:10.5px;font-weight:700;margin-top:7px;">적정보다 <b>{k["val"]-k["optHi"]:.1f}{k["unit"]}</b> 높음 ↑</div>'
        elif k["val"] < k["optLo"]:
            dev = f'<div class="g-dev" style="left:{pos}%;width:{_clamp(o_l-pos,0,100)}%;background:{c}"></div>'
            out = f'<div class="g-out" style="color:{c};font-size:10.5px;font-weight:700;margin-top:7px;">적정보다 <b>{k["optLo"]-k["val"]:.1f}{k["unit"]}</b> 낮음 ↓</div>'
        val_fmt = f'{k["val"]:,.1f}' if k["unit"] in ("℃", "%") else f'{k["val"]:,.0f}'
        parts.append(f"""
        <div class="kpi">
          <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
            <span class="kpi-name">{k["name"]}</span>
            <span class="badge {k["status"]}">{k["label"]}</span>
          </div>
          <div class="kpi-val"><span class="v">{val_fmt}</span><span class="u">{k["unit"]}</span></div>
          <div class="g-track">
            <div class="g-opt" style="left:{o_l}%;width:{o_w}%"></div>{dev}
            <div class="g-pin" style="left:{pos}%;background:{c}"></div>
          </div>
          <div style="display:flex;justify-content:space-between;font-size:10px;color:var(--ink-3);margin-top:10px;">
            <span>{k["min"]}</span><span style="font-weight:700;color:var(--ok)">적정 {k["optLo"]}~{k["optHi"]}</span><span>{k["max"]}</span>
          </div>{out}
        </div>""")
    parts.append("</section>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def _status_from_opt_range(val: float, opt_lo: float, opt_hi: float, env_key: str = "") -> tuple[str, str]:
    if opt_lo <= val <= opt_hi:
        return "ok", "적정"
    if val > opt_hi:
        if env_key == "일사량":
            return "risk", "최고한계"
        status = "risk" if env_key == "야간습도" else "warn"
        return status, "높음"
    return "warn", "낮음"


def build_env_kpis_from_measures(measures: dict[str, float]) -> list[dict]:
    specs = [
        ("야간 습도", "야간습도", "%", 40, 100, 60, 80),
        ("한낮 일사량", "일사량", "", 0, 2500, 1200, 2000),
        ("주간 온도", "주간온도", "℃", 15, 30, 20, 24),
        ("야간 온도", "야간온도", "℃", 10, 25, 15, 18),
        ("주간 습도", "주간습도", "%", 40, 100, 60, 80),
        ("주간 CO₂", "주간CO2", "ppm", 300, 900, 400, 800),
    ]
    kpis = []
    for name, key, unit, vmin, vmax, opt_lo, opt_hi in specs:
        val = measures.get(key)
        if val is None or (isinstance(val, float) and np.isnan(val)):
            continue
        status, label = _status_from_opt_range(float(val), opt_lo, opt_hi, key)
        if opt_lo <= float(val) <= opt_hi:
            label = "적정"
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


def _alert_priority_kpis(kpis: list[dict]) -> list[dict]:
    """상단 알림 순서 — 야간습도·일사량 등 주요 항목 우선."""
    order = {"야간 습도": 0, "한낮 일사량": 1, "주간 온도": 2, "야간 온도": 3}
    flagged = [k for k in kpis if k["status"] != "ok"]
    return sorted(flagged, key=lambda k: (order.get(k["name"], 9), {"risk": 0, "warn": 1}.get(k["status"], 9)))


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
    return f'오늘 꼭 볼 것 — <b>{k["name"]}</b>가 {detail}. 환경 제어를 점검하세요.'


def _env_secondary_alert(k: dict) -> str:
    return (
        f'이상 지속 알림 — <b>{k["name"]} {_format_kpi_value(k)}</b> '
        f'상태가 지속되고 있습니다.'
    )


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
) -> list[dict]:
    """현황 탭 환경 KPI — 업로드 센서 최근 7일 우선."""
    if sensor_df is not None and date_col_sensor and temp_col:
        measures = build_recent_env_measures(
            sensor_df, date_col_sensor, temp_col, hum_col, solar_col, co2_col=co2_col
        )
        if measures:
            return build_env_kpis_from_measures(measures)
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
    from rda_standards import build_rda_recent_actuals

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


def render_control_quality_stats(stats: dict):
    oos = stats.get("night_hum_oos_pct")
    vpd = stats.get("night_vpd")
    swings = stats.get("day_temp_swing_days", 0)
    days = stats.get("days", 7)

    if oos is None and vpd is None:
        return

    if oos is not None:
        oos_status = "risk" if oos >= 50 else ("warn" if oos >= 30 else "ok")
        oos_label = "주의" if oos_status == "risk" else ("보통" if oos_status == "warn" else "양호")
        oos_color = "var(--risk)" if oos_status == "risk" else ("var(--warn)" if oos_status == "warn" else "var(--ok)")
    else:
        oos_status, oos_label, oos_color = "ok", "—", "var(--ink)"

    if vpd is not None:
        vpd_status = "ok" if 0.6 <= vpd <= 1.2 else "warn"
        vpd_label = "적정" if vpd_status == "ok" else ("낮음" if vpd < 0.6 else "높음")
        vpd_color = "var(--ok)" if vpd_status == "ok" else "var(--warn)"
        vpd_note = "적정 0.6~1.2" + (" · 다습으로 다소 낮음" if vpd < 0.6 else (" · 건조" if vpd > 1.2 else ""))
    else:
        vpd_status, vpd_label, vpd_color, vpd_note = "ok", "—", "var(--ink)", "—"

    swing_status = "warn" if swings >= 3 else "ok"
    swing_label = "보통" if swing_status == "warn" else "양호"
    swing_color = "var(--warn)" if swing_status == "warn" else "var(--ok)"

    oos_val = f"{oos:.0f}" if oos is not None else "—"
    vpd_val = f"{vpd:.1f}" if vpd is not None else "—"

    st.markdown(
        f"""
        <div class="stat-row">
          <div class="stat">
            <div class="sl">적정 이탈 시간 <span class="badge {oos_status}">{oos_label}</span></div>
            <div class="sv" style="color:{oos_color};">{oos_val}<span style="font-size:13px;color:var(--ink-3);font-weight:600">%</span></div>
            <div class="sx">야간습도가 적정(60~80%)을 벗어난 시간 비율</div>
          </div>
          <div class="stat">
            <div class="sl">야간 VPD <span class="badge {vpd_status}">{vpd_label}</span></div>
            <div class="sv" style="color:{vpd_color};">{vpd_val}<span style="font-size:13px;color:var(--ink-3);font-weight:600"> kPa</span></div>
            <div class="sx">{vpd_note}</div>
          </div>
          <div class="stat">
            <div class="sl">환경 안정성 <span class="badge {swing_status}">{swing_label}</span></div>
            <div class="sv" style="color:{swing_color};">{swings}<span style="font-size:13px;color:var(--ink-3);font-weight:600"> 회</span></div>
            <div class="sx">주간온도 급변 횟수(일교차 5℃ 초과 일수)</div>
          </div>
        </div>
        <p class="subnote">※ 최근 {days}일 기준. 한 시점 값이 아니라 ‘얼마나 오래·안정적으로 적정을 유지했는가’를 봅니다. VPD는 수증기압차로, 토마토 제어 품질의 핵심 지표입니다.</p>
        """,
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
        '<div class="eyebrow">Control · <span class="ko">환경 제어가 잘 되고 있나 (최근 7일)</span></div>',
        unsafe_allow_html=True,
    )
    control = build_control_quality_from_sensor(sensor_df, date_col, temp_col, hum_col)
    if control:
        render_control_quality_stats(control)
    else:
        st.caption("온도·습도 센서 데이터가 있으면 최근 7일 제어 품질을 함께 표시합니다.")


def render_action_item(rank, title, why, desc, status, color):
    st.markdown(
        f"""
        <div class="card act">
          <div class="rank">{rank}</div>
          <div class="act-body">
            <div class="h">{title} <span style="font-weight:600;font-size:12px;color:var(--ink-3);margin-left:8px;">{why}</span></div>
            <div class="d">{desc}</div>
          </div>
          <div class="act-right"><div style="font-size:10.5px;color:var(--ink-3);font-weight:600;">상태</div>
          <div class="imp" style="color:{color};">{status}</div></div>
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
    from rda_standards import RDA_STAGE_COLORS

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


def _judge_in_range(val: float, range_text: str) -> tuple[str, str]:
    from rda_standards import parse_range

    lo, hi = parse_range(range_text)
    if lo is None or hi is None or val is None or np.isnan(val):
        return "—", ""
    if lo <= val <= hi:
        return "적정", "ok"
    if val > hi:
        return "높음 ↑", "warn"
    return "낮음 ↓", "warn"


def render_rda_result_table(view: pd.DataFrame, highlight_indices: list[int] | None = None):
    highlights = set(highlight_indices or [])
    headers = "".join(f"<th>{html.escape(str(c))}</th>" for c in view.columns)
    rows = []
    for i in range(len(view)):
        row = view.iloc[i]
        cls = ' class="rda-row-match"' if i in highlights else ""
        cells = []
        for c in view.columns:
            v = row[c]
            text = "—" if pd.isna(v) else str(v)
            cells.append(f"<td>{html.escape(text)}</td>")
        rows.append(f"<tr{cls}>{''.join(cells)}</tr>")
    st.markdown(
        f'<div class="card rda-result-scroll">'
        f'<table class="stage-tbl rda-result-tbl"><thead><tr>{headers}</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>',
        unsafe_allow_html=True,
    )


def render_rda_compare_table(match_row: pd.Series, actuals: dict[str, float] | None):
    if match_row is None or match_row.empty or not actuals:
        return
    mapping = [
        ("누적일사량", "누적일사량(범위)", "일사량", ""),
        ("주간 평균온도", "주간 평균온도(℃)", "주간온도", "℃"),
        ("야간 평균온도", "야간 평균온도(℃)", "야간온도", "℃"),
    ]
    rows = []
    for label, rda_col, actual_key, unit in mapping:
        rec = match_row.get(rda_col, "—")
        val = actuals.get(actual_key)
        if val is None or (isinstance(val, float) and np.isnan(val)):
            continue
        judge, jcls = _judge_in_range(float(val), str(rec))
        rows.append(
            f"<tr><td>{label}</td><td>{rec}</td>"
            f'<td style="font-weight:600;">{float(val):.1f}{unit}</td>'
            f'<td class="judge {jcls}">{judge}</td></tr>'
        )
    if rows:
        st.markdown(
            '<div class="eyebrow">Compare · <span class="ko">농진청 권장 대비 최근 실측</span></div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "농진청 권장: **노란색 행**과 동일한 누적일사량·외기기온 구간의 권장값을 **최소~최댓값**으로 통합 · "
            "최근 실측: **조회 입력값(누적일사량)** 및 센서 **최근 7일** 주·야간 온도"
        )
        st.markdown(
            f'<div class="card"><table class="stage-tbl"><tr><th>환경</th><th>농진청 권장</th><th>최근 실측</th><th>판정</th></tr>{"".join(rows)}</table></div>',
            unsafe_allow_html=True,
        )


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
    from geo_weather import fetch_current_temperature, reverse_geocode_label
    from streamlit_geolocation import streamlit_geolocation

    location = _parse_geolocation(streamlit_geolocation())
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
    from geo_weather import fetch_outdoor_temp_for_region
    from korea_regions import list_sido, list_sigungu

    st.markdown(
        '<div class="eyebrow" style="margin-top:4px;">Location · <span class="ko">외기기온 위치</span></div>',
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
    from rda_standards import (
        RDA_STAGES_GROWTH,
        RDA_STAGES_SOLAR,
        build_rda_recent_actuals,
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

    st.markdown(
        '<div class="data-head"><h1>생육 흐름</h1>'
        '<p>농진청 토마토 시설재배 <b>일사량별 최적환경</b>·<b>생육상태별 최적생산량</b> 표준을 조회합니다.</p></div>',
        unsafe_allow_html=True,
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
            facility = st.radio("시설유형", ["비닐", "유리"], horizontal=True, key=f"rda_facility_{kind}")
            stages = RDA_STAGES_SOLAR if kind == "solar" else RDA_STAGES_GROWTH
            stage_key = f"rda_stage_{kind}"
            if stage_key not in st.session_state:
                st.session_state[stage_key] = (
                    default_stage if default_stage in stages else stages[4]
                )
            stage = st.radio(
                "권장설정 조회 선택사항",
                stages,
                horizontal=True,
                key=stage_key,
            )
            st.markdown('<div class="eyebrow">Stage · <span class="ko">생육단계</span></div>', unsafe_allow_html=True)
            render_rda_stage_picker(kind, stage, stages)

            st.markdown(
                '<div class="eyebrow" style="margin-top:18px;">Search · <span class="ko">맞춤형 최적환경설정 조회</span></div>',
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
                st.warning("농진청 표준 데이터 파일을 찾을 수 없습니다. `data/` 폴더의 xlsx 파일을 확인해 주세요.")
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

            if kind == "solar" and search and aggregated_rec is not None and not shown.empty:
                rda_actuals = build_rda_recent_actuals(
                    sensor_df,
                    date_col_sensor,
                    temp_col,
                    solar_col,
                    solar_override=solar_q,
                )
                render_rda_compare_table(aggregated_rec, rda_actuals)

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
            rda_kpis = build_env_kpis_from_measures(measures)
            render_env_detail_section(
                rda_kpis,
                sensor_df=sensor_df,
                date_col=date_col_sensor,
                temp_col=temp_col,
                hum_col=hum_col,
                context_note=(
                    "※ 적정 구간은 작기 전체 기준입니다. "
                    "<b style=\"color:var(--ink-2)\">업로드한 환경센서 최근 7일</b> 데이터로 계산했습니다. "
                    "농진청 표준 조회 결과와 함께 현재 생육단계 목표 환경을 확인하세요."
                ),
            )
        else:
            st.markdown(
                '<div class="eyebrow">Env · <span class="ko">환경 상세 — 지금 값·적정 구간·제어 품질</span></div>',
                unsafe_allow_html=True,
            )
            st.info("환경센서 데이터를 업로드하면 조회 결과와 함께 환경 상세를 확인할 수 있습니다.")

    st.markdown('<div class="tab-bottom-spacer"></div>', unsafe_allow_html=True)


def render_recipe_table(measures: dict[str, float]):
    rows = []
    for env, (lo, hi) in STAGE_RECIPE.items():
        val = measures.get(env)
        if val is None or np.isnan(val):
            continue
        if lo <= val <= hi:
            judge, jcls = "적정", "ok"
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
    actions = []
    advice = {
        "야간 습도": ("야간 제습·환기", "난방배관·환기로 야간 결로 차단, 관수량 점검. 80% 이하로 낮춰 잿빛곰팡이·노균병 위험 완화.", "위험", "var(--risk)"),
        "한낮 일사량": ("한낮 차광·엽온 관리", "차광 스크린·환기·세무 냉방으로 정오 전후 엽온 상승 억제.", "주의", "var(--warn)"),
        "주간 온도": ("주간 온도 완화", "정오 환기 강화로 24℃대 적정구간 복귀.", "주의", "var(--warn)"),
        "야간 온도": ("야간 온도 관리", "야간 환기·난방으로 13~16℃ 권장 구간 유지.", "주의", "var(--warn)"),
    }
    for k in kpis:
        if k["status"] == "ok":
            continue
        if k["name"] in advice:
            title, desc, status, color = advice[k["name"]]
            why = f'{k["name"]} {k["val"]:.1f}{k["unit"]} ({k["label"]})'
            actions.append({"title": title, "why": why, "desc": desc, "status": status, "color": color})
    return actions[:3]


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
                name="표준 범위 (p25~p75)", hoverinfo="skip",
            ))
            fig.add_trace(go.Scatter(
                x=std[x_col], y=std["p50"], mode="lines",
                line=dict(color="#8A97A4", width=2, dash="dash"),
                name="표준 중앙값 (p50)",
            ))
    fig.add_trace(go.Scatter(
        x=plot_df[x_col], y=plot_df[y_col], mode="lines+markers",
        line=dict(color=color, width=2), marker=dict(size=5),
        name="내 농가",
    ))
    fig.update_layout(
        title=title, height=220, margin=dict(l=40, r=10, t=36, b=30),
        template="plotly_white",
        showlegend=standard_df is not None and not standard_df.empty,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=10)),
        paper_bgcolor="#fff", plot_bgcolor="#F7F8FA",
        font=dict(family="Pretendard, sans-serif", size=11, color="#243240"),
    )
    fig.update_xaxes(gridcolor="#EEF1F5", linecolor="#D7DDE4")
    fig.update_yaxes(gridcolor="#EEF1F5", linecolor="#D7DDE4")
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


GROWTH_CHART_PRIMARY = ["착과수", "초장", "엽수", "수확수"]
GROWTH_CHART_EXTRA = ["생장길이", "엽장", "엽폭", "줄기굵기", "화방높이"]
MAIN_TAB_LABELS = ["1 데이터", "2 현황", "3 생육 흐름", "4 예측"]
MAIN_TAB_STATUS = 1


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
    """생육·수확 시계열 차트 — 업로드 실측 + data/생육 참조 표준."""
    import app as core
    from growth_standards import build_growth_standard_curves

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
    standard_curves, n_ref_farms = build_growth_standard_curves(upload_start, max_rel_day=max_rel_day)

    st.markdown(
        '<div class="eyebrow">Growth · <span class="ko">생육·수확이 어떻게 커왔나</span></div>',
        unsafe_allow_html=True,
    )
    if standard_curves and n_ref_farms:
        st.caption(
            f"**실선 · 내 농가** = 업로드 파일 조사일자별 실측 · "
            f"**회색 점선 · 표준** = `data/생육` 참조 {n_ref_farms}개 농가 "
            f"(정식 시기 {upload_start.strftime('%m-%d')} 전후 유사 농가 가중 · 주별 p25~p75)"
        )
    else:
        st.caption(
            "업로드한 생육·수확 파일의 **조사일자별 실측값**입니다. "
            "같은 날짜에 화방별 여러 행이 있으면 수확·착과는 합산, 생육 측정값은 평균으로 표시합니다."
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


def _upload_forecast_cache_key(upload_df: pd.DataFrame, selected_week: int, fruit_total: int) -> str:
    frame = upload_df.copy()
    frame["조사일자"] = pd.to_datetime(frame["조사일자"], errors="coerce")
    frame = frame.dropna(subset=["조사일자"]).sort_values("조사일자")
    if frame.empty:
        return f"empty-{selected_week}-{fruit_total}"
    latest = frame.iloc[-1]
    env_cols = sorted(c for c in frame.columns if "주평균" in c or "주평균" in str(c))
    env_sig = tuple(
        round(float(latest[c]), 3) if c in latest.index and pd.notna(latest[c]) else None
        for c in env_cols[:7]
    )
    return f"{len(frame)}|{latest['조사일자'].date()}|{selected_week}|{fruit_total}|{env_sig}"


def render_model_forecast_section(
    upload_df,
    week_dfs: dict,
    selected_week: int,
    growth_features: list[str],
    fruit_total: int,
):
    """기존 전망 카드 아래 — RandomForest 모델 예측 카드."""
    from reference_training_data import build_model_forecast_summary

    cache_key = _upload_forecast_cache_key(upload_df, selected_week, fruit_total)
    if (
        st.session_state.get("model_forecast_cache_key") == cache_key
        and st.session_state.get("model_forecast_summary")
    ):
        summary = st.session_state.model_forecast_summary
    else:
        with st.spinner("RandomForest 모델 예측 계산 중… (최초 1회는 참조 데이터 로드로 시간이 걸릴 수 있습니다)"):
            summary = build_model_forecast_summary(
                upload_df,
                week_dfs,
                selected_week,
                growth_features,
                fruit_total=fruit_total,
            )
        st.session_state.model_forecast_cache_key = cache_key
        st.session_state.model_forecast_summary = summary

    if not summary or not summary.get("targets"):
        st.caption("모델 예측을 계산할 데이터가 부족합니다. 분석 데이터와 참조 폴더를 확인해 주세요.")
        return

    info = summary["info"]
    week = summary["selected_week"]
    targets = summary["targets"]
    t_harvest = targets.get("수확수", {})
    t_fruit = targets.get("착과수", {})
    t_height = targets.get("초장", {})
    delay_m = summary.get("model_delay_days", 0)

    harvest_sv = f'{t_harvest.get("pred", 0):.0f}<span style="font-size:14px;color:var(--ink-3);"> 개</span>' if t_harvest else "—"
    harvest_sx = (
        f'{summary["harvest_note"]}<br>R² {t_harvest["r2"]:.2f} · {week}주 환경'
        if t_harvest else ""
    )
    if t_harvest and t_harvest.get("actual") is not None:
        harvest_sx += f'<br>실측 {t_harvest["actual"]:.0f}개 → 예측 {t_harvest["pred"]:.0f}개'

    delay_sv = f'{delay_m}<span style="font-size:14px;color:var(--ink-3);">일</span>'
    delay_sx = "표준 대비 예측 초장 기준"
    if t_height:
        delay_sx += f'<br>예측 초장 {t_height["pred"]:.1f}cm · R² {t_height["r2"]:.2f}'
        if t_height.get("actual") is not None:
            delay_sx += f' (실측 {t_height["actual"]:.1f}cm)'

    fruit_sv = f'{t_fruit.get("pred", 0):.0f}<span style="font-size:14px;color:var(--ink-3);"> 개</span>' if t_fruit else "—"
    fruit_sx = f'최근 조사({summary["latest_date"]}) 환경 기준'
    if t_fruit:
        fruit_sx += f'<br>R² {t_fruit["r2"]:.2f}'
        if t_fruit.get("actual") is not None:
            fruit_sx += f' · 실측 {t_fruit["actual"]:.0f}개'
        fruit_sx += f'<br>작기 누적 예측 약 {summary["projected_fruit_total"]:,}개'

    train_note = (
        f"학습 {info['upload_rows']:,}건(업로드) + {info['ref_rows']:,}건(참조 {info['ref_farms']}농가)"
        if info.get("ref_rows")
        else f"학습 {info.get('upload_rows', 0):,}건(업로드만)"
    )

    st.markdown(
        f"""
        <div class="forecast-model">
          <p class="model-head">🤖 RandomForest 모델 예측 · {train_note}</p>
          <div class="simple-grid">
            <div class="scard model">
              <div style="font-size:24px;">📈</div>
              <div class="sl">모델 예측 · 수확수</div>
              <div class="sv">{harvest_sv}</div>
              <div class="sx">{harvest_sx}</div>
            </div>
            <div class="scard model">
              <div style="font-size:24px;">🌿</div>
              <div class="sl">모델 예측 · 생육 지연</div>
              <div class="sv">{delay_sv}</div>
              <div class="sx">{delay_sx}</div>
            </div>
            <div class="scard model">
              <div style="font-size:24px;">🍅</div>
              <div class="sl">모델 예측 · 착과수</div>
              <div class="sv">{fruit_sv}</div>
              <div class="sx">{fruit_sx}</div>
            </div>
          </div>
          <p class="subnote" style="margin-top:13px;">
            ※ 참조 데이터(`data/생육`·`환경`·`일사량`)와 업로드 데이터로 학습한 RandomForest가
            <b>최근 조사일({summary["latest_date"]})의 {week}주 환경</b>을 입력으로 예측한 값입니다.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def run_desktop_ui(render_xai_fn):
    import app as core

    st.markdown(ADIMS_CSS, unsafe_allow_html=True)

    if "dims_ready" not in st.session_state:
        st.session_state.dims_ready = False
    if "weeks" not in st.session_state:
        st.session_state.weeks = 7

    render_dims_header(st.session_state.get("dims_asof", "—"))

    tab_data, tab_now, tab_series, tab_forecast = st.tabs(MAIN_TAB_LABELS)

    sensor_file = yield_file = None
    crop_name = st.session_state.get("dims_crop", "토마토")
    has_data = False
    run = False

    with tab_data:
        st.markdown(
            '<div class="map-sub" style="font-size:11px;font-weight:700;color:var(--ink-3);margin:26px 0 9px;">'
            "작물을 선택해주세요</div>",
            unsafe_allow_html=True,
        )
        crop_name = st.selectbox("작물", ["토마토", "딸기", "파프리카", "오이"], key="dims_crop", label_visibility="collapsed")

        st.markdown(
            '<div class="data-head" style="margin-top:18px;"><h1>분석할 데이터를 올려주세요</h1>'
            '<p>보안키 또는 파일 업로드 중 <b>하나</b>를 선택해 분석을 진행하세요.</p></div>',
            unsafe_allow_html=True,
        )

        if "dims_data_source_mode" not in st.session_state:
            st.session_state.dims_data_source_mode = "파일 업로드"
        prev_mode = st.session_state.get("dims_data_source_mode")
        data_source_mode = st.radio(
            "데이터 입력 방식",
            ["보안키 사용", "파일 업로드"],
            horizontal=True,
            key="dims_data_source_mode",
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

        if data_source_mode == "보안키 사용":
            st.markdown(
                '<p class="data-source-note">데모용 보안키를 입력하면 샘플 데이터로 바로 분석할 수 있습니다.</p>',
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
                st.error("데모 데이터 파일을 찾을 수 없습니다. `sample_data/` 폴더를 확인해 주세요.")
        else:
            st.markdown(
                '<p class="data-source-note">환경센서·수확·생육 CSV 또는 Excel(xlsx) 파일을 업로드하세요.</p>',
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**환경센서 데이터 (CSV · XLSX)**")
                st.caption("측정일자 · 온도 · 습도 · CO₂ · 외부누적일사량")
                sensor_file = st.file_uploader(
                    "환경센서", type=["csv", "xlsx"], label_visibility="collapsed", key="dims_sensor"
                )
            with c2:
                st.markdown("**수확·생육 데이터 (CSV · XLSX)**")
                st.caption("조사일자 · 수확수 · 착과수 · 생육 측정값")
                yield_file = st.file_uploader(
                    "수확·생육", type=["csv", "xlsx"], label_visibility="collapsed", key="dims_yield"
                )
            has_uploads = bool(sensor_file and yield_file)

        has_demo = (
            data_source_mode == "보안키 사용"
            and demo_unlocked
            and DEFAULT_SENSOR_FILE.exists()
            and DEFAULT_YIELD_FILE.exists()
        )
        has_data = has_demo if data_source_mode == "보안키 사용" else has_uploads
        can_analyze = has_data

        sensor_df = yield_df = None
        if data_source_mode == "보안키 사용" and has_demo:
            sensor_df = read_table_path(DEFAULT_SENSOR_FILE)
            yield_df = read_table_path(DEFAULT_YIELD_FILE)
        elif data_source_mode == "파일 업로드" and has_uploads:
            sensor_df = read_uploaded_table(sensor_file)
            yield_df = read_uploaded_table(yield_file)

        if has_data and sensor_df is not None and yield_df is not None:
            yield_df = core.aggregate_fruit_level_yield(
                yield_df, "조사일자" if "조사일자" in yield_df.columns else yield_df.columns[0]
            )
            growth_features = (
                ["초장", "생장길이", "엽수", "엽장", "엽폭", "줄기굵기", "화방높이"]
                if crop_name == "토마토"
                else ["초장", "엽수", "엽장", "엽폭", "줄기굵기", "화방높이"]
            )

            with st.expander("매핑 데이터 확인 · 자동 인식됨", expanded=False):
                st.markdown(
                    '<div class="map-sub" style="font-size:11px;font-weight:700;color:var(--ink-3);">환경센서 · 자동 인식</div>',
                    unsafe_allow_html=True,
                )
                env_chips = [c for c in sensor_df.columns[:8]]
                st.markdown(
                    '<div class="mchips">' + "".join(f'<span class="mchip">{c}</span>' for c in env_chips) + "</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="map-sub" style="font-size:11px;font-weight:700;color:var(--ink-3);margin-top:12px;">수확·생육 · 자동 인식</div>',
                    unsafe_allow_html=True,
                )
                yld_chips = [c for c in yield_df.columns[:10]]
                st.markdown(
                    '<div class="mchips">' + "".join(f'<span class="mchip">{c}</span>' for c in yld_chips) + "</div>",
                    unsafe_allow_html=True,
                )

            manual_map = st.checkbox("컬럼이 맞지 않으면 직접 지정", key="dims_manual_map")
            if manual_map:
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1:
                    date_col_sensor = st.selectbox("센서 날짜", sensor_df.columns, index=core.pick_column_index(sensor_df.columns, ["측정시간", "측정 일자", "날짜시간", "일시", "날짜"]))
                with c2:
                    temp_col = st.selectbox("온도", sensor_df.columns, index=core.pick_column_index(sensor_df.columns, ["온도_내부", "내부온도", "온도"]))
                with c3:
                    hum_col = st.selectbox("습도", sensor_df.columns, index=core.pick_column_index(sensor_df.columns, ["상대습도_내부", "습도_내부", "습도"]))
                with c4:
                    co2_col = st.selectbox("CO₂", sensor_df.columns, index=core.pick_column_index(sensor_df.columns, ["잔존CO2", "CO2", "CO₂"]))
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
                    date_col_yield = st.selectbox("조사일자", yield_df.columns, index=core.pick_column_index(yield_df.columns, ["조사일자", "날짜"]))
                with c7:
                    harvest_count_col = st.selectbox("수확수", yield_df.columns, index=core.pick_column_index(yield_df.columns, ["화방별수확수", "수확수"]))
                with c8:
                    harvest_weight_col = st.selectbox("착과수", yield_df.columns, index=core.pick_column_index(yield_df.columns, ["화방별착과수", "착과수"]))
                growth_cols = {}
                for gf in growth_features:
                    opts = [None] + yield_df.columns.tolist()
                    idx = yield_df.columns.get_loc(gf) + 1 if gf in yield_df.columns else 0
                    growth_cols[gf] = st.selectbox(gf, opts, index=idx, key=f"dims_gf_{gf}")
            else:
                date_col_sensor = sensor_df.columns[core.pick_column_index(sensor_df.columns, ["측정시간", "측정 일자", "날짜시간", "일시", "날짜", "Date", "datetime"])]
                temp_col = sensor_df.columns[core.pick_column_index(sensor_df.columns, ["온도(℃)", "온도_내부", "내부온도", "온도"])]
                hum_col = sensor_df.columns[core.pick_column_index(sensor_df.columns, ["상대 습도(%)", "상대습도_내부", "습도_내부", "습도"])]
                co2_col = sensor_df.columns[core.pick_column_index(sensor_df.columns, ["CO2(ppm)", "잔존CO2", "CO2", "CO₂", "co2"])]
                solar_col = colmap.pick_external_cumulative_solar_column(sensor_df.columns)
                date_col_yield = yield_df.columns[core.pick_column_index(yield_df.columns, ["조사일자", "조사 일자", "날짜", "Date", "date"])]
                harvest_count_col = yield_df.columns[core.pick_column_index(yield_df.columns, ["화방별수확수", "수확수", "수확과수"])]
                harvest_weight_col = yield_df.columns[core.pick_column_index(yield_df.columns, ["화방별착과수", "착과수", "수확과중"])]
                growth_cols = {gf: (gf if gf in yield_df.columns else None) for gf in growth_features}
        elif not can_analyze:
            if data_source_mode == "보안키 사용":
                st.info("올바른 보안키를 입력하면 매핑 확인과 분석 실행이 가능합니다.")
            else:
                st.info(
                    "두 파일(CSV 또는 xlsx)을 모두 업로드하면 "
                    "매핑 확인과 분석 실행이 가능합니다."
                )

        st.markdown('<div class="run-bar">', unsafe_allow_html=True)
        rb1, rb2, rb3 = st.columns([2, 1, 1])
        with rb2:
            weeks_val = st.number_input(
                "평균 계산 기간 (주)",
                min_value=1,
                max_value=7,
                value=st.session_state.weeks,
                key="dims_weeks",
            )
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
            if run:
                st.session_state.dims_ready = True
                st.session_state.dims_show_complete_msg = True
                st.session_state.dims_goto_tab = MAIN_TAB_STATUS
        st.markdown("</div>", unsafe_allow_html=True)

    if not has_data:
        with tab_now:
            st.info("데이터 탭에서 보안키 또는 파일 업로드 중 하나를 선택한 뒤 「분석 결과 보기」를 실행하세요.")
        with tab_series:
            render_rda_flow_tab()
        render_disclaimer()
        return

    # 전처리
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
    for wk in range(1, 8):
        week_dfs[wk] = core.compute_rolling_summary(
            sensor_df, yield_df, date_col_sensor, date_col_yield,
            temp_col, hum_col, co2_col, solar_col,
            harvest_count_col, harvest_weight_col, growth_cols, wk,
        )
    df = week_dfs[selected_week].copy()
    if df.empty or "조사일자" not in df.columns:
        st.session_state.dims_show_complete_msg = False
        st.error("생육·수확 데이터를 처리하지 못했습니다. **조사일자** 컬럼과 날짜 형식을 확인해 주세요.")
        with tab_series:
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

    if dims_ready and st.session_state.pop("dims_show_complete_msg", False):
        st.success("분석이 완료되었습니다. 결과를 확인하세요.")

    yield_chart_df = build_growth_chart_df(
        yield_df, date_col_yield, harvest_count_col, harvest_weight_col, growth_cols
    )
    harvest_total, fruit_total = _yield_cumulative_totals(
        yield_df, date_col_yield, harvest_count_col, harvest_weight_col, growth_cols
    )

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
    )
    risk_kpis = _alert_priority_kpis(env_kpis)

    from growth_standards import summarize_growth_vs_standard

    if dims_ready and not df.empty:
        growth_chart_df = build_growth_chart_df(
            df, growth_cols={gf: gf for gf in growth_features if gf in df.columns}
        )
    else:
        growth_chart_df = yield_chart_df
    growth_summary = summarize_growth_vs_standard(growth_chart_df)
    delay_days = growth_summary["delay_days"]

    n_risk = len([k for k in env_kpis if k["status"] == "risk"])
    n_warn = len([k for k in env_kpis if k["status"] == "warn"])
    env_pill = "위험" if n_risk else ("주의" if n_warn else "양호")
    env_pill_cls = "pill" if n_risk or n_warn else "pill acc"

    with tab_now:
        if not dims_ready:
            st.info("데이터 탭에서 매핑을 확인한 뒤 「분석 결과 보기」를 누르면 예측·상세 분석이 열립니다.")

        if risk_kpis:
            render_triage(_env_primary_alert(risk_kpis[0]))
        if len(risk_kpis) > 1:
            render_triage(_env_secondary_alert(risk_kpis[1]), kind="warn", icon="⏱️")

        pill_cls = "pill" if growth_summary["pill_warn"] else "pill acc"
        if env_kpis:
            tags = "".join(
                f'<span class="tag {"r" if k["status"]=="risk" else "w"}">'
                f'{k["name"]} {_format_kpi_value(k)} · {k["label"]}</span>'
                for k in _sort_env_kpis(env_kpis)[:4]
            )
        else:
            tags = '<span class="tag w">환경센서 데이터 없음</span>'
        st.markdown(
            f"""
            <div class="hero-grid">
              <div class="card growth-card">
                <span class="{pill_cls}"><span class="bead"></span>{growth_summary["pill_label"]}</span>
                <h2 style="font-size:20px;font-weight:700;margin:12px 0 8px;color:var(--ink);line-height:1.45;">
                  {growth_summary["headline"]}
                </h2>
                <div class="card-body" style="color:var(--ink-2);font-size:13.5px;">{growth_summary["desc"]}</div>
              </div>
              <div class="card verdict-card">
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
                  <span class="{env_pill_cls}"><span class="bead"></span>{env_pill}</span>
                  <span style="font-size:12px;color:var(--ink-3);">환경 <b style="color:var(--risk);">{n_risk} 위험 · {n_warn} 주의</b></span>
                </div>
                <h2 style="font-size:18px;font-weight:700;color:var(--ink);">환경 상태를 확인하세요.</h2>
                <div class="card-body" style="margin-top:12px;">{tags}</div>
                <div style="margin-top:auto;padding-top:10px;font-size:11.5px;color:var(--ink-3);">업로드 센서 최근 7일 평균 기준</div>
              </div>
            </div>""",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="stat-row">
              <div class="stat"><div class="sl">{growth_summary["stat_note"]}</div><div class="sv">{growth_summary["stat_value"]}</div><div class="sx">참조 농가 표준(p25~p75)</div></div>
              <div class="stat"><div class="sl">누적 수확수</div><div class="sv">{harvest_total:,}<span style="font-size:13px;color:var(--ink-3);"> 개</span></div><div class="sx">업로드 생육·수확 조사 누계</div></div>
              <div class="stat"><div class="sl">누적 착과수</div><div class="sv">{fruit_total:,}<span style="font-size:13px;color:var(--ink-3);"> 개</span></div><div class="sx">업로드 생육·수확 조사 누계</div></div>
            </div>
            <p class="subnote">※ 환경 수치는 업로드 센서 최근 7일, 수확·착과는 업로드 파일 조사일자별 합산입니다. 표준 곡선은 `data/생육` 참조 농가 기준입니다.</p>
            """,
            unsafe_allow_html=True,
        )

        render_growth_timeseries_section(growth_chart_df, key_prefix="status")

        if dims_ready:
            st.markdown('<div class="eyebrow">Act · <span class="ko">오늘 해야 할 일</span></div>', unsafe_allow_html=True)
            actions = build_actions_from_kpis(env_kpis)
            if actions:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                for i, act in enumerate(actions, 1):
                    render_action_item(i, act["title"], act["why"], act["desc"], act["status"], act["color"])
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.success("현재 측정값 기준 긴급 조치 항목이 없습니다.")

    if dims_ready:
        with tab_forecast:
            st.markdown(
                '<div class="data-head"><h1>앞으로 전망</h1>'
                '<p>지금 추세로 갈 때의 예상입니다. 컴퓨터가 추정한 <b>참고용</b> 값이에요.</p></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <div class="forecast">
                  <div class="simple-grid">
                    <div class="scard"><div style="font-size:24px;">🗓️</div><div class="sl">예상 수확 시기</div>
                      <div class="sv">조사 {len(df)}회 기준</div><div class="sx">표준보다 약 {delay_days}일 {"늦어요" if delay_days else "유사"}</div></div>
                    <div class="scard"><div style="font-size:24px;">🌱</div><div class="sl">생육 지연 전망</div>
                      <div class="sv">{delay_days}<span style="font-size:14px;color:var(--ink-3);">일</span></div>
                      <div class="sx">환경 관리 시<br>단축 가능</div></div>
                    <div class="scard"><div style="font-size:24px;">🍅</div><div class="sl">예상 착과수</div>
                      <div class="sv">약 {fruit_total}<span style="font-size:14px;color:var(--ink-3);">개</span></div>
                      <div class="sx">현재 누계 기준</div></div>
                  </div>
                  <p class="subnote" style="margin-top:13px;">⚠️ 컴퓨터가 과거 데이터로 추정한 미래 값입니다. 현장 관찰을 우선하세요.</p>
                </div>""",
                unsafe_allow_html=True,
            )
            render_model_forecast_section(
                df,
                week_dfs,
                selected_week,
                growth_features,
                fruit_total,
            )
            with st.expander("상세 모델·XAI 분석 (SHAP · ICE · PDP · ALE)", expanded=False):
                render_xai_fn(
                    df=df, week_dfs=week_dfs, selected_week=selected_week,
                    growth_features=growth_features, sensor_df=sensor_df, yield_df=yield_df,
                )

    with tab_series:
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

    goto_tab = st.session_state.pop("dims_goto_tab", None)
    if goto_tab is not None:
        _focus_main_tab(int(goto_tab))

    render_disclaimer()

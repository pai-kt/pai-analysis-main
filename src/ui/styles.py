"""ADIMS UI styles and shared constants."""
from __future__ import annotations

import os

from src.paths import SAMPLE_DATA_DIR

APP_TITLE = "의사결정지원시스템"
APP_SUBTITLE = "시설원예 생육·환경 데이터 기반 분석·예측"
DIMS_SAMPLE_DIR = SAMPLE_DATA_DIR
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
  position:relative!important;
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
  padding:18px 22px;
  margin:10px 0 12px;
  box-shadow:var(--shadow);
  overflow:visible;
  position:relative;
  z-index:1;
}
.dims-header-row{display:flex;align-items:center;gap:20px;}
.dims-brand{display:flex;align-items:center;gap:12px;min-width:0;flex:1.15;}
.dims-brand .dot{width:12px;height:12px;border-radius:4px;background:var(--accent);display:inline-block;flex-shrink:0;}
.dims-brand-text{display:flex;flex-direction:column;gap:3px;min-width:0;}
.dims-brand-title{font-weight:800;font-size:22px;letter-spacing:-.45px;color:var(--ink);line-height:1.2;}
.dims-brand-sub{font-size:13.5px;font-weight:500;color:var(--ink-2);letter-spacing:-.1px;line-height:1.4;}
.dims-header-mid{
  flex:1;
  min-width:0;
  padding:8px 14px;
  border-left:1px solid var(--line-soft);
  border-right:1px solid var(--line-soft);
}
.dims-mid-title{font-size:14px;font-weight:700;color:var(--ink);letter-spacing:-.2px;margin-bottom:4px;}
.dims-mid-steps{display:flex;flex-wrap:wrap;align-items:center;gap:6px;font-size:12.5px;font-weight:600;color:var(--ink-2);}
.dims-mid-sep{color:var(--ink-3);font-weight:500;}
.dims-asof{text-align:right;flex-shrink:0;margin-right:48px;min-width:108px;}
.dims-asof-label{font-size:12px;color:var(--ink-3);font-weight:600;margin-bottom:2px;}
.dims-asof-value{font-size:16px;color:var(--ink);font-weight:700;letter-spacing:-.2px;}
@media(max-width:900px){
  .dims-header-mid{display:none;}
}
.st-key-theme_toggle{
  position:absolute!important;
  top:3.75rem;
  right:max(1.25rem,22px);
  z-index:20;
  width:34px!important;
  height:34px!important;
  overflow:visible!important;
}
.st-key-theme_toggle [data-testid="stButton"]{margin:0!important;}
.st-key-theme_toggle button{
  width:34px!important;
  height:34px!important;
  min-height:34px!important;
  padding:0!important;
  border-radius:10px!important;
  border:1px solid var(--line)!important;
  background:var(--surface)!important;
  color:var(--ink)!important;
  box-shadow:0 2px 8px rgba(36,50,64,.10)!important;
  transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease,background .18s ease!important;
}
.st-key-theme_toggle button:hover{
  transform:translateY(-1px);
  border-color:var(--accent)!important;
  background:var(--accent-bg)!important;
  box-shadow:0 5px 14px rgba(36,50,64,.16)!important;
}
.st-key-theme_toggle button:active{transform:translateY(0) scale(.96);}
.st-key-theme_toggle button p{
  font-family:Arial,sans-serif!important;
  font-size:19px!important;
  font-weight:400!important;
  line-height:1!important;
  margin:0!important;
}
@media(max-width:640px){
  .dims-asof{display:none;}
  .st-key-theme_toggle{top:3.7rem;}
}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow);margin-bottom:4px;}
.hero-cols [data-testid="stHorizontalBlock"]{gap:1.5rem!important;margin-top:20px!important;align-items:stretch!important;}
.hero-cols [data-testid="column"]{display:flex!important;flex-direction:column!important;}
.hero-cols [data-testid="column"] > div{width:100%!important;flex:1!important;display:flex!important;flex-direction:column!important;}
.hero-cols [data-testid="column"] [data-testid="stMarkdown"]{flex:1!important;display:flex!important;flex-direction:column!important;}
.hero-cols [data-testid="column"] [data-testid="stMarkdown"] > div{width:100%!important;flex:1!important;display:flex!important;flex-direction:column!important;}
.hero-cols [data-testid="stPlotlyChart"]{margin-top:8px;}
.hero-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px;margin-top:20px;align-items:stretch;}
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
.data-head h1{font-size:26px;font-weight:800;letter-spacing:-.55px;color:var(--ink)!important;margin:0;line-height:1.25;}
.data-head p{color:var(--ink-2);font-size:14.5px;margin-top:8px;line-height:1.5;}
.data-hero{
  background:linear-gradient(135deg,var(--surface) 0%,var(--accent-bg) 100%);
  border:1px solid var(--line);
  border-radius:var(--radius);
  padding:22px 24px;
  margin:8px 0 18px;
  box-shadow:var(--shadow);
}
.data-hero-kicker{
  font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
  color:var(--accent);margin-bottom:8px;
}
.data-field-label{
  font-size:12px;font-weight:700;color:var(--ink-3);margin:0 0 8px;letter-spacing:-.1px;
}
.data-note-card,.data-status-card{
  margin:4px 0 16px;padding:12px 16px;border-radius:12px;
  background:var(--accent-bg);border:1px solid color-mix(in srgb,var(--accent) 22%,var(--line));
  color:var(--ink-2);font-size:13px;font-weight:600;line-height:1.45;
}
.data-status-card{background:var(--surface);}
.st-key-upload_panel_sensor,
.st-key-upload_panel_yield,
.st-key-upload_panel_sensor_demo,
.st-key-upload_panel_yield_demo{
  background:var(--surface);
  border:1px solid var(--line);
  border-radius:var(--radius);
  padding:16px 16px 10px;
  box-shadow:var(--shadow);
  height:100%;
  box-sizing:border-box;
  display:flex;
  flex-direction:column;
}
div[data-testid="stHorizontalBlock"]:has(.st-key-upload_panel_sensor),
div[data-testid="stHorizontalBlock"]:has(.st-key-upload_panel_sensor_demo){
  gap:10px!important;
  align-items:stretch!important;
}
div[data-testid="stHorizontalBlock"]:has(.st-key-upload_panel_sensor) > div[data-testid="stColumn"],
div[data-testid="stHorizontalBlock"]:has(.st-key-upload_panel_sensor_demo) > div[data-testid="stColumn"]{
  display:flex!important;
  flex-direction:column!important;
}
div[data-testid="stHorizontalBlock"]:has(.st-key-upload_panel_sensor) > div[data-testid="stColumn"] > div,
div[data-testid="stHorizontalBlock"]:has(.st-key-upload_panel_sensor_demo) > div[data-testid="stColumn"] > div{
  height:100%!important;
  display:flex!important;
  flex-direction:column!important;
}
.st-key-upload_panel_sensor [data-testid="stFileUploader"],
.st-key-upload_panel_yield [data-testid="stFileUploader"],
.st-key-upload_panel_sensor_demo [data-testid="stFileUploader"],
.st-key-upload_panel_yield_demo [data-testid="stFileUploader"]{
  margin-top:auto;
}
.upload-panel-head{margin-bottom:4px;}
.upload-panel-title{font-size:16px;font-weight:800;color:var(--ink);letter-spacing:-.3px;}
.env-card-spacer{height:36px;}
.st-key-data_run_card{
  background:var(--surface);
  border:1px solid var(--line);
  border-radius:var(--radius);
  padding:16px 18px;
  margin-top:8px;
  box-shadow:var(--shadow);
}
.data-run-copy{padding-top:6px;}
.data-run-title{font-size:15px;font-weight:800;color:var(--ink);letter-spacing:-.2px;}
.data-run-desc{font-size:12.5px;color:var(--ink-3);margin-top:4px;font-weight:500;}
.data-run-note{font-size:12px;color:var(--ink-2);margin-top:8px;line-height:1.45;font-weight:500;}
.analysis-progress-card{
  margin:14px 0 10px;padding:14px 16px;border-radius:12px;
  background:var(--accent-bg);border:1px solid color-mix(in srgb,var(--accent) 24%,var(--line));
}
.analysis-progress-title{font-size:14px;font-weight:800;color:var(--ink);letter-spacing:-.2px;}
.analysis-progress-desc{font-size:12.5px;color:var(--ink-2);margin-top:4px;font-weight:500;}
.st-key-rda_location_card,
[class*="st-key-rda_setup_"],
[class*="st-key-rda_search_card_"]{
  background:var(--surface);
  border:1px solid var(--line);
  border-radius:var(--radius);
  padding:20px 22px;
  box-shadow:var(--shadow);
  margin:12px 0 16px;
}
.rda-section-head{display:flex;align-items:center;gap:12px;margin-bottom:16px;}
.rda-section-head--compact{margin-bottom:10px;}
.rda-step{
  display:flex;align-items:center;justify-content:center;flex:0 0 auto;
  width:34px;height:34px;border-radius:10px;
  background:var(--accent-bg);color:var(--accent);
  font-size:12px;font-weight:800;
}
.rda-section-kicker{
  font-size:10.5px;font-weight:800;letter-spacing:.1em;
  text-transform:uppercase;color:var(--accent);line-height:1.2;
}
.rda-section-title{font-size:17px;font-weight:800;color:var(--ink);letter-spacing:-.3px;margin-top:2px;}
.rda-section-desc{font-size:12.5px;font-weight:500;color:var(--ink-3);margin-top:3px;}
.st-key-rda_location_card div[role="radiogroup"],
[class*="st-key-rda_setup_"] div[role="radiogroup"]{
  gap:8px!important;
}
.st-key-rda_location_card label[data-baseweb="radio"],
[class*="st-key-rda_setup_"] label[data-baseweb="radio"]{
  background:var(--bg);
  border:1px solid var(--line);
  border-radius:9px;
  padding:7px 11px!important;
  transition:background .18s ease,border-color .18s ease;
}
.st-key-rda_location_card label[data-baseweb="radio"]:hover,
[class*="st-key-rda_setup_"] label[data-baseweb="radio"]:hover{
  background:var(--accent-bg);
  border-color:var(--accent);
}
.triage{display:flex;gap:12px;align-items:center;margin-top:16px;margin-bottom:4px;padding:14px 18px;background:var(--surface);border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow);}
.triage.risk{background:var(--risk-bg);border-color:color-mix(in srgb,var(--risk) 35%,var(--line));}
.triage.warn{background:var(--warn-bg);border-color:color-mix(in srgb,var(--warn) 35%,var(--line));}
.triage .tt{font-size:13.5px;color:var(--ink);font-weight:600;line-height:1.5;}
.triage.risk .tt b{color:var(--risk);}
.triage.warn .tt b{color:var(--warn);}
.triage.ok .tt b{color:var(--ok);}
.pill{display:inline-flex;align-items:center;gap:8px;font-weight:700;font-size:14px;padding:7px 14px;border-radius:999px;background:var(--warn-bg);color:var(--warn);}
.pill.acc{background:var(--accent-bg);color:var(--accent);}
.pill .bead{width:9px;height:9px;border-radius:50%;background:currentColor;box-shadow:0 0 0 4px color-mix(in srgb,currentColor 18%,transparent);}
.stat-row{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:20px;}
.stat-row.cols-2{grid-template-columns:repeat(2,1fr);}
@media(max-width:880px){.stat-row{grid-template-columns:1fr;}}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:15px 17px;box-shadow:var(--shadow);}
.stat .sl{font-size:11px;color:var(--ink-3);font-weight:600;}
.stat .sv{font-size:22px;font-weight:700;margin-top:5px;color:var(--ink);}
.stat .sx{font-size:11.5px;color:var(--ink-2);margin-top:3px;}
.stat .prog{height:6px;border-radius:4px;background:var(--bg);overflow:hidden;margin-top:10px;}
.stat .prog i{display:block;height:100%;border-radius:4px;background:var(--accent);}
.tag{font-size:12px;font-weight:600;padding:5px 10px;border-radius:8px;display:inline-block;margin:3px;}
.tag.r{color:var(--risk);background:var(--risk-bg)} .tag.w{color:var(--warn);background:var(--warn-bg)}
.tag.ok{color:var(--ok);background:var(--ok-bg)}
.tag.high{color:var(--warn);background:var(--warn-bg)}
.tag.low{color:var(--accent);background:var(--accent-bg)}
.status-tag-row{display:flex;flex-wrap:wrap;align-items:center;gap:3px;min-height:35px;}
.status-tag-row + .status-tag-row{margin-top:3px;}
.act{display:grid;grid-template-columns:1fr auto;gap:16px;align-items:center;padding:16px 20px;border-bottom:1px solid var(--line-soft);}
.act:last-child{border-bottom:0}
.act-body .h{font-size:14.5px;font-weight:700;color:var(--ink);}
.act-body .d{font-size:13px;color:var(--ink-2);margin-top:3px;}
.act-right{text-align:right;}
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
.stage-bar{display:flex;width:100%;height:48px;border-radius:11px;overflow:hidden;border:1px solid var(--line);box-shadow:var(--shadow);margin-top:14px;}
.stage-seg{box-sizing:border-box;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:#fff;text-align:center;line-height:1.25;padding:4px 6px;word-break:keep-all;flex-shrink:0;}
.stage-seg--s1{font-size:10.5px;}
.stage-tbl{width:100%;border-collapse:collapse;font-size:12.5px;}
.stage-tbl th,.stage-tbl td{padding:11px 14px;text-align:left;border-bottom:1px solid var(--line-soft);color:var(--ink);}
.stage-tbl th{font-size:11px;font-weight:700;color:var(--ink-3);background:var(--bg);}
.rda-result-tbl tr.rda-row-match td{background:var(--warn-bg);}
.rda-result-scroll{max-height:380px;overflow:auto;border-radius:var(--radius);}
.rda-result-scroll .rda-result-tbl{min-width:960px;}
.rda-result-scroll .rda-result-tbl thead th{position:sticky;top:0;z-index:2;background:var(--bg);box-shadow:0 1px 0 var(--line-soft);white-space:nowrap;}
.rda-result-scroll .rda-result-tbl th,
.rda-result-scroll .rda-result-tbl td{text-align:center;white-space:nowrap;}
.rda-compare-tbl th,.rda-compare-tbl td{text-align:center;}
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
.forecast-flow{margin-top:4px;padding:4px 2px 8px;}
.forecast-flow .ff-row{display:flex;flex-wrap:wrap;justify-content:center;gap:12px;margin:0;}
.forecast-flow .ff-box{
  min-width:150px;max-width:220px;flex:1 1 150px;
  background:var(--surface);border:1px solid var(--line);border-radius:12px;
  padding:12px 14px;text-align:center;box-shadow:var(--shadow);
}
.forecast-flow .ff-box .ff-t{font-size:12.5px;font-weight:700;color:var(--ink);line-height:1.35;}
.forecast-flow .ff-box .ff-s{font-size:11px;color:var(--ink-3);margin-top:5px;line-height:1.4;}
.forecast-flow .ff-box.ff-src{background:var(--bg);}
.forecast-flow .ff-box.ff-x{background:var(--accent-bg);border-color:var(--line);}
.forecast-flow .ff-box.ff-model{background:var(--accent);border-color:var(--accent);}
.forecast-flow .ff-box.ff-model .ff-t,
.forecast-flow .ff-box.ff-model .ff-s{color:#fff;}
.forecast-flow .ff-box.ff-model .ff-s{opacity:.9;}
.forecast-flow .ff-box.ff-out{border:1.5px solid var(--accent);}
.forecast-flow .ff-arrow{
  text-align:center;color:var(--ink-3);font-size:14px;line-height:1;padding:6px 0 8px;
  user-select:none;
}
.forecast-flow .ff-note{font-size:11.5px;color:var(--ink-3);margin-top:12px;line-height:1.5;}
.disclaimer{margin:34px 0 12px;padding:16px 20px;background:#EEF1F5;border-radius:12px;display:flex;gap:12px;}
.disclaimer .dt{font-size:12.5px;color:var(--ink-2);line-height:1.6;}
.copyright{margin:0 0 28px;padding:14px 4px 6px;text-align:center;font-size:11.5px;color:var(--ink-3);line-height:1.65;border-top:1px solid var(--line-soft);}
.copyright b{color:var(--ink-2);font-weight:600;}
.run-bar{display:flex;align-items:center;gap:18px;margin-top:18px;padding:16px 22px;background:var(--accent-bg);border-radius:var(--radius);}
.mchips{display:flex;flex-wrap:wrap;gap:7px;margin:8px 0;}
.mchip{font-size:12px;font-weight:600;color:var(--ink-2);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:7px 12px;}
.mchip.req{color:var(--ink-2);background:var(--bg);border-color:var(--line);}
.mchip.ok{color:var(--ok);background:var(--ok-bg);border-color:#C8E2CD;}
.mchip.miss{color:var(--risk);background:var(--risk-bg);border-color:#F0C7C8;}
.req-vars{margin:6px 0 10px;}
.req-vars .req-label{font-size:11px;font-weight:700;color:var(--ink-3);margin-bottom:6px;}
.map-legend{font-size:11.5px;color:var(--ink-3);margin:4px 0 10px;}
.map-legend b.ok{color:var(--ok);} .map-legend b.miss{color:var(--risk);}
.dims-top-spacer{height:6px;}
.subnote{font-size:11.5px;color:var(--ink-3);margin:9px 2px 0;}
[data-testid="stTabs"]{margin-top:8px;margin-bottom:2rem;}
[data-testid="stTabs"] [data-baseweb="tab-list"]{
  gap:6px;
  border-bottom:none!important;
  background:var(--surface);
  border:1px solid var(--line);
  border-radius:14px;
  padding:6px;
  box-shadow:var(--shadow);
  margin-top:2px;
}
[data-testid="stTabs"] [data-baseweb="tab-border"],
[data-testid="stTabs"] [data-baseweb="tab-highlight"]{
  display:none!important;
}
[data-testid="stTabs"] [data-baseweb="tab"]{
  font-size:14px!important;
  font-weight:700!important;
  letter-spacing:-.2px;
  color:var(--ink-2)!important;
  padding:10px 18px!important;
  min-height:40px!important;
  border:none!important;
  border-bottom:none!important;
  border-radius:10px!important;
  background:transparent!important;
  transition:background .18s ease,color .18s ease,box-shadow .18s ease,transform .18s ease!important;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover{
  color:var(--accent)!important;
  background:var(--accent-bg)!important;
}
[data-testid="stTabs"] [aria-selected="true"]{
  color:#fff!important;
  background:var(--accent)!important;
  border-bottom:none!important;
  box-shadow:0 3px 10px rgba(78,121,167,.28)!important;
}
[data-testid="stTabs"] [aria-selected="true"]:hover{
  color:#fff!important;
  background:var(--accent)!important;
}
[data-testid="stPlotlyChart"]{margin-bottom:12px;}
.tab-bottom-spacer{height:48px;}
.stButton>button[kind="primary"]{background:var(--accent)!important;color:#fff!important;font-weight:700!important;border-radius:10px!important;padding:12px 24px!important;box-shadow:0 4px 12px rgba(78,121,167,.3)!important;border:none!important;}
.stButton>button[kind="primary"]:disabled,.stButton>button:disabled{background:#C5CDD6!important;color:#fff!important;box-shadow:none!important;cursor:not-allowed!important;opacity:1!important;border:none!important;}
.data-source-note{font-size:12px;color:var(--ink-2);margin:4px 0 14px;}
div[data-testid="stFileUploader"] section{
  border:1.5px dashed color-mix(in srgb,var(--accent) 28%,var(--line))!important;
  border-radius:12px!important;
  background:var(--bg)!important;
  min-height:118px!important;
}
div[data-testid="stFileUploader"] section:hover{
  border-color:var(--accent)!important;
  background:var(--accent-bg)!important;
}
.gps-allow-label{
  display:flex;align-items:center;min-height:40px;
  font-size:13px;font-weight:600;color:var(--ink-2);
  letter-spacing:-.1px;white-space:nowrap;
}
/* GPS 버튼 + (위치 접근 허용) 라벨 한 줄 정렬 */
div[data-testid="stHorizontalBlock"]:has(.gps-allow-label){
  align-items:center!important;
  gap:0.35rem!important;
  max-width:280px;
}
div[data-testid="stHorizontalBlock"]:has(.gps-allow-label) iframe{
  width:42px!important;
  min-width:42px!important;
}
</style>
"""


DARK_MODE_CSS = """
<style>
:root{
  color-scheme:dark;
  --bg:#111827; --surface:#1F2937; --line:#374151; --line-soft:#303B4B;
  --ink:#F3F4F6; --ink-2:#CBD5E1; --ink-3:#94A3B8;
  --accent:#7FA8D1; --accent-bg:#25384D;
  --ok:#78C987; --ok-bg:#203C2B;
  --warn:#F0B554; --warn-bg:#49371E;
  --risk:#F0787A; --risk-bg:#48272B;
  --shadow:0 1px 2px rgba(0,0,0,.22),0 8px 22px rgba(0,0,0,.24);
}
.forecast{background:#182231!important;}
.forecast-model{background:#1D3045!important;}
.forecast-flow .ff-box.ff-x{background:#2A3A4D!important;}
.forecast-flow .ff-box.ff-model .ff-t,
.forecast-flow .ff-box.ff-model .ff-s{color:#F8FAFC!important;}
.disclaimer{background:#263140!important;}
.g-track{background:#3B4655!important;}
.g-pin{border-color:#1F2937!important;box-shadow:0 0 0 1.5px rgba(255,255,255,.28)!important;}
.scard.model .sv{color:#8CB5DE!important;}

/* Streamlit 위젯 글자색 (config.toml light 테마 잔여색 덮기) */
.stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stCaptionContainer"] p{
  color:var(--ink-3)!important;
}
.stApp [data-testid="stWidgetLabel"],
.stApp [data-testid="stWidgetLabel"] p,
.stApp [data-testid="stMarkdownContainer"] p{
  color:var(--ink)!important;
}

/* 라디오 / 체크박스 */
.stApp div[role="radiogroup"] label,
.stApp div[role="radiogroup"] label p,
.stApp label[data-baseweb="radio"],
.stApp label[data-baseweb="radio"] p,
.stApp label[data-baseweb="checkbox"],
.stApp label[data-baseweb="checkbox"] p{
  color:var(--ink-2)!important;
  -webkit-text-fill-color:var(--ink-2)!important;
  opacity:1!important;
}
.stApp div[role="radiogroup"] label[data-checked="true"] p,
.stApp label[data-baseweb="radio"][data-checked="true"] p{
  color:var(--ink)!important;
  -webkit-text-fill-color:var(--ink)!important;
}
/* 활성 탭 글자 유지 */
[data-testid="stTabs"] [aria-selected="true"],
[data-testid="stTabs"] [aria-selected="true"] p{
  color:#fff!important;
  -webkit-text-fill-color:#fff!important;
}

/* Select / Input / Number */
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea,
[data-baseweb="select"] > div,
[data-baseweb="popover"],
[data-baseweb="menu"],
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea{
  background:var(--surface)!important;
  color:var(--ink)!important;
  -webkit-text-fill-color:var(--ink)!important;
  border-color:var(--line)!important;
}
[data-baseweb="select"] > div{
  background:var(--bg)!important;
  border:1px solid var(--line)!important;
}
[data-baseweb="select"] span,
[data-baseweb="select"] div,
[data-testid="stSelectbox"] span,
[data-testid="stSelectbox"] div[data-baseweb="select"] *{
  color:var(--ink)!important;
  -webkit-text-fill-color:var(--ink)!important;
  opacity:1!important;
}
[data-baseweb="popover"] li,
[data-baseweb="popover"] [role="option"],
[data-baseweb="menu"] li{
  background:var(--surface)!important;
  color:var(--ink)!important;
  -webkit-text-fill-color:var(--ink)!important;
}
[data-baseweb="popover"] li:hover,
[data-baseweb="menu"] li:hover{
  background:var(--accent-bg)!important;
}

/* File uploader — 드롭존 안내문 */
div[data-testid="stFileUploader"] section{
  background:var(--bg)!important;
  border-color:color-mix(in srgb,var(--accent) 40%,var(--line))!important;
}
div[data-testid="stFileUploader"] section:hover{
  background:var(--accent-bg)!important;
  border-color:var(--accent)!important;
}
div[data-testid="stFileUploader"] section,
div[data-testid="stFileUploader"] section *:not(button):not(button *){
  color:var(--ink-2)!important;
  -webkit-text-fill-color:var(--ink-2)!important;
  opacity:1!important;
}
div[data-testid="stFileUploader"] small,
div[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] small{
  color:var(--ink-3)!important;
  -webkit-text-fill-color:var(--ink-3)!important;
}
/* Browse files 버튼 — 밝은 배경 + 어두운 글자 */
div[data-testid="stFileUploader"] button,
div[data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"],
div[data-testid="stFileUploader"] [data-baseweb="button"]{
  background:#E8EEF5!important;
  background-color:#E8EEF5!important;
  color:#1F2937!important;
  border:1px solid #9AA8B8!important;
  font-weight:700!important;
}
div[data-testid="stFileUploader"] button *,
div[data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"] *,
div[data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"] p,
div[data-testid="stFileUploader"] [data-baseweb="button"] *,
div[data-testid="stFileUploader"] [data-baseweb="button"] p{
  color:#1F2937!important;
  -webkit-text-fill-color:#1F2937!important;
}
div[data-testid="stFileUploader"] button:hover,
div[data-testid="stFileUploader"] [data-baseweb="button"]:hover{
  background:#D5E3F2!important;
  border-color:var(--accent)!important;
}

/* Primary / Disabled 버튼 */
.stButton>button[kind="primary"]{
  background:var(--accent)!important;
  color:#0B1220!important;
  font-weight:800!important;
}
.stButton>button[kind="primary"] p,
.stButton>button[kind="primary"] span{
  color:#0B1220!important;
  -webkit-text-fill-color:#0B1220!important;
}
.stButton>button[kind="primary"]:disabled,
.stButton>button:disabled{
  background:#3B4655!important;
  color:#CBD5E1!important;
  border:1px solid #4B5563!important;
  opacity:1!important;
}
.stButton>button[kind="primary]:disabled p,
.stButton>button:disabled p,
.stButton>button[kind="primary"]:disabled span,
.stButton>button:disabled span{
  color:#CBD5E1!important;
  -webkit-text-fill-color:#CBD5E1!important;
}
.stButton>button[kind="secondary"],
.stButton>button:not([kind="primary"]){
  background:var(--surface)!important;
  color:var(--ink)!important;
  border:1px solid var(--line)!important;
}
.stButton>button[kind="secondary"] p,
.stButton>button:not([kind="primary"]) p{
  color:var(--ink)!important;
  -webkit-text-fill-color:var(--ink)!important;
}

/* Expander / Alert / Info */
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span{
  color:var(--ink)!important;
}
[data-testid="stAlert"]{color:var(--ink)!important;}
[data-testid="stDataFrame"],
[data-testid="stTable"]{color:var(--ink)!important;}
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



MAIN_TAB_LABELS = ["1 · 데이터", "2 · 환경 설정", "3 · 내 농가 진단", "4 · 예측"]
MAIN_TAB_ENV = 1
MAIN_TAB_STATUS = 2

GROWTH_CHART_PRIMARY = ["착과수", "초장", "엽수", "수확수"]
GROWTH_CHART_EXTRA = ["생장길이", "엽장", "엽폭", "줄기굵기", "화방높이"]

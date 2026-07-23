"""Tab 4 · 예측."""
from __future__ import annotations

import streamlit as st
import pandas as pd

from src.ui.common import render_tab_hero


def _upload_forecast_cache_key(upload_df: pd.DataFrame, selected_week: int, fruit_total: int) -> str:
    from src.model_store import MANIFEST_PATH

    model_version = MANIFEST_PATH.stat().st_mtime_ns if MANIFEST_PATH.exists() else 0
    frame = upload_df.copy()
    frame["조사일자"] = pd.to_datetime(frame["조사일자"], errors="coerce")
    frame = frame.dropna(subset=["조사일자"]).sort_values("조사일자")
    if frame.empty:
        return f"empty-{selected_week}-{fruit_total}-{model_version}"
    latest = frame.iloc[-1]
    env_cols = sorted(c for c in frame.columns if "주평균" in c or "주평균" in str(c))
    env_sig = tuple(
        round(float(latest[c]), 3) if c in latest.index and pd.notna(latest[c]) else None
        for c in env_cols[:7]
    )
    return (
        f"{len(frame)}|{latest['조사일자'].date()}|{selected_week}|"
        f"{fruit_total}|{env_sig}|{model_version}"
    )


# --- 모델 입출력 흐름 보기 (일시 비활성) ---
# def _fmt_span(start, end) -> str:
#     try:
#         s = pd.to_datetime(start).strftime("%Y-%m-%d")
#         e = pd.to_datetime(end).strftime("%Y-%m-%d")
#         return f"{s} ~ {e}"
#     except Exception:
#         return "—"
#
#
# def _fmt_md(d) -> str:
#     try:
#         return pd.to_datetime(d).strftime("%m-%d")
#     except Exception:
#         return "—"
#
#
# def _delta_text(pred, actual, unit: str = "") -> str:
#     if pred is None or actual is None:
#         return "실측 —"
#     diff = float(pred) - float(actual)
#     sign = "+" if diff >= 0 else ""
#     if unit == "cm":
#         return f"실측 {actual:.0f} · {sign}{diff:.0f}"
#     return f"실측 {actual:.0f} · {sign}{diff:.1f}"
#
#
# def _box(title: str, sub: str, kind: str = "") -> str:
#     cls = f"ff-box {kind}".strip()
#     return f'<div class="{cls}"><div class="ff-t">{title}</div><div class="ff-s">{sub}</div></div>'
#
#
# def render_forecast_pipeline_expander(
#     summary: dict,
#     upload_df: pd.DataFrame,
#     selected_week: int,
#     fruit_total: int,
#     *,
#     sensor_df=None,
#     date_col_sensor: str | None = None,
# ):
#     """모델 입출력 흐름을 드롭다운으로 표시 (R² 미표시)."""
#     week = int(summary.get("selected_week") or selected_week)
#     week_days = week * 7
#     targets = summary.get("targets") or {}
#     t_h = targets.get("수확수") or {}
#     t_f = targets.get("착과수") or {}
#     t_g = targets.get("초장") or {}
#     latest_date = summary.get("latest_date") or "—"
#     delay_m = int(summary.get("model_delay_days") or 0)
#     projected = int(summary.get("projected_fruit_total") or fruit_total)
#
#     frame = upload_df.copy()
#     frame["조사일자"] = pd.to_datetime(frame["조사일자"], errors="coerce")
#     frame = frame.dropna(subset=["조사일자"]).sort_values("조사일자")
#     yield_rows = len(frame)
#     yield_span = _fmt_span(frame["조사일자"].min(), frame["조사일자"].max()) if yield_rows else "—"
#
#     latest = frame.iloc[-1] if yield_rows else None
#     win_start = (
#         (pd.to_datetime(latest["조사일자"]) - pd.Timedelta(days=week_days)).strftime("%m-%d")
#         if latest is not None
#         else "—"
#     )
#     win_end = _fmt_md(latest["조사일자"]) if latest is not None else "—"
#
#     sensor_rows = 0
#     sensor_span = "—"
#     sensor_win_rows = 0
#     if sensor_df is not None and date_col_sensor and date_col_sensor in sensor_df.columns and latest is not None:
#         s = sensor_df.copy()
#         s[date_col_sensor] = pd.to_datetime(s[date_col_sensor], errors="coerce")
#         s = s.dropna(subset=[date_col_sensor])
#         sensor_rows = len(s)
#         if sensor_rows:
#             sensor_span = _fmt_span(s[date_col_sensor].min(), s[date_col_sensor].max())
#             ld = pd.to_datetime(latest["조사일자"])
#             start = ld - pd.Timedelta(days=week_days)
#             sensor_win_rows = int(((s[date_col_sensor] >= start) & (s[date_col_sensor] <= ld)).sum())
#
#     act_h = t_h.get("actual")
#     act_f = t_f.get("actual")
#     act_g = t_g.get("actual")
#     latest_sub = (
#         f"실측 수확{act_h:.0f} · 착과{act_f:.0f} · 초장{act_g:.0f}"
#         if act_h is not None and act_f is not None and act_g is not None
#         else f"조사일 {latest_date}"
#     )
#
#     n_h = t_h.get("n_train")
#     n_f = t_f.get("n_train")
#     n_g = t_g.get("n_train")
#     pred_h = t_h.get("pred")
#     pred_f = t_f.get("pred")
#     pred_g = t_g.get("pred")
#
#     sensor_title = (
#         f"환경센서 {sensor_rows:,}행" if sensor_rows else "환경센서"
#     )
#     sensor_sub = sensor_span if sensor_rows else "온도·습도·CO₂·일사"
#     yield_title = f"생육·수확 {yield_rows:,}행"
#     roll_sub = (
#         f"창: {win_start}~{win_end}"
#         + (f" · {sensor_win_rows:,}행" if sensor_win_rows else "")
#     )
#
#     if act_f is not None and pred_f is not None:
#         proj_sub = f"{fruit_total:,}−{act_f:.0f}+{pred_f:.1f}"
#     else:
#         proj_sub = "누계−실측+ŷ"
#
#     html = f"""
#     <div class="forecast-flow">
#       <div class="ff-row">
#         {_box(sensor_title, sensor_sub, "ff-src")}
#         {_box(yield_title, yield_span, "ff-src")}
#       </div>
#       <div class="ff-arrow">↓</div>
#       <div class="ff-row">
#         {_box(f"{week}주 롤링 ({week_days}일)", roll_sub)}
#       </div>
#       <div class="ff-arrow">↓</div>
#       <div class="ff-row">
#         {_box(f"최신 1행 {win_end}", latest_sub)}
#       </div>
#       <div class="ff-arrow">↓</div>
#       <div class="ff-row">
#         {_box("입력 X (7피처)", "주야 온습CO₂ + 일사", "ff-x")}
#       </div>
#       <div class="ff-arrow">↓</div>
#       <div class="ff-row">
#         {_box("RF 수확수", f"n_train={n_h}" if n_h else "RandomForest", "ff-model")}
#         {_box("RF 착과수", f"n_train={n_f}" if n_f else "RandomForest", "ff-model")}
#         {_box("RF 초장", f"n_train={n_g}" if n_g else "RandomForest", "ff-model")}
#       </div>
#       <div class="ff-arrow">↓</div>
#       <div class="ff-row">
#         {_box(
#             f"ŷ={pred_h:.1f}개" if pred_h is not None else "ŷ 수확수",
#             _delta_text(pred_h, act_h),
#             "ff-out",
#         )}
#         {_box(
#             f"ŷ={pred_f:.1f}개" if pred_f is not None else "ŷ 착과수",
#             _delta_text(pred_f, act_f),
#             "ff-out",
#         )}
#         {_box(
#             f"ŷ={pred_g:.0f}cm" if pred_g is not None else "ŷ 초장",
#             _delta_text(pred_g, act_g, "cm"),
#             "ff-out",
#         )}
#       </div>
#       <div class="ff-arrow">↓</div>
#       <div class="ff-row">
#         {_box(f"지연 {delay_m}일", "ŷ초장 ≥ 표준 p50" if delay_m == 0 else "ŷ초장 &lt; 표준 p50", "ff-out")}
#         {_box(f"누적추정 {projected:,}", proj_sub, "ff-out")}
#       </div>
#     </div>
#     """
#     with st.expander("모델 입출력 흐름 보기", expanded=False):
#         st.markdown(html, unsafe_allow_html=True)


def render_model_forecast_section(
    upload_df,
    week_dfs: dict,
    selected_week: int,
    growth_features: list[str],
    fruit_total: int,
    *,
    sensor_df=None,
    date_col_sensor: str | None = None,
):
    """기존 전망 카드 아래 — RandomForest 모델 예측 카드."""
    from src.reference_training_data import build_model_forecast_summary

    cache_key = _upload_forecast_cache_key(upload_df, selected_week, fruit_total)
    if (
        st.session_state.get("model_forecast_cache_key") == cache_key
        and st.session_state.get("model_forecast_summary")
    ):
        summary = st.session_state.model_forecast_summary
    else:
        with st.spinner("저장된 RandomForest 모델로 예측 중…"):
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
        st.caption(
            "모델 예측을 계산할 수 없습니다. `python train_reference_models.py`로 "
            "`models/` 폴더에 사전 학습 모델을 생성했는지 확인해 주세요."
        )
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
        f'<span style="color:var(--ink-3);">모델 추정치</span> · {week}주 환경 입력<br>'
        f'{summary["harvest_note"]}'
        if t_harvest else ""
    )
    if t_harvest and t_harvest.get("actual") is not None:
        harvest_sx += f'<br>동일 조사일 실측 {t_harvest["actual"]:.0f}개 → 모델 {t_harvest["pred"]:.0f}개'

    delay_sv = f'{delay_m}<span style="font-size:14px;color:var(--ink-3);">일</span>'
    delay_sx = '<span style="color:var(--ink-3);">모델 추정 초장</span> · 표준곡선(p50) 대비'
    if t_height:
        delay_sx += f'<br>추정 초장 {t_height["pred"]:.1f}cm'
        if t_height.get("actual") is not None:
            delay_sx += f' (실측 {t_height["actual"]:.1f}cm)'

    fruit_sv = f'{t_fruit.get("pred", 0):.0f}<span style="font-size:14px;color:var(--ink-3);"> 개</span>' if t_fruit else "—"
    fruit_sx = (
        f'<span style="color:var(--ink-3);">모델 추정치</span> · {summary["latest_date"]} · {week}주 환경'
        if t_fruit else ""
    )
    if t_fruit:
        if t_fruit.get("actual") is not None:
            fruit_sx += f'<br>동일 조사일 실측 {t_fruit["actual"]:.0f}개'
        fruit_sx += (
            f'<br><span style="color:var(--ink-3);">작기 누적 추정</span> '
            f'약 {summary["projected_fruit_total"]:,}개'
            f' <span style="font-size:11px;">(누계−마지막 실측+모델 추정)</span>'
        )

    if info.get("ref_rows"):
        ref_label = (
            f"참조 {info['ref_farms']}농가 {info['ref_rows']:,}건"
            if info.get("ref_farms")
            else f"참조 {info['ref_rows']:,}건"
        )
        train_note = f"{ref_label} 사전 학습 · 업로드 최근 조사 1행 추정"
    else:
        train_note = "사전 학습 모델 없음"

    st.markdown(
        f"""
        <div class="forecast-model">
          <p class="model-head">🤖 RandomForest · {train_note}</p>
          <p class="subnote" style="margin:0 0 12px;color:var(--ink-3);">
            사전 학습 모델 <b>추정치</b>입니다. (다음 조사 예측 아님)
          </p>
          <div class="simple-grid">
            <div class="scard model">
              <div style="font-size:24px;">📈</div>
              <div class="sl">모델 추정 · 수확수</div>
              <div class="sv">{harvest_sv}</div>
              <div class="sx">{harvest_sx}</div>
            </div>
            <div class="scard model">
              <div style="font-size:24px;">🌿</div>
              <div class="sl">모델 추정 · 생육 지연</div>
              <div class="sv">{delay_sv}</div>
              <div class="sx">{delay_sx}</div>
            </div>
            <div class="scard model">
              <div style="font-size:24px;">🍅</div>
              <div class="sl">모델 추정 · 착과수</div>
              <div class="sv">{fruit_sv}</div>
              <div class="sx">{fruit_sx}</div>
            </div>
          </div>
          <p class="subnote" style="margin-top:13px;">
            ※ <code>models/</code>에 저장된 RandomForest를 불러와
            <b>최근 조사일({summary["latest_date"]})</b>의 <b>{week}주 환경</b> 1행만 입력해 추정합니다.
            실행 시 재학습하지 않으며, 참조 데이터로 <b>사전 학습</b>된 모델을 사용합니다.
            수확수·착과수 숫자는 <b>다음 조사 예측이 아닌 모델 추정치</b>이고,
            생육 지연은 <b>모델이 추정한 초장</b>을 표준 곡선과 비교한 값입니다.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # render_forecast_pipeline_expander(
    #     summary,
    #     upload_df,
    #     selected_week,
    #     fruit_total,
    #     sensor_df=sensor_df,
    #     date_col_sensor=date_col_sensor,
    # )


def render_forecast_tab(
    *,
    dims_ready: bool,
    df,
    week_dfs: dict,
    selected_week: int,
    growth_features: list[str],
    fruit_total: int,
    delay_days: int = 0,
    sensor_df=None,
    date_col_sensor: str | None = None,
):
    """예측 탭 본문."""
    render_tab_hero(
        "Forecast · 예측",
        "앞으로의 전망을 확인하세요",
        "지금 추세로 갈 때의 예상입니다. 모델이 추정한 <b>참고용</b> 값이에요.",
    )
    if not dims_ready or df is None:
        st.info("데이터 탭에서 「분석 결과 보기」를 실행하면 전망이 표시됩니다.")
        return

    render_model_forecast_section(
        df,
        week_dfs,
        selected_week,
        growth_features,
        fruit_total,
        sensor_df=sensor_df,
        date_col_sensor=date_col_sensor,
    )

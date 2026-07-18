"""Tab 4 · 예측."""
from __future__ import annotations

import streamlit as st
import pandas as pd

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


def render_model_forecast_section(
    upload_df,
    week_dfs: dict,
    selected_week: int,
    growth_features: list[str],
    fruit_total: int,
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
        f'{summary["harvest_note"]}<br>학습 검증 R² {t_harvest["r2"]:.2f}'
        if t_harvest else ""
    )
    if t_harvest and t_harvest.get("actual") is not None:
        harvest_sx += f'<br>동일 조사일 실측 {t_harvest["actual"]:.0f}개 → 모델 {t_harvest["pred"]:.0f}개'

    delay_sv = f'{delay_m}<span style="font-size:14px;color:var(--ink-3);">일</span>'
    delay_sx = '<span style="color:var(--ink-3);">모델 추정 초장</span> · 표준곡선(p50) 대비'
    if t_height:
        delay_sx += f'<br>추정 초장 {t_height["pred"]:.1f}cm · 학습 검증 R² {t_height["r2"]:.2f}'
        if t_height.get("actual") is not None:
            delay_sx += f' (실측 {t_height["actual"]:.1f}cm)'

    fruit_sv = f'{t_fruit.get("pred", 0):.0f}<span style="font-size:14px;color:var(--ink-3);"> 개</span>' if t_fruit else "—"
    fruit_sx = (
        f'<span style="color:var(--ink-3);">모델 추정치</span> · {summary["latest_date"]} · {week}주 환경'
        if t_fruit else ""
    )
    if t_fruit:
        fruit_sx += f'<br>학습 검증 R² {t_fruit["r2"]:.2f}'
        if t_fruit.get("actual") is not None:
            fruit_sx += f' · 동일 조사일 실측 {t_fruit["actual"]:.0f}개'
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
            실행 시 재학습하지 않으며, R²는 참조 데이터로 <b>사전 학습·검증</b>할 때의 지표입니다.
            수확수·착과수 숫자는 <b>다음 조사 예측이 아닌 모델 추정치</b>이고,
            생육 지연은 <b>모델이 추정한 초장</b>을 표준 곡선과 비교한 값입니다.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )



def render_forecast_tab(
    *,
    dims_ready: bool,
    df,
    week_dfs: dict,
    selected_week: int,
    growth_features: list[str],
    fruit_total: int,
    delay_days: int = 0,
):
    """예측 탭 본문."""
    if not dims_ready or df is None:
        st.info("데이터 탭에서 「분석 결과 보기」를 실행하면 전망이 표시됩니다.")
        return

    st.markdown(
        '<div class="data-head"><h1>앞으로 전망</h1>'
        '<p>지금 추세로 갈 때의 예상입니다. 컴퓨터가 추정한 <b>참고용</b> 값이에요.</p></div>',
        unsafe_allow_html=True,
    )
    render_model_forecast_section(
        df,
        week_dfs,
        selected_week,
        growth_features,
        fruit_total,
    )

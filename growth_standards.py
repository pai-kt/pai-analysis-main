"""data/생육 참조 데이터 기반 생육·수확 표준 곡선."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

GROWTH_REF_DIR = Path(__file__).resolve().parent / "data" / "생육"
GROWTH_REF_CACHE = Path(__file__).resolve().parent / "data" / ".growth_ref_trajectories.parquet"

STANDARD_METRICS = [
    "착과수", "초장", "엽수", "수확수",
    "생장길이", "엽장", "엽폭", "줄기굵기", "화방높이",
]

SUM_METRICS = {"착과수", "수확수"}
MEAN_METRICS = {"초장", "생장길이", "엽수", "엽장", "엽폭", "줄기굵기", "화방높이"}


def _clean_series(s: pd.Series) -> pd.Series:
    out = pd.to_numeric(s, errors="coerce")
    return out.where(out >= 0)


def _pick_date_col(columns) -> str | None:
    for name in ("조사일자", "조사일", "조사 일자", "날짜"):
        if name in columns:
            return name
    return None


def _aggregate_farm_daily(raw: pd.DataFrame) -> pd.DataFrame:
    """농가 파일 1개 → 조사일자별 집계."""
    date_col = _pick_date_col(raw.columns)
    if date_col is None:
        return pd.DataFrame()

    frame = raw.copy()
    frame["조사일자"] = pd.to_datetime(frame[date_col], errors="coerce")
    frame = frame.dropna(subset=["조사일자"])
    if frame.empty:
        return pd.DataFrame()

    sum_map = {
        "수확수": next((c for c in ("수확수", "화방별수확수") if c in frame.columns), None),
        "착과수": next((c for c in ("착과수", "화방별착과수") if c in frame.columns), None),
    }
    for std, src in sum_map.items():
        if src:
            frame[std] = _clean_series(frame[src])

    for col in MEAN_METRICS:
        if col in frame.columns:
            frame[col] = _clean_series(frame[col])

    agg: dict[str, str] = {}
    for c in SUM_METRICS:
        if c in frame.columns:
            agg[c] = "sum"
    for c in MEAN_METRICS:
        if c in frame.columns and c not in agg:
            agg[c] = "mean"
    if not agg:
        return pd.DataFrame()

    frame["_d"] = frame["조사일자"].dt.normalize()
    out = frame.groupby("_d", as_index=False).agg(agg)
    return out.rename(columns={"_d": "조사일자"}).sort_values("조사일자")


def _day_of_year(ts: pd.Timestamp) -> int:
    return int(ts.timetuple().tm_yday)


def _circular_day_diff(a: int, b: int) -> int:
    d = abs(a - b)
    return min(d, 365 - d)


def _calendar_weight(ref_start: pd.Timestamp, upload_start: pd.Timestamp, sigma_days: float = 45.0) -> float:
    diff = _circular_day_diff(_day_of_year(ref_start), _day_of_year(upload_start))
    return float(np.exp(-0.5 * (diff / sigma_days) ** 2))


def _weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not mask.any():
        return np.nan
    v = values[mask]
    w = weights[mask]
    order = np.argsort(v)
    v, w = v[order], w[order]
    cw = np.cumsum(w) / w.sum()
    return float(np.interp(q, cw, v))


def _reference_cache_stale() -> bool:
    if not GROWTH_REF_CACHE.exists():
        return True
    cache_mtime = GROWTH_REF_CACHE.stat().st_mtime
    if not GROWTH_REF_DIR.exists():
        return False
    for path in GROWTH_REF_DIR.glob("*.xlsx"):
        if path.name.startswith("~$"):
            continue
        if path.stat().st_mtime > cache_mtime:
            return True
    return False


def _build_reference_trajectories() -> tuple[pd.DataFrame, int]:
    """모든 참조 농가의 (rel_week, metric, value, farm_start) 레코드."""
    rows: list[dict] = []
    n_files = 0
    if not GROWTH_REF_DIR.exists():
        return pd.DataFrame(), 0

    usecols = {
        "조사일자", "조사일", "수확수", "화방별수확수", "착과수", "화방별착과수",
        "초장", "생장길이", "엽수", "엽장", "엽폭", "줄기굵기", "화방높이",
    }

    for path in sorted(GROWTH_REF_DIR.glob("*.xlsx")):
        if path.name.startswith("~$"):
            continue
        try:
            header = pd.read_excel(path, engine="openpyxl", nrows=0)
            cols = [c for c in header.columns if c in usecols]
            if not cols:
                continue
            raw = pd.read_excel(path, engine="openpyxl", usecols=cols)
        except Exception:
            continue
        daily = _aggregate_farm_daily(raw)
        if daily.empty:
            continue
        farm_start = daily["조사일자"].min()
        n_files += 1
        for _, row in daily.iterrows():
            rel_day = int((row["조사일자"] - farm_start).days)
            if rel_day < 0:
                continue
            rel_week = (rel_day // 7) * 7
            for metric in STANDARD_METRICS:
                if metric not in daily.columns:
                    continue
                val = row.get(metric)
                if val is None or (isinstance(val, float) and np.isnan(val)):
                    continue
                rows.append({
                    "rel_week": rel_week,
                    "metric": metric,
                    "value": float(val),
                    "farm_start": farm_start,
                    "farm_id": path.stem,
                })

    ref = pd.DataFrame(rows)
    if not ref.empty:
        try:
            ref.to_parquet(GROWTH_REF_CACHE, index=False)
        except Exception:
            pass
    return ref, n_files


@lru_cache(maxsize=1)
def _load_reference_trajectories() -> tuple[pd.DataFrame, int]:
    if not _reference_cache_stale():
        try:
            ref = pd.read_parquet(GROWTH_REF_CACHE)
            n_files = ref["farm_id"].nunique() if not ref.empty else 0
            if "farm_start" in ref.columns:
                ref["farm_start"] = pd.to_datetime(ref["farm_start"])
            return ref, int(n_files)
        except Exception:
            pass
    return _build_reference_trajectories()


def build_growth_standard_curves(
    upload_start: pd.Timestamp,
    max_rel_day: int | None = None,
    sigma_days: float = 45.0,
) -> tuple[dict[str, pd.DataFrame], int]:
    """
    업로드 시작일과 유사한 정식 시기의 참조 농가를 가중해 표준 곡선(p25/p50/p75) 생성.
    반환 곡선의 조사일자 = upload_start + rel_week.
    """
    ref, n_files = _load_reference_trajectories()
    if ref.empty or pd.isna(upload_start):
        return {}, n_files

    upload_start = pd.Timestamp(upload_start).normalize()
    ref = ref.copy()
    ref["weight"] = ref["farm_start"].apply(lambda d: _calendar_weight(d, upload_start, sigma_days))

    if max_rel_day is None:
        max_rel_day = int(ref["rel_week"].max()) if not ref.empty else 0

    curves: dict[str, pd.DataFrame] = {}
    for metric in STANDARD_METRICS:
        sub = ref[ref["metric"] == metric]
        if sub.empty:
            continue
        points = []
        for rel_week in sorted(sub["rel_week"].unique()):
            if rel_week > max_rel_day + 7:
                continue
            bucket = sub[sub["rel_week"] == rel_week]
            if bucket.empty:
                continue
            vals = bucket["value"].to_numpy(dtype=float)
            wts = bucket["weight"].to_numpy(dtype=float)
            if wts.sum() <= 0:
                continue
            p25 = _weighted_quantile(vals, wts, 0.25)
            p50 = _weighted_quantile(vals, wts, 0.50)
            p75 = _weighted_quantile(vals, wts, 0.75)
            if not np.isfinite(p50):
                continue
            points.append({
                "조사일자": upload_start + pd.Timedelta(days=int(rel_week)),
                "rel_week": int(rel_week),
                "p25": p25,
                "p50": p50,
                "p75": p75,
            })
        if points:
            curves[metric] = pd.DataFrame(points).sort_values("조사일자")

    return curves, n_files


def summarize_growth_vs_standard(chart_df: pd.DataFrame) -> dict:
    """최근 조사 기준 참조 표준 대비 생육·수확 요약 (현황 카드용)."""
    fallback = {
        "pill_label": "확인 필요",
        "pill_warn": False,
        "headline": "생육·수확 데이터를 확인해 주세요.",
        "desc": "아래 「생육·수확이 어떻게 커왔나」에서 조사별 추이를 확인할 수 있습니다.",
        "stat_value": "—",
        "stat_note": "표준 대비",
        "delay_days": 0,
    }
    if chart_df is None or chart_df.empty or "조사일자" not in chart_df.columns:
        return fallback

    plot = chart_df.copy()
    plot["조사일자"] = pd.to_datetime(plot["조사일자"], errors="coerce")
    plot = plot.dropna(subset=["조사일자"]).sort_values("조사일자")
    if plot.empty:
        return fallback

    upload_start = plot["조사일자"].min().normalize()
    latest_date = plot["조사일자"].max().normalize()
    rel_week = ((latest_date - upload_start).days // 7) * 7
    max_rel = int((latest_date - upload_start).days) + 7
    curves, n_ref = build_growth_standard_curves(upload_start, max_rel_day=max_rel)

    checks = [
        ("초장", "초장"),
        ("착과수", "착과"),
        ("수확수", "수확"),
    ]
    low_items: list[str] = []
    high_items: list[str] = []
    delay_days = 0

    for metric, short in checks:
        if metric not in plot.columns:
            continue
        series = pd.to_numeric(plot[metric], errors="coerce").dropna()
        if series.empty:
            continue
        actual = float(series.iloc[-1])
        std = curves.get(metric)
        if std is None or std.empty:
            continue
        row = std.iloc[(std["rel_week"] - rel_week).abs().argsort()[:1]].iloc[0]
        p25, p50, p75 = float(row["p25"]), float(row["p50"]), float(row["p75"])
        if actual < p25:
            low_items.append(short)
            if metric == "초장" and p50 > actual:
                delay_days = max(delay_days, int(round((p50 - actual) / max(p50 * 0.015, 1))))
        elif actual > p75:
            high_items.append(short)

    delay_days = min(max(delay_days, 0), 45)

    if n_ref == 0 or not curves:
        return {
            **fallback,
            "headline": "업로드 데이터 기준으로 생육·수확 추이를 확인할 수 있습니다.",
            "desc": "참조 표준 데이터가 준비되면 그래프에 회색 밴드로 함께 표시됩니다.",
        }

    if not low_items and not high_items:
        return {
            "pill_label": "순조",
            "pill_warn": False,
            "headline": "초장·착과·수확이 <b style=\"color:var(--accent)\">참조 농가 표준 범위</b> 안에 있습니다.",
            "desc": "아래 그래프에서 실선이 회색 밴드(표준) 안에 있는지 함께 확인해 보세요.",
            "stat_value": "양호",
            "stat_note": "표준 대비",
            "delay_days": 0,
        }

    if low_items and not high_items:
        items = "·".join(low_items)
        headline = (
            f"<b style=\"color:var(--accent)\">{items}</b>이(가) 참조 농가보다 "
            f"{'다소 ' if delay_days < 7 else ''}느립니다."
        )
        pill = "주의" if delay_days >= 3 else "점검"
        stat = f"{items} 낮음"
    elif high_items and not low_items:
        items = "·".join(high_items)
        headline = f"<b style=\"color:var(--accent)\">{items}</b>이(가) 참조 농가보다 빠르게 늘고 있습니다."
        pill = "순조"
        stat = f"{items} 높음"
    else:
        headline = (
            f"착과·수확·초장 중 <b style=\"color:var(--accent)\">표준과 다른 항목</b>이 있습니다. "
            "그래프에서 항목별로 확인해 보세요."
        )
        pill = "점검"
        stat = "혼재"

    return {
        "pill_label": pill,
        "pill_warn": pill != "순조",
        "headline": headline,
        "desc": "아래 「생육·수확이 어떻게 커왔나」에서 <b>실선(내 농가)</b>과 <b>회색 밴드(참조 표준)</b>를 비교하세요.",
        "stat_value": stat,
        "stat_note": "표준 대비",
        "delay_days": delay_days,
    }

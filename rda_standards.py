"""농진청 토마토 최적환경·생육 표준 (data/*.xlsx)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"

RDA_STAGES_SOLAR = [
    "생육초기",
    "생육중기(9~10월)",
    "생육중기(11~12월)",
    "생육중기(1~2월)",
    "생육중기(3~6월)",
    "생육말기(7~8월)",
]

RDA_STAGES_GROWTH = [
    "생육초기",
    "생육중기(9~10월)",
    "생육중기(11~12월)",
    "생육중기(1~2월)",
    "생육중기(3~6월)",
    "생육말기(7~8월, 상대 주차 < 10)",
]

RDA_STAGE_COLORS = {
    "생육초기": "#59A14F",
    "생육중기(9~10월)": "#4E79A7",
    "생육중기(11~12월)": "#76B7B2",
    "생육중기(1~2월)": "#B07AA1",
    "생육중기(3~6월)": "#E8A33D",
    "생육말기(7~8월)": "#E15759",
    "생육말기(7~8월, 상대 주차 < 10)": "#E15759",
}

SOLAR_DISPLAY_COLS = [
    ("누적일사량(범위)", "누적일사량(J/㎠/day)"),
    ("외기기온(범위)", "외기기온(℃)"),
    ("생산량(㎏/3.3㎡)", "생산량(㎏/3.3㎡)"),
    ("일일 평균온도(℃)", "일일 평균온도(℃)"),
    ("주간 평균온도(℃)", "주간 평균온도(℃)"),
    ("야간 평균온도(℃)", "야간 평균온도(℃)"),
    ("새벽온도(℃)", "새벽온도(℃)"),
    ("주간 평균습도(%)", "주간 평균습도(%)"),
    ("잔존 CO₂(ppm)", "잔존CO₂(ppm)"),
    ("급액 EC(dS/m)", "급액 EC(dS/m)"),
    ("급액 pH", "급액 pH"),
    ("1회 급액량(㏄/회)", "1회 급액량(㏄/회)"),
    ("1일 공급량(㏄/day)", "1일 공급량(㏄/day)"),
]

GROWTH_DISPLAY_COLS = [
    ("누적일사량(범위)", "누적일사량"),
    ("외기기온(범위)", "외기기온"),
    ("생산량(㎏/3.3㎡)", "생산량"),
    ("생장길이(㎝)", "생장길이"),
    ("줄기굵기(㎜)", "줄기굵기"),
    ("화방높이(㎝)", "화방높이"),
    ("일일 평균온도(℃)", "일일 평균온도"),
    ("주간 평균온도(℃)", "주간 평균온도"),
    ("야간 평균온도(℃)", "야간 평균온도"),
    ("새벽온도(℃)", "새벽 온도"),
    ("주간 평균습도(%)", "주간 평균습도"),
    ("잔존 CO₂(ppm)", "잔존CO₂"),
    ("급액횟수(회)", "급액횟수"),
    ("급액 EC(dS/m)", "급액 EC"),
    ("급액 pH", "급액 pH"),
    ("1회 급액량(㏄/회)", "1회 급액량"),
    ("1일 공급량(㏄/day)", "1일 급액량"),
]


def parse_range(text) -> tuple[float | None, float | None]:
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return None, None
    s = str(text).strip().replace(" ", "").replace("nan", "")
    if "~" not in s:
        return None, None
    lo, hi = s.split("~", 1)
    try:
        return float(lo), float(hi)
    except ValueError:
        return None, None


def value_in_range(value: float, range_text: str) -> bool:
    lo, hi = parse_range(range_text)
    if lo is None or hi is None:
        return False
    return lo <= value <= hi


def range_distance(value: float, range_text: str) -> float:
    """범위 밖이면 가장 가까운 경계까지 거리, 범위 안이면 중심과의 상대 거리."""
    lo, hi = parse_range(range_text)
    if lo is None or hi is None:
        return float("inf")
    width = max(hi - lo, 1e-6)
    if value < lo:
        return (lo - value) / width
    if value > hi:
        return (value - hi) / width
    return abs(value - (lo + hi) / 2) / width * 0.05


def find_best_match_index(
    df: pd.DataFrame,
    solar: float | None,
    outdoor: float | None,
) -> int | None:
    if df.empty:
        return None
    if solar is None and outdoor is None:
        return None
    best_pos, best_score = 0, float("inf")
    for pos, (_, row) in enumerate(df.iterrows()):
        score = 0.0
        if solar is not None:
            score += range_distance(solar, row.get("누적일사량(범위)"))
        if outdoor is not None:
            score += range_distance(outdoor, row.get("외기기온(범위)"))
        if score < best_score:
            best_score, best_pos = score, pos
    return best_pos


def find_match_group_indices(df: pd.DataFrame, anchor_pos: int) -> list[int]:
    """동일한 누적일사량·외기기온 범위를 가진 행 인덱스 목록."""
    if df.empty or anchor_pos < 0 or anchor_pos >= len(df):
        return []
    anchor = df.iloc[anchor_pos]
    solar_key = str(anchor.get("누적일사량(범위)", ""))
    outdoor_key = str(anchor.get("외기기온(범위)", ""))
    return [
        pos
        for pos, (_, row) in enumerate(df.iterrows())
        if str(row.get("누적일사량(범위)", "")) == solar_key
        and str(row.get("외기기온(범위)", "")) == outdoor_key
    ]


def _numeric_values_from_cell(value) -> list[float]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    lo, hi = parse_range(value)
    if lo is not None and hi is not None:
        return [lo, hi]
    try:
        return [float(str(value).replace(",", ""))]
    except ValueError:
        return []


def _format_agg_number(n: float) -> str:
    if abs(n - round(n)) < 0.05:
        return str(int(round(n)))
    return f"{n:.1f}".rstrip("0").rstrip(".")


def aggregate_rda_recommendation_rows(df: pd.DataFrame, indices: list[int]) -> pd.Series:
    """동일 입력 구간 행들의 권장값을 열별 최소~최댓값으로 통합."""
    if not indices:
        return pd.Series(dtype=object)
    subset = df.iloc[indices]
    merged = {}
    for col in subset.columns:
        nums: list[float] = []
        for val in subset[col]:
            nums.extend(_numeric_values_from_cell(val))
        if nums:
            lo, hi = min(nums), max(nums)
            if lo == hi:
                merged[col] = _format_agg_number(lo)
            else:
                merged[col] = f"{_format_agg_number(lo)}~{_format_agg_number(hi)}"
        else:
            first = subset[col].dropna()
            merged[col] = first.iloc[0] if not first.empty else "—"
    return pd.Series(merged)


def find_best_match_group(
    df: pd.DataFrame,
    solar: float | None,
    outdoor: float | None,
) -> tuple[list[int], pd.Series | None]:
    best = find_best_match_index(df, solar, outdoor)
    if best is None:
        return [], None
    indices = find_match_group_indices(df, best)
    return indices, aggregate_rda_recommendation_rows(df, indices)


def infer_stage_from_month(month: int) -> str:
    if month in (9, 10):
        return "생육중기(9~10월)"
    if month in (11, 12):
        return "생육중기(11~12월)"
    if month in (1, 2):
        return "생육중기(1~2월)"
    if month in (3, 4, 5, 6):
        return "생육중기(3~6월)"
    if month in (7, 8):
        return "생육말기(7~8월)"
    return "생육중기(3~6월)"


def _resolve_sheet(stage: str, sheet_names: list[str]) -> str:
    if stage in sheet_names:
        return stage
    if stage == "생육말기(7~8월)":
        for name in sheet_names:
            if name.startswith("생육말기(7~8월"):
                return name
    return sheet_names[0]


@lru_cache(maxsize=4)
def _load_workbook(kind: str, facility: str) -> dict[str, pd.DataFrame]:
    fname = {
        ("solar", "비닐"): "solar_level_vinyl_standard.xlsx",
        ("solar", "유리"): "solar_level_glass_standard.xlsx",
        ("growth", "비닐"): "growth_stage_vinyl_standard.xlsx",
        ("growth", "유리"): "growth_stage_glass_standard.xlsx",
    }[(kind, facility)]
    path = DATA_DIR / fname
    if not path.exists():
        return {}
    book: dict[str, pd.DataFrame] = {}
    xl = pd.ExcelFile(path)
    for sheet in xl.sheet_names:
        book[sheet] = pd.read_excel(path, sheet_name=sheet)
    return book


def load_solar_standard(facility: str, stage: str) -> pd.DataFrame:
    book = _load_workbook("solar", facility)
    if not book:
        return pd.DataFrame()
    sheet = _resolve_sheet(stage, list(book.keys()))
    return book[sheet].copy()


def load_growth_standard(facility: str, stage: str) -> pd.DataFrame:
    book = _load_workbook("growth", facility)
    if not book:
        return pd.DataFrame()
    sheet = _resolve_stage_growth(stage, list(book.keys()))
    return book[sheet].copy()


def _resolve_stage_growth(stage: str, sheet_names: list[str]) -> str:
    if stage in sheet_names:
        return stage
    if stage == "생육말기(7~8월)":
        for name in sheet_names:
            if name.startswith("생육말기"):
                return name
    return _resolve_sheet(stage, sheet_names)


def filter_by_inputs(df: pd.DataFrame, solar: float | None, outdoor: float | None) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if solar is not None:
        out = out[out["누적일사량(범위)"].apply(lambda r: value_in_range(solar, r))]
    if outdoor is not None:
        out = out[out["외기기온(범위)"].apply(lambda r: value_in_range(outdoor, r))]
    if "생산량(㎏/3.3㎡)" in out.columns:
        out = out.sort_values("생산량(㎏/3.3㎡)", ascending=False, na_position="last")
    return out.reset_index(drop=True)


def format_display_table(df: pd.DataFrame, columns: list[tuple[str, str]]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[label for _, label in columns])
    view = pd.DataFrame()
    for src, label in columns:
        if src in df.columns:
            view[label] = df[src]
    return view


def estimate_cumulative_solar(sensor_df, date_col: str, solar_col: str, days: int = 7) -> float | None:
    """최근 N일 일별 외부누적일사량 최댓값 중 최댓값 (농진청 탭 조회용)."""
    if sensor_df is None or date_col not in sensor_df.columns or solar_col not in sensor_df.columns:
        return None
    tmp = sensor_df[[date_col, solar_col]].copy()
    tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
    tmp[solar_col] = pd.to_numeric(tmp[solar_col], errors="coerce")
    tmp = tmp.dropna()
    if tmp.empty:
        return None
    tmp["d"] = tmp[date_col].dt.date
    daily_max = tmp.groupby("d")[solar_col].max()
    if daily_max.empty:
        return None
    return float(daily_max.tail(days).max())


def estimate_outdoor_temp(sensor_df, date_col: str, temp_col: str, days: int = 7) -> float | None:
    """온실 내부 온도로 외기기온 대용 추정 (외기 센서 없을 때)."""
    if sensor_df is None or date_col not in sensor_df.columns or temp_col not in sensor_df.columns:
        return None
    tmp = sensor_df[[date_col, temp_col]].copy()
    tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
    tmp[temp_col] = pd.to_numeric(tmp[temp_col], errors="coerce")
    tmp = tmp.dropna().sort_values(date_col)
    if tmp.empty:
        return None
    return float(tmp[temp_col].tail(days * 24 * 6).mean())  # ~10min intervals rough


def build_rda_recent_actuals(
    sensor_df,
    date_col: str,
    temp_col: str,
    solar_col: str,
    days: int = 7,
    solar_override: float | None = None,
) -> dict[str, float]:
    """농진청 탭 비교표용 최근 실측 — 센서 최근 N일 + 조회 입력값 기준."""
    if sensor_df is None or date_col not in sensor_df.columns:
        return {}
    tmp = sensor_df.copy()
    tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
    tmp = tmp.dropna(subset=[date_col])
    if tmp.empty:
        return {}
    tmp["date"] = tmp[date_col].dt.date
    tmp["hour"] = tmp[date_col].dt.hour
    latest_date = tmp["date"].max()
    start = pd.Timestamp(latest_date) - pd.Timedelta(days=days - 1)
    subset = tmp[tmp[date_col] >= start].copy()

    actuals: dict[str, float] = {}
    if solar_override is not None:
        actuals["일사량"] = float(solar_override)
    elif solar_col and solar_col in sensor_df.columns:
        est = estimate_cumulative_solar(sensor_df, date_col, solar_col, days)
        if est is not None:
            actuals["일사량"] = est

    if temp_col and temp_col in subset.columns:
        subset[temp_col] = pd.to_numeric(subset[temp_col], errors="coerce")
        day = subset[(subset["hour"] >= 8) & (subset["hour"] <= 18)]
        night = subset[(subset["hour"] >= 19) | (subset["hour"] <= 7)]
        if not day[temp_col].dropna().empty:
            actuals["주간온도"] = float(day[temp_col].mean())
        if not night[temp_col].dropna().empty:
            actuals["야간온도"] = float(night[temp_col].mean())
    return actuals

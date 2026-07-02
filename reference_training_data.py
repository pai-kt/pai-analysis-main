"""data/생육 · data/환경 · data/일사량 참조 데이터 → RandomForest 학습용 테이블."""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

DATA_ROOT = Path(__file__).resolve().parent / "data"
ENV_DIR = DATA_ROOT / "환경"
GROW_DIR = DATA_ROOT / "생육"
SOLAR_PATH = DATA_ROOT / "일사량" / "sol2022.xlsx"
CACHE_DIR = DATA_ROOT / ".reference_training_cache"
CACHE_ALL_WEEKS = CACHE_DIR / "all_weeks.parquet"

REF_TEMP_COL = "온도_내부"
REF_HUM_COL = "상대습도_내부"
REF_CO2_COL = "잔존CO2"
REF_SOLAR_COL = "누적일사량_외부"
REF_HARVEST_COL = "화방별수확수"
REF_FRUIT_COL = "화방별착과수"

DEFAULT_GROWTH_FEATURES = [
    "초장", "생장길이", "엽수", "엽장", "엽폭", "줄기굵기", "화방높이",
]
META_COLS = ["_source", "_farm_key", "_region", "_week"]

SUM_YIELD_COLS = {"수확수", "착과수"}
MEAN_GROWTH_COLS = set(DEFAULT_GROWTH_FEATURES)


def _norm_name(path: Path) -> str:
    return unicodedata.normalize("NFC", path.name)


def _farm_key(path: Path) -> str | None:
    m = re.search(r"_(?:기상환경|생육기본)_(.+)\.xlsx$", _norm_name(path))
    return m.group(1) if m else None


def _region_key(path: Path) -> str | None:
    m = re.search(r"22년_완숙토마토_(.+?)_(?:기상환경|생육기본)_", _norm_name(path))
    return m.group(1) if m else None


def _list_paired_farms() -> list[tuple[str, Path, Path, str | None]]:
    env_map: dict[str, Path] = {}
    grow_map: dict[str, Path] = {}
    region_map: dict[str, str | None] = {}

    for path in ENV_DIR.glob("*.xlsx"):
        if path.name.startswith("~$"):
            continue
        key = _farm_key(path)
        if key:
            env_map[key] = path
            region_map[key] = _region_key(path)

    for path in GROW_DIR.glob("*.xlsx"):
        if path.name.startswith("~$"):
            continue
        key = _farm_key(path)
        if key:
            grow_map[key] = path

    return [
        (key, env_map[key], grow_map[key], region_map.get(key))
        for key in sorted(set(env_map) & set(grow_map))
    ]


def _cache_stale() -> bool:
    if not CACHE_ALL_WEEKS.exists():
        return True
    cache_mtime = CACHE_ALL_WEEKS.stat().st_mtime
    paths = [SOLAR_PATH, *ENV_DIR.glob("*.xlsx"), *GROW_DIR.glob("*.xlsx")]
    for path in paths:
        if path.name.startswith("~$"):
            continue
        if path.exists() and path.stat().st_mtime > cache_mtime:
            return True
    return False


@lru_cache(maxsize=1)
def _load_solar_daily() -> pd.DataFrame:
    if not SOLAR_PATH.exists():
        return pd.DataFrame(columns=["id", "date", "sol"])
    sol = pd.read_excel(SOLAR_PATH, engine="openpyxl")
    sol["date"] = pd.to_datetime(sol["date"], errors="coerce").dt.normalize()
    sol["sol"] = pd.to_numeric(sol["sol"], errors="coerce")
    return sol.dropna(subset=["date", "sol"])


def _env_daily_solar(env_df: pd.DataFrame) -> pd.Series:
    daily = env_df.copy()
    daily["date"] = pd.to_datetime(daily["date"], errors="coerce").dt.normalize()
    daily[REF_SOLAR_COL] = pd.to_numeric(daily[REF_SOLAR_COL], errors="coerce")
    return daily.groupby("date")[REF_SOLAR_COL].max()


def _match_solar_id(env_df: pd.DataFrame, solar_df: pd.DataFrame) -> int | None:
    env_daily = _env_daily_solar(env_df)
    if env_daily.empty or solar_df.empty:
        return None

    best_id = None
    best_corr = -1.0
    for sid in solar_df["id"].dropna().unique():
        sub = solar_df[solar_df["id"] == sid].set_index("date")["sol"]
        merged = pd.concat([env_daily, sub], axis=1, join="inner").dropna()
        if len(merged) < 14:
            continue
        corr = merged.iloc[:, 0].corr(merged.iloc[:, 1])
        if corr is not None and corr > best_corr:
            best_corr = float(corr)
            best_id = int(sid)
    return best_id if best_corr >= 0.5 else None


def _inject_solar_from_file(env_df: pd.DataFrame, solar_df: pd.DataFrame, solar_id: int) -> pd.DataFrame:
    out = env_df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.normalize()
    daily = (
        solar_df[solar_df["id"] == solar_id]
        .drop_duplicates("date")
        .set_index("date")["sol"]
    )
    if daily.empty:
        return out
    mapped = out["date"].map(daily)
    out[REF_SOLAR_COL] = mapped.fillna(out[REF_SOLAR_COL])
    return out


def _prepare_reference_env(env_path: Path, solar_df: pd.DataFrame) -> pd.DataFrame:
    env_df = pd.read_excel(env_path, engine="openpyxl")
    env_df["date"] = pd.to_datetime(env_df["date"], errors="coerce")
    env_df["time"] = env_df["time"].astype(str)
    env_df["datetime"] = pd.to_datetime(
        env_df["date"].dt.strftime("%Y-%m-%d") + " " + env_df["time"].str[:8],
        errors="coerce",
    )
    env_df = env_df.dropna(subset=["datetime"]).copy()
    env_df["hour"] = env_df["datetime"].dt.hour

    for col in [REF_TEMP_COL, REF_HUM_COL, REF_CO2_COL, REF_SOLAR_COL]:
        if col in env_df.columns:
            env_df[col] = pd.to_numeric(env_df[col], errors="coerce")

    solar_id = _match_solar_id(env_df, solar_df)
    if solar_id is not None:
        env_df = _inject_solar_from_file(env_df, solar_df, solar_id)
    return env_df


def _aggregate_reference_yield(raw: pd.DataFrame, growth_features: list[str]) -> pd.DataFrame:
    frame = raw.copy()
    if "조사일자" not in frame.columns:
        return pd.DataFrame()

    frame["조사일자"] = pd.to_datetime(frame["조사일자"], errors="coerce")
    frame = frame.dropna(subset=["조사일자"])
    if frame.empty:
        return pd.DataFrame()

    if REF_HARVEST_COL in frame.columns:
        frame["수확수"] = pd.to_numeric(frame[REF_HARVEST_COL], errors="coerce")
    elif "수확수" in frame.columns:
        frame["수확수"] = pd.to_numeric(frame["수확수"], errors="coerce")

    if REF_FRUIT_COL in frame.columns:
        frame["착과수"] = pd.to_numeric(frame[REF_FRUIT_COL], errors="coerce")
    elif "착과수" in frame.columns:
        frame["착과수"] = pd.to_numeric(frame["착과수"], errors="coerce")

    agg: dict[str, str] = {}
    for col in SUM_YIELD_COLS:
        if col in frame.columns:
            agg[col] = "sum"
    for col in growth_features:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
            agg[col] = "mean"

    if not agg:
        return pd.DataFrame()

    return frame.groupby("조사일자", as_index=False).agg(agg).sort_values("조사일자")


def _build_all_reference_rows(growth_features: list[str]) -> pd.DataFrame:
    import app as core

    farms = _list_paired_farms()
    solar_df = _load_solar_daily()
    chunks: list[pd.DataFrame] = []

    for farm_key, env_path, grow_path, region in farms:
        try:
            env_df = _prepare_reference_env(env_path, solar_df)
            grow_df = _aggregate_reference_yield(
                pd.read_excel(grow_path, engine="openpyxl"),
                growth_features,
            )
            if grow_df.empty or env_df.empty:
                continue

            growth_cols = {gf: gf for gf in growth_features if gf in grow_df.columns}
            for week in range(1, 8):
                out = core.compute_rolling_summary(
                    env_df,
                    grow_df,
                    "datetime",
                    "조사일자",
                    REF_TEMP_COL,
                    REF_HUM_COL,
                    REF_CO2_COL,
                    REF_SOLAR_COL,
                    "수확수",
                    "착과수",
                    growth_cols,
                    week,
                )
                if out.empty:
                    continue
                out["_source"] = "reference"
                out["_farm_key"] = farm_key
                out["_region"] = region or ""
                out["_week"] = week
                chunks.append(out)
        except Exception:
            continue

    if not chunks:
        return pd.DataFrame()

    all_rows = pd.concat(chunks, ignore_index=True, sort=False)
    all_rows["조사일자"] = pd.to_datetime(all_rows["조사일자"], errors="coerce")
    return all_rows


@lru_cache(maxsize=8)
def _load_all_reference_rows(growth_key: tuple[str, ...]) -> pd.DataFrame:
    growth_features = list(growth_key)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if not _cache_stale():
        try:
            cached = pd.read_parquet(CACHE_ALL_WEEKS)
            if not cached.empty and "_week" in cached.columns:
                cached["조사일자"] = pd.to_datetime(cached["조사일자"], errors="coerce")
                return cached
        except Exception:
            pass

    all_rows = _build_all_reference_rows(growth_features)
    if not all_rows.empty:
        try:
            all_rows.to_parquet(CACHE_ALL_WEEKS, index=False)
        except Exception:
            pass
    return all_rows


def _slice_week_columns(df: pd.DataFrame, week: int, growth_features: list[str]) -> pd.DataFrame:
    """다주차 캐시에서 해당 주차 환경 컬럼만 남깁니다."""
    import app as core

    env_cols = [
        core.build_window_feature_name(week, suffix)
        for suffix in [
            "평균주간온도(08~18시)",
            "평균야간온도(19~07시)",
            "평균주간습도(08~18시)",
            "평균야간습도(19~07시)",
            "평균주간CO₂(08~18시)",
            "평균야간CO₂(19~07시)",
            "평균누적일사량(1일최대값기준)",
        ]
    ]
    base = ["조사일자", "수확수", "착과수", *growth_features, "_source", "_farm_key", "_region"]
    cols = [c for c in base if c in df.columns] + [c for c in env_cols if c in df.columns]
    return df[cols].copy()


def build_reference_week_df(week: int, growth_features: list[str] | None = None) -> pd.DataFrame:
    growth_features = growth_features or DEFAULT_GROWTH_FEATURES
    all_rows = _load_all_reference_rows(tuple(growth_features))
    if all_rows.empty:
        return pd.DataFrame()
    sub = all_rows[all_rows["_week"] == week].drop(columns=["_week"]).reset_index(drop=True)
    return _slice_week_columns(sub, week, growth_features)


def build_reference_week_dfs(growth_features: list[str] | None = None) -> dict[int, pd.DataFrame]:
    growth_features = growth_features or DEFAULT_GROWTH_FEATURES
    all_rows = _load_all_reference_rows(tuple(growth_features))
    out: dict[int, pd.DataFrame] = {}
    if all_rows.empty:
        return {wk: pd.DataFrame() for wk in range(1, 8)}
    for wk in range(1, 8):
        sub = all_rows[all_rows["_week"] == wk].drop(columns=["_week"]).reset_index(drop=True)
        out[wk] = _slice_week_columns(sub, wk, growth_features)
    return out


def _mark_upload(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["_source"] = "upload"
    out["_farm_key"] = "내 농가"
    out["_region"] = ""
    return out


def combine_training_data(
    upload_df: pd.DataFrame,
    upload_week_dfs: dict[int, pd.DataFrame],
    selected_week: int,
    growth_features: list[str] | None = None,
) -> tuple[pd.DataFrame, dict[int, pd.DataFrame], dict]:
    growth_features = growth_features or DEFAULT_GROWTH_FEATURES
    ref_week_dfs = build_reference_week_dfs(growth_features)

    upload_marked = _mark_upload(upload_df)
    ref_selected = ref_week_dfs.get(selected_week, pd.DataFrame())
    train_df = pd.concat([upload_marked, ref_selected], ignore_index=True, sort=False)
    train_df["조사일자"] = pd.to_datetime(train_df["조사일자"], errors="coerce")

    train_week_dfs: dict[int, pd.DataFrame] = {}
    for wk in range(1, 8):
        up = upload_week_dfs.get(wk, pd.DataFrame())
        ref = ref_week_dfs.get(wk, pd.DataFrame())
        parts = []
        if not up.empty:
            parts.append(_mark_upload(up))
        if not ref.empty:
            parts.append(ref)
        if parts:
            merged = pd.concat(parts, ignore_index=True, sort=False)
            merged["조사일자"] = pd.to_datetime(merged["조사일자"], errors="coerce")
            train_week_dfs[wk] = merged
        else:
            train_week_dfs[wk] = pd.DataFrame()

    info = {
        "upload_rows": int((train_df["_source"] == "upload").sum()) if "_source" in train_df.columns else len(upload_df),
        "ref_rows": int((train_df["_source"] == "reference").sum()) if "_source" in train_df.columns else 0,
        "ref_farms": int(ref_selected["_farm_key"].nunique()) if not ref_selected.empty and "_farm_key" in ref_selected.columns else 0,
        "total_rows": len(train_df),
    }
    return train_df, train_week_dfs, info


def training_feature_columns(df: pd.DataFrame, growth_features: list[str]) -> list[str]:
    exclude = ["조사일자", "수확수", "착과수", *growth_features, *META_COLS]
    return [col for col in df.columns if col not in exclude]


def _predict_latest_row(fitted: dict, latest: pd.Series) -> float:
    import app as core

    X_latest = latest[fitted["features"]].to_frame().T
    X_latest = X_latest.apply(pd.to_numeric, errors="coerce").fillna(fitted["fill"])
    return float(core.safe_predict(fitted["model"], X_latest, fitted["features"])[0])


def _fit_and_predict_latest(
    train_df: pd.DataFrame,
    growth_features: list[str],
    target_col: str,
    latest: pd.Series,
) -> dict | None:
    """학습 후 즉시 예측하고 모델 객체는 해제 (메모리 절약)."""
    from sklearn.model_selection import train_test_split
    import app as core

    features = training_feature_columns(train_df, growth_features)
    if target_col not in train_df.columns or not features:
        return None

    X = train_df[features].copy()
    fill = X.mean(numeric_only=True)
    X = X.fillna(fill)
    y = pd.to_numeric(train_df[target_col], errors="coerce")
    valid = y.notna()
    X = X.loc[valid].copy()
    y = y.loc[valid].copy()
    if len(X) < 8:
        return None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    model = core.make_model("RandomForest")
    model.fit(X_train, y_train)
    y_pred = core.safe_predict(model, X_test, features)
    metrics = core.compute_metrics(y_test, y_pred)
    pred = float(_predict_latest_row({"model": model, "features": features, "fill": fill}, latest))
    del model
    return {
        "pred": pred,
        "metrics": metrics,
        "n_train": len(X_train),
    }


def _model_delay_from_height(
    pred_height: float,
    upload_df: pd.DataFrame,
    latest_date: pd.Timestamp,
) -> int:
    from growth_standards import build_growth_standard_curves

    upload_start = pd.to_datetime(upload_df["조사일자"], errors="coerce").min()
    if pd.isna(upload_start) or pd.isna(latest_date):
        return 0
    upload_start = upload_start.normalize()
    latest_date = pd.to_datetime(latest_date).normalize()
    rel_week = ((latest_date - upload_start).days // 7) * 7
    curves, _ = build_growth_standard_curves(upload_start, max_rel_day=rel_week + 7)
    std = curves.get("초장")
    if std is None or std.empty:
        return 0
    row = std.iloc[(std["rel_week"] - rel_week).abs().argsort()[:1]].iloc[0]
    p50 = float(row["p50"])
    if pred_height >= p50:
        return 0
    return min(max(int(round((p50 - pred_height) / max(p50 * 0.015, 1))), 0), 45)


def build_model_forecast_summary(
    upload_df: pd.DataFrame,
    week_dfs: dict[int, pd.DataFrame],
    selected_week: int,
    growth_features: list[str] | None = None,
    fruit_total: int = 0,
) -> dict | None:
    """업로드 최신 조사 + 참조 학습 RandomForest → 예측 탭 카드용 요약."""
    growth_features = growth_features or DEFAULT_GROWTH_FEATURES
    frame = upload_df.copy()
    if frame.empty or "조사일자" not in frame.columns:
        return None

    frame["조사일자"] = pd.to_datetime(frame["조사일자"], errors="coerce")
    frame = frame.dropna(subset=["조사일자"]).sort_values("조사일자")
    if frame.empty:
        return None

    latest = frame.iloc[-1]
    latest_date = latest["조사일자"]

    train_df, _, info = combine_training_data(
        frame, week_dfs, selected_week, growth_features
    )
    if train_df.empty:
        return None

    targets: dict[str, dict] = {}
    for target in ("착과수", "수확수", "초장"):
        result = _fit_and_predict_latest(train_df, growth_features, target, latest)
        if result is None:
            continue
        pred = result["pred"]
        if target in ("수확수", "착과수"):
            pred = max(0.0, pred)
        actual_raw = latest.get(target)
        actual = float(actual_raw) if pd.notna(actual_raw) else None
        targets[target] = {
            "pred": pred,
            "actual": actual,
            "r2": float(result["metrics"]["R2"]),
            "mae": float(result["metrics"]["MAE"]),
            "n_train": result["n_train"],
        }

    if not targets:
        return None

    model_delay = 0
    if "초장" in targets:
        model_delay = _model_delay_from_height(
            targets["초장"]["pred"], frame, latest_date
        )

    projected_fruit = fruit_total
    if "착과수" in targets and targets["착과수"]["actual"] is not None:
        projected_fruit = int(
            max(0, fruit_total - targets["착과수"]["actual"] + targets["착과수"]["pred"])
        )

    harvest_note = "최근 환경 유지 시 다음 조사 기준"
    if "수확수" in targets:
        pred_h = targets["수확수"]["pred"]
        act_h = targets["수확수"]["actual"]
        if act_h is not None and pred_h > act_h * 1.05:
            harvest_note = "모델상 수확 증가 추세"
        elif act_h is not None and pred_h < act_h * 0.95:
            harvest_note = "모델상 수확 둔화 추세"

    return {
        "info": info,
        "selected_week": selected_week,
        "latest_date": latest_date.strftime("%Y-%m-%d"),
        "targets": targets,
        "model_delay_days": model_delay,
        "projected_fruit_total": projected_fruit,
        "harvest_note": harvest_note,
    }

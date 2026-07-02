"""참조 데이터로 학습한 모델을 models/에 저장·로드."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import KBinsDiscretizer

from reference_training_data import (
    DEFAULT_GROWTH_FEATURES,
    build_reference_week_df,
    training_feature_columns,
)

MODELS_DIR = Path(__file__).resolve().parent / "models"
MANIFEST_PATH = MODELS_DIR / "manifest.json"

MODEL_TYPES = ["RandomForest", "XGBoost", "LGBM", "GaussianNB"]
MODEL_SLUGS = {
    "RandomForest": "randomforest",
    "XGBoost": "xgboost",
    "LGBM": "lgbm",
    "GaussianNB": "gaussiannb",
}
FORECAST_TARGETS = ["착과수", "수확수", "초장"]


def _model_file(week: int, model_type: str, target: str) -> Path:
    slug = MODEL_SLUGS[model_type]
    return MODELS_DIR / f"week_{week:02d}" / f"{slug}_{target}.joblib"


def _meta_file(week: int, model_type: str, target: str) -> Path:
    slug = MODEL_SLUGS[model_type]
    return MODELS_DIR / f"week_{week:02d}" / f"{slug}_{target}.meta.json"


def _prepare_training_frame(
    week: int,
    growth_features: list[str],
) -> tuple[pd.DataFrame, list[str]] | None:
    df = build_reference_week_df(week, growth_features)
    if df.empty:
        return None
    features = training_feature_columns(df, growth_features)
    if not features:
        return None
    return df, features


def _fit_model(model_type: str, X_train, y_train):
    from ml_utils import make_model

    model = make_model(model_type)
    extra = None
    if model_type == "GaussianNB":
        n_unique = int(pd.Series(y_train).nunique())
        n_bins = max(3, min(15, n_unique))
        discretizer = KBinsDiscretizer(
            n_bins=n_bins, encode="ordinal", strategy="quantile"
        )
        y_bin = discretizer.fit_transform(
            np.asarray(y_train).reshape(-1, 1)
        ).ravel().astype(int)
        model.fit(X_train, y_bin)
        extra = {"discretizer": discretizer}
        return model, extra
    model.fit(X_train, y_train)
    return model, extra


def _predict_values(model_type: str, model, X, extra=None) -> np.ndarray:
    from ml_utils import safe_predict

    if model_type == "GaussianNB" and extra and "discretizer" in extra:
        discretizer: KBinsDiscretizer = extra["discretizer"]
        proba = model.predict_proba(X)
        edges = discretizer.bin_edges_[0]
        centers = (edges[:-1] + edges[1:]) / 2.0
        if proba.shape[1] != len(centers):
            # 클래스 수와 bin 수 불일치 시 가장 가까운 중심값 사용
            preds = model.predict(X).astype(int)
            preds = np.clip(preds, 0, len(centers) - 1)
            return centers[preds]
        return proba @ centers
    return safe_predict(model, X, list(X.columns))


def train_and_save_model(
    week: int,
    model_type: str,
    target: str,
    growth_features: list[str] | None = None,
) -> dict | None:
    """참조 데이터만으로 1개 모델 학습 후 models/ 저장."""
    growth_features = growth_features or DEFAULT_GROWTH_FEATURES
    prepared = _prepare_training_frame(week, growth_features)
    if prepared is None:
        return None
    df, features = prepared
    if target not in df.columns:
        return None

    X = df[features].copy()
    fill = X.mean(numeric_only=True)
    X = X.fillna(fill)
    y = pd.to_numeric(df[target], errors="coerce")
    valid = y.notna()
    X = X.loc[valid].copy()
    y = y.loc[valid].copy()
    if len(X) < 12:
        return None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    model, extra = _fit_model(model_type, X_train, y_train)
    y_pred = _predict_values(model_type, model, X_test, extra)

    from ml_utils import compute_metrics

    metrics = compute_metrics(y_test, y_pred)

    out_dir = MODELS_DIR / f"week_{week:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = {"model": model, "extra": extra}
    joblib.dump(payload, _model_file(week, model_type, target))

    import sklearn

    meta = {
        "model_type": model_type,
        "target": target,
        "week": week,
        "features": features,
        "fill": {k: float(v) if pd.notna(v) else None for k, v in fill.items()},
        "metrics": {k: float(v) for k, v in metrics.items()},
        "n_train": int(len(X_train)),
        "n_total": int(len(X)),
        "is_gaussian_nb": model_type == "GaussianNB",
        "sklearn_version": sklearn.__version__,
    }
    _meta_file(week, model_type, target).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return meta


def train_and_save_all_models(
    growth_features: list[str] | None = None,
    weeks: range | None = None,
) -> dict:
    """4종 모델 × 3타깃 × 7주차 일괄 학습."""
    growth_features = growth_features or DEFAULT_GROWTH_FEATURES
    weeks = weeks or range(1, 8)
    from reference_training_data import _list_paired_farms

    manifest: dict = {
        "models": [],
        "growth_features": growth_features,
        "ref_farms": len(_list_paired_farms()),
    }

    for week in weeks:
        for model_type in MODEL_TYPES:
            for target in FORECAST_TARGETS:
                try:
                    meta = train_and_save_model(week, model_type, target, growth_features)
                    if meta:
                        manifest["models"].append(
                            {
                                "week": week,
                                "model_type": model_type,
                                "target": target,
                                "r2": meta["metrics"]["R2"],
                                "n_train": meta["n_train"],
                            }
                        )
                        print(
                            f"OK week={week} {model_type} {target} "
                            f"R2={meta['metrics']['R2']:.3f} n={meta['n_train']}"
                        )
                    else:
                        print(f"SKIP week={week} {model_type} {target}")
                except Exception as exc:
                    print(f"FAIL week={week} {model_type} {target}: {exc}")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest


def load_model_bundle(
    week: int,
    model_type: str,
    target: str,
) -> dict | None:
    """저장된 모델 + 메타 로드."""
    model_path = _model_file(week, model_type, target)
    meta_path = _meta_file(week, model_type, target)
    if not model_path.exists() or not meta_path.exists():
        return None
    payload = joblib.load(model_path)
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    return {
        "model": payload["model"],
        "extra": payload.get("extra"),
        "meta": meta,
    }


def models_available() -> bool:
    return MANIFEST_PATH.exists() and any(MODELS_DIR.glob("week_*/*.joblib"))


def load_weekly_saved_metrics(model_type: str, target: str) -> list[dict]:
    """저장된 1~7주 모델 평가지표."""
    rows = []
    for week in range(1, 8):
        bundle = load_model_bundle(week, model_type, target)
        if not bundle:
            continue
        m = bundle["meta"]["metrics"]
        rows.append({
            "Week": week,
            "MSE": m["MSE"],
            "MAE": m["MAE"],
            "R2": m["R2"],
        })
    return rows


def build_feature_matrix(
    frame: pd.DataFrame | pd.Series | None,
    features: list[str],
    fill: pd.Series | dict,
) -> pd.DataFrame:
    """모델 meta features 순서로 행렬 구성 (없는 컬럼은 fill 값 사용)."""
    fill = pd.Series(fill).reindex(features).fillna(0.0)
    if frame is None:
        return pd.DataFrame([fill.to_dict()], columns=features)
    if isinstance(frame, pd.Series):
        frame = frame.to_frame().T
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return pd.DataFrame([fill.to_dict()], columns=features)

    data: dict[str, pd.Series] = {}
    for f in features:
        if f in frame.columns:
            data[f] = pd.to_numeric(frame[f], errors="coerce")
        else:
            data[f] = pd.Series(fill[f], index=frame.index)
    return pd.DataFrame(data, columns=features).fillna(fill)


def shap_background_matrix(
    upload_df: pd.DataFrame | None,
    features: list[str],
    fill: pd.Series | dict,
    min_rows: int = 10,
) -> pd.DataFrame:
    """SHAP 배경용 행렬 — 업로드 데이터 + fill 패딩."""
    X = build_feature_matrix(upload_df, features, fill)
    if len(X) >= min_rows:
        return X
    pad = pd.DataFrame([pd.Series(fill).reindex(features).fillna(0.0).to_dict()] * (min_rows - len(X)))
    return pd.concat([X, pad], ignore_index=True)


def predict_row(
    bundle: dict,
    row: pd.Series,
    model_type: str | None = None,
) -> float:
    model_type = model_type or bundle["meta"]["model_type"]
    features = bundle["meta"]["features"]
    fill = pd.Series(bundle["meta"]["fill"])
    X = build_feature_matrix(row, features, fill)
    pred = float(_predict_values(model_type, bundle["model"], X, bundle.get("extra"))[0])
    if bundle["meta"]["target"] in ("수확수", "착과수"):
        pred = max(0.0, pred)
    return pred


def predict_upload_latest(
    upload_df: pd.DataFrame,
    week: int,
    model_type: str,
    target: str,
) -> dict | None:
    """업로드 최신 조사 1행 예측."""
    bundle = load_model_bundle(week, model_type, target)
    if bundle is None:
        return None

    frame = upload_df.copy()
    frame["조사일자"] = pd.to_datetime(frame["조사일자"], errors="coerce")
    frame = frame.dropna(subset=["조사일자"]).sort_values("조사일자")
    if frame.empty:
        return None

    latest = frame.iloc[-1]
    pred = predict_row(bundle, latest, model_type)
    actual_raw = latest.get(target)
    actual = float(actual_raw) if pd.notna(actual_raw) else None
    return {
        "pred": pred,
        "actual": actual,
        "metrics": bundle["meta"]["metrics"],
        "n_train": bundle["meta"]["n_train"],
        "model_type": model_type,
        "target": target,
    }

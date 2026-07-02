"""모델 생성·예측·평가 (Streamlit 비의존)."""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.naive_bayes import GaussianNB
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor


def safe_predict(model, X_input, feature_names):
    if isinstance(X_input, pd.Series):
        X_input = pd.DataFrame([X_input])
    elif isinstance(X_input, np.ndarray):
        X_input = pd.DataFrame(X_input, columns=feature_names)
    elif not isinstance(X_input, pd.DataFrame):
        raise TypeError("X_input은 Series, ndarray, DataFrame 중 하나여야 합니다.")

    X_input = X_input.reindex(columns=feature_names)
    return model.predict(X_input)


def make_model(model_choice: str):
    if model_choice == "RandomForest":
        return RandomForestRegressor(random_state=42)
    if model_choice == "GradientBoosting":
        return GradientBoostingRegressor(random_state=42)
    if model_choice == "XGBoost":
        return XGBRegressor(random_state=42, objective="reg:squarederror")
    if model_choice == "LGBM":
        return LGBMRegressor(random_state=42)
    if model_choice == "GaussianNB":
        return GaussianNB()
    raise ValueError("지원하지 않는 모델")


def compute_metrics(y_true, y_pred):
    return {
        "MSE": mean_squared_error(y_true, y_pred),
        "MAE": mean_absolute_error(y_true, y_pred),
        "R2": r2_score(y_true, y_pred),
    }

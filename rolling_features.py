"""환경 롤링 요약 피처 (Streamlit 비의존)."""
from datetime import timedelta

import numpy as np
import pandas as pd


def build_window_feature_name(week, suffix):
    return f"{week}주{suffix}"


def compute_rolling_summary(
    sensor_df,
    yield_df,
    date_col_sensor,
    date_col_yield,
    temp_col,
    hum_col,
    co2_col,
    solar_col,
    harvest_count_col,
    harvest_weight_col,
    growth_cols,
    week,
):
    days = week * 7
    temp_day_col_name = build_window_feature_name(week, "평균주간온도(08~18시)")
    temp_night_col_name = build_window_feature_name(week, "평균야간온도(19~07시)")
    hum_day_col_name = build_window_feature_name(week, "평균주간습도(08~18시)")
    hum_night_col_name = build_window_feature_name(week, "평균야간습도(19~07시)")
    co2_day_col_name = build_window_feature_name(week, "평균주간CO₂(08~18시)")
    co2_night_col_name = build_window_feature_name(week, "평균야간CO₂(19~07시)")
    solar_col_name = build_window_feature_name(week, "평균누적일사량(1일최대값기준)")

    results = []
    sensor_dates = pd.to_datetime(sensor_df[date_col_sensor], errors="coerce")

    for _, row in yield_df.iterrows():
        date = pd.to_datetime(row[date_col_yield], errors="coerce")
        if pd.isna(date):
            continue
        start_date = date - timedelta(days=days)
        mask = (sensor_dates >= start_date) & (sensor_dates <= date)
        subset = sensor_df.loc[mask].copy()

        avg_solar = np.nan
        avg_co2_day = np.nan
        avg_co2_night = np.nan
        avg_temp_day = np.nan
        avg_temp_night = np.nan
        avg_hum_day = np.nan
        avg_hum_night = np.nan

        if not subset.empty:
            subset[solar_col] = pd.to_numeric(subset[solar_col], errors="coerce")
            daily_max_solar = (
                subset.groupby("date")[solar_col]
                .max()
                .reset_index()
            )
            if not daily_max_solar.empty:
                avg_solar = daily_max_solar[solar_col].mean()

            co2_daytime = subset[
                (subset["hour"] >= 8) &
                (subset["hour"] <= 18)
            ]
            if not co2_daytime.empty:
                co2_day_mean = co2_daytime.groupby("date")[co2_col].mean().reset_index()
                if not co2_day_mean.empty:
                    avg_co2_day = pd.to_numeric(
                        co2_day_mean[co2_col],
                        errors="coerce",
                    ).mean()

            co2_nighttime = subset[
                (subset["hour"] >= 19) |
                (subset["hour"] <= 7)
            ]
            if not co2_nighttime.empty:
                co2_night_mean = co2_nighttime.groupby("date")[co2_col].mean().reset_index()
                if not co2_night_mean.empty:
                    avg_co2_night = pd.to_numeric(
                        co2_night_mean[co2_col],
                        errors="coerce",
                    ).mean()

            temp_daytime = subset[
                (subset["hour"] >= 8) &
                (subset["hour"] <= 18)
            ]
            if not temp_daytime.empty and temp_col in temp_daytime.columns:
                avg_temp_day = pd.to_numeric(
                    temp_daytime[temp_col],
                    errors="coerce",
                ).mean()

            temp_nighttime = subset[
                (subset["hour"] >= 19) |
                (subset["hour"] <= 7)
            ]
            if not temp_nighttime.empty and temp_col in temp_nighttime.columns:
                avg_temp_night = pd.to_numeric(
                    temp_nighttime[temp_col],
                    errors="coerce",
                ).mean()

            hum_daytime = subset[(subset["hour"] >= 8) & (subset["hour"] <= 18)]
            if not hum_daytime.empty and hum_col in hum_daytime.columns:
                avg_hum_day = pd.to_numeric(hum_daytime[hum_col], errors="coerce").mean()

            hum_nighttime = subset[(subset["hour"] >= 19) | (subset["hour"] <= 7)]
            if not hum_nighttime.empty and hum_col in hum_nighttime.columns:
                avg_hum_night = pd.to_numeric(hum_nighttime[hum_col], errors="coerce").mean()

        result_row = {
            "조사일자": date,
            "수확수": row[harvest_count_col] if harvest_count_col in row else np.nan,
            "착과수": row[harvest_weight_col] if harvest_weight_col in row else np.nan,
            temp_day_col_name: avg_temp_day,
            temp_night_col_name: avg_temp_night,
            hum_day_col_name: avg_hum_day,
            hum_night_col_name: avg_hum_night,
            co2_day_col_name: avg_co2_day,
            co2_night_col_name: avg_co2_night,
            solar_col_name: avg_solar,
        }

        for gf, col in growth_cols.items():
            if col and col in row.index:
                result_row[gf] = row[col]
            else:
                result_row[gf] = np.nan

        results.append(result_row)

    out = pd.DataFrame(results)
    if out.empty or "조사일자" not in out.columns:
        base_cols = [
            "조사일자", "수확수", "착과수",
            temp_day_col_name, temp_night_col_name,
            hum_day_col_name, hum_night_col_name,
            co2_day_col_name, co2_night_col_name, solar_col_name,
        ]
        base_cols += [gf for gf in growth_cols]
        return pd.DataFrame(columns=base_cols)
    return out.sort_values("조사일자").reset_index(drop=True)

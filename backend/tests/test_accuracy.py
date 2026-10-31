import math

import pandas as pd

from app.analytics.matching import actuals_frame, forecasts_frame, match_actuals_to_forecasts, select_forecasts
from app.analytics.metrics import accuracy_metrics, matched_rows
from tests.conftest import utc


def _matched() -> pd.DataFrame:
    actuals = actuals_frame(
        [
            {"start_time": utc(2026, 1, 2, 0, 0), "generation_mw": 1000},
            {"start_time": utc(2026, 1, 2, 0, 30), "generation_mw": 1100},
        ]
    )
    forecasts = forecasts_frame(
        [
            {"start_time": utc(2026, 1, 2, 0, 0), "publish_time": utc(2026, 1, 1, 8, 30), "generation_mw": 1200},
        ]
    )
    selected = select_forecasts(
        forecasts,
        mode="decision_time",
        cutoff_hour=9,
        cutoff_minute=50,
        timezone_name="Europe/London",
    )
    return match_actuals_to_forecasts(actuals, selected)


def test_mae() -> None:
    metrics = accuracy_metrics(_matched(), mape_min_actual_mw=1.0)
    assert metrics["sample_count"] == 1
    assert metrics["mae_mw"] == 150.0


def test_rmse() -> None:
    metrics = accuracy_metrics(_matched(), mape_min_actual_mw=1.0)
    assert math.isclose(metrics["rmse_mw"], 150.0)


def test_bias() -> None:
    metrics = accuracy_metrics(_matched(), mape_min_actual_mw=1.0)
    assert metrics["bias_mw"] == 150.0


def test_mape_excludes_zero_actuals() -> None:
    actuals = actuals_frame(
        [
            {"start_time": utc(2026, 1, 2, 0, 0), "generation_mw": 0},
            {"start_time": utc(2026, 1, 2, 0, 30), "generation_mw": 0},
            {"start_time": utc(2026, 1, 2, 1, 0), "generation_mw": 100},
            {"start_time": utc(2026, 1, 2, 1, 30), "generation_mw": 100},
        ]
    )
    forecasts = forecasts_frame(
        [
            {"start_time": utc(2026, 1, 2, 0, 0), "publish_time": utc(2026, 1, 1, 8, 30), "generation_mw": 50},
            {"start_time": utc(2026, 1, 2, 1, 0), "publish_time": utc(2026, 1, 1, 8, 30), "generation_mw": 50},
        ]
    )
    selected = select_forecasts(
        forecasts,
        mode="decision_time",
        cutoff_hour=9,
        cutoff_minute=50,
        timezone_name="Europe/London",
    )
    matched = match_actuals_to_forecasts(actuals, selected)
    metrics = accuracy_metrics(matched, mape_min_actual_mw=1.0)
    assert metrics["sample_count"] == 2
    assert metrics["mape_sample_count"] == 1
    assert metrics["mape_excluded_count"] == 1
    assert math.isclose(metrics["mape_pct"], 50.0)


def test_missing_observations_are_not_treated_as_zero() -> None:
    actuals = actuals_frame(
        [
            {"start_time": utc(2026, 1, 2, 0, 0), "generation_mw": 1000},
            {"start_time": utc(2026, 1, 2, 0, 30), "generation_mw": 1000},
            {"start_time": utc(2026, 1, 2, 1, 0), "generation_mw": 1000},
            {"start_time": utc(2026, 1, 2, 1, 30), "generation_mw": 1000},
        ]
    )
    forecasts = forecasts_frame(
        [
            {"start_time": utc(2026, 1, 2, 0, 0), "publish_time": utc(2026, 1, 1, 8, 30), "generation_mw": 1200},
        ]
    )
    selected = select_forecasts(
        forecasts,
        mode="decision_time",
        cutoff_hour=9,
        cutoff_minute=50,
        timezone_name="Europe/London",
    )
    frame = match_actuals_to_forecasts(actuals, selected)
    matched = matched_rows(frame)
    metrics = accuracy_metrics(frame, mape_min_actual_mw=1.0)
    assert len(frame) == 2
    assert len(matched) == 1
    assert metrics["sample_count"] == 1
    assert metrics["mae_mw"] == 200.0
    assert pd.isna(frame.loc[frame["start_time"] == pd.Timestamp(utc(2026, 1, 2, 1, 0)), "forecast_mw"].iloc[0])

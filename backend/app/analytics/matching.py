from __future__ import annotations

from datetime import datetime

import pandas as pd

from app.core.timeutils import decision_cutoff_utc, ensure_utc, hour_floor_utc

DECISION_TIME = "decision_time"
LATEST_BEFORE_DELIVERY = "latest_before_delivery"


def actuals_frame(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["start_time", "generation_mw"])
    frame = pd.DataFrame(rows)
    frame["start_time"] = pd.to_datetime(frame["start_time"], utc=True)
    frame["generation_mw"] = pd.to_numeric(frame["generation_mw"], errors="coerce")
    frame = frame.dropna(subset=["start_time", "generation_mw"])
    frame = frame.drop_duplicates(subset=["start_time"], keep="first")
    return frame.sort_values("start_time").reset_index(drop=True)


def forecasts_frame(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["start_time", "publish_time", "generation_mw"])
    frame = pd.DataFrame(rows)
    frame["start_time"] = pd.to_datetime(frame["start_time"], utc=True)
    frame["publish_time"] = pd.to_datetime(frame["publish_time"], utc=True)
    frame["generation_mw"] = pd.to_numeric(frame["generation_mw"], errors="coerce")
    frame = frame.dropna(subset=["start_time", "publish_time", "generation_mw"])
    frame = frame.drop_duplicates(subset=["start_time", "publish_time"], keep="first")
    return frame.sort_values(["start_time", "publish_time"]).reset_index(drop=True)


def cutoff_for_start(
    start_time: datetime,
    *,
    mode: str,
    cutoff_hour: int,
    cutoff_minute: int,
    timezone_name: str,
) -> datetime:
    start_time = ensure_utc(start_time)
    if mode == LATEST_BEFORE_DELIVERY:
        return start_time
    if mode == DECISION_TIME:
        return decision_cutoff_utc(
            start_time,
            cutoff_hour=cutoff_hour,
            cutoff_minute=cutoff_minute,
            timezone_name=timezone_name,
        )
    raise ValueError(f"Unsupported selection mode: {mode}")


def select_forecasts(
    forecasts: pd.DataFrame,
    *,
    mode: str,
    cutoff_hour: int,
    cutoff_minute: int,
    timezone_name: str,
) -> pd.DataFrame:
    """Select the latest eligible revision per target start_time.

    Eligibility: publish_time <= cutoff. Forecasts published after the cutoff
    are excluded. If no eligible revision exists, the start_time is omitted.
    Duplicate (start_time, publish_time) rows are dropped before selection.
    """
    empty = pd.DataFrame(columns=["start_time", "publish_time", "generation_mw", "cutoff"])
    if forecasts.empty:
        return empty

    unique_starts = forecasts["start_time"].drop_duplicates()
    cutoff_map = {
        ts: pd.Timestamp(
            cutoff_for_start(
                ts.to_pydatetime(),
                mode=mode,
                cutoff_hour=cutoff_hour,
                cutoff_minute=cutoff_minute,
                timezone_name=timezone_name,
            )
        )
        for ts in unique_starts
    }
    working = forecasts.copy()
    working["cutoff"] = working["start_time"].map(cutoff_map)
    eligible = working[working["publish_time"] <= working["cutoff"]]
    if eligible.empty:
        return empty
    eligible = eligible.sort_values(["start_time", "publish_time"])
    selected = eligible.drop_duplicates(subset=["start_time"], keep="last")
    return selected.reset_index(drop=True)


def aggregate_actuals_to_hours(actuals: pd.DataFrame) -> pd.DataFrame:
    """Convert FUELHH half-hourly MW into hourly mean MW.

    FUELHH is average power over each 30-minute settlement period. WINDFOR is
    an hourly forecast. Metrics therefore compare one forecast to one actual
    for the same UTC hour.

    The hourly actual is the mean of the :00 and :30 MW readings. That mean is
    the correct average power over two equal-length intervals. Both readings
    must exist; a lone half-hour is dropped so a 30-minute sample is not
    treated as a full hour. The hourly forecast is never copied onto both
    half-hours for accuracy calculations.
    """
    columns = ["start_time", "generation_mw", "half_hour_count"]
    if actuals.empty:
        return pd.DataFrame(columns=columns)

    working = actuals.copy()
    working["start_time"] = pd.to_datetime(working["start_time"], utc=True)
    working["hour_start"] = working["start_time"].dt.floor("h")
    rows: list[dict] = []
    for hour_start, group in working.groupby("hour_start", sort=True):
        minutes = set(int(value) for value in group["start_time"].dt.minute.tolist())
        if not {0, 30}.issubset(minutes):
            continue
        rows.append(
            {
                "start_time": hour_start,
                "generation_mw": float(group["generation_mw"].mean()),
                "half_hour_count": int(len(group)),
            }
        )
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows)


def match_actuals_to_forecasts(
    actuals: pd.DataFrame,
    selected_forecasts: pd.DataFrame,
) -> pd.DataFrame:
    """Join hourly mean actuals to hourly selected forecasts.

    Missing forecasts stay as NA and are never filled with zero. Incomplete
    actual hours are omitted rather than padded.
    """
    columns = [
        "start_time",
        "actual_mw",
        "forecast_mw",
        "forecast_publish_time",
        "cutoff",
        "error_mw",
        "abs_error_mw",
        "pct_error",
        "interval_hours",
        "half_hour_count",
    ]
    hourly = aggregate_actuals_to_hours(actuals)
    if hourly.empty:
        return pd.DataFrame(columns=columns)

    actual_df = hourly.rename(columns={"generation_mw": "actual_mw"})
    forecast_df = selected_forecasts.copy()
    if forecast_df.empty:
        forecast_df = pd.DataFrame(columns=["start_time", "publish_time", "generation_mw", "cutoff"])
    forecast_df = forecast_df.rename(
        columns={
            "generation_mw": "forecast_mw",
            "publish_time": "forecast_publish_time",
        }
    )
    merged = actual_df.merge(forecast_df, on="start_time", how="left")
    merged["error_mw"] = merged["forecast_mw"] - merged["actual_mw"]
    merged["abs_error_mw"] = merged["error_mw"].abs()
    merged["pct_error"] = (merged["error_mw"] / merged["actual_mw"]) * 100
    merged.loc[merged["actual_mw"].abs() < 1e-12, "pct_error"] = pd.NA
    merged["interval_hours"] = 1.0
    return merged.sort_values("start_time").reset_index(drop=True)


def half_hourly_display_frame(
    actuals: pd.DataFrame,
    selected_forecasts: pd.DataFrame,
) -> pd.DataFrame:
    """Settlement-period actuals with the hourly forecast overlaid for charts.

    This is display-only. Accuracy metrics use match_actuals_to_forecasts.
    """
    columns = [
        "start_time",
        "actual_mw",
        "forecast_mw",
        "forecast_publish_time",
        "cutoff",
        "error_mw",
        "abs_error_mw",
        "pct_error",
        "interval_hours",
    ]
    if actuals.empty:
        return pd.DataFrame(columns=columns)

    actual_df = actuals.copy()
    actual_df["hour_start"] = actual_df["start_time"].dt.floor("h")
    forecast_df = selected_forecasts.copy()
    if forecast_df.empty:
        forecast_df = pd.DataFrame(columns=["start_time", "publish_time", "generation_mw", "cutoff"])
    forecast_df = forecast_df.rename(
        columns={
            "start_time": "hour_start",
            "generation_mw": "forecast_mw",
            "publish_time": "forecast_publish_time",
        }
    )
    merged = actual_df.merge(forecast_df, on="hour_start", how="left")
    merged = merged.rename(columns={"generation_mw": "actual_mw"})
    merged["error_mw"] = merged["forecast_mw"] - merged["actual_mw"]
    merged["abs_error_mw"] = merged["error_mw"].abs()
    merged["pct_error"] = (merged["error_mw"] / merged["actual_mw"]) * 100
    merged.loc[merged["actual_mw"].abs() < 1e-12, "pct_error"] = pd.NA
    merged["interval_hours"] = 0.5
    return merged.sort_values("start_time").reset_index(drop=True)


def expected_hours(start: datetime, end: datetime) -> pd.DatetimeIndex:
    return pd.date_range(start=ensure_utc(start), end=ensure_utc(end), freq="h", inclusive="left", tz="UTC")


def expected_half_hours(start: datetime, end: datetime) -> pd.DatetimeIndex:
    """Half-hourly index for settlement-period actual coverage checks."""
    return pd.date_range(start=ensure_utc(start), end=ensure_utc(end), freq="30min", inclusive="left", tz="UTC")


def hour_floor_py(start_time: datetime) -> datetime:
    return hour_floor_utc(start_time)

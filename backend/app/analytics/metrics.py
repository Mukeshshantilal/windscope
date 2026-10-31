from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd


def matched_rows(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    return frame.dropna(subset=["actual_mw", "forecast_mw"]).copy()


def accuracy_metrics(frame: pd.DataFrame, *, mape_min_actual_mw: float) -> dict:
    matched = matched_rows(frame)
    if matched.empty:
        return {
            "sample_count": 0,
            "mae_mw": None,
            "rmse_mw": None,
            "bias_mw": None,
            "mape_pct": None,
            "mape_sample_count": 0,
            "mape_excluded_count": 0,
            "average_actual_mw": None,
            "average_forecast_mw": None,
            "median_error_mw": None,
            "p50_abs_error_mw": None,
            "p75_abs_error_mw": None,
            "p90_abs_error_mw": None,
            "p95_abs_error_mw": None,
            "overforecast_count": 0,
            "underforecast_count": 0,
            "exact_count": 0,
        }

    actual = matched["actual_mw"].to_numpy(dtype=float)
    forecast = matched["forecast_mw"].to_numpy(dtype=float)
    errors = forecast - actual
    abs_errors = np.abs(errors)
    mape_mask = np.abs(actual) >= mape_min_actual_mw
    mape_values = np.abs((actual[mape_mask] - forecast[mape_mask]) / actual[mape_mask]) * 100

    return {
        "sample_count": int(len(matched)),
        "mae_mw": float(np.mean(abs_errors)),
        "rmse_mw": float(np.sqrt(np.mean(np.square(errors)))),
        "bias_mw": float(np.mean(errors)),
        "mape_pct": float(np.mean(mape_values)) if mape_values.size else None,
        "mape_sample_count": int(mape_values.size),
        "mape_excluded_count": int((~mape_mask).sum()),
        "average_actual_mw": float(np.mean(actual)),
        "average_forecast_mw": float(np.mean(forecast)),
        "median_error_mw": float(np.median(errors)),
        "p50_abs_error_mw": float(np.percentile(abs_errors, 50)),
        "p75_abs_error_mw": float(np.percentile(abs_errors, 75)),
        "p90_abs_error_mw": float(np.percentile(abs_errors, 90)),
        "p95_abs_error_mw": float(np.percentile(abs_errors, 95)),
        "overforecast_count": int((errors > 0).sum()),
        "underforecast_count": int((errors < 0).sum()),
        "exact_count": int((errors == 0).sum()),
    }


def coverage_stats(
    *,
    matched_count: int,
    actual_count: int,
    expected_count: int,
    missing_actual_count: int,
    missing_forecast_count: int,
) -> dict:
    coverage = (matched_count / expected_count * 100.0) if expected_count else None
    actual_coverage = (actual_count / expected_count * 100.0) if expected_count else None
    return {
        "expected_periods": expected_count,
        "actual_periods": actual_count,
        "matched_periods": matched_count,
        "missing_actual_periods": missing_actual_count,
        "missing_eligible_forecast_periods": missing_forecast_count,
        "data_coverage_pct": coverage,
        "actual_coverage_pct": actual_coverage,
    }


def daily_accuracy(frame: pd.DataFrame, timezone_name: str) -> pd.DataFrame:
    matched = matched_rows(frame)
    if matched.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "mae_mw",
                "rmse_mw",
                "bias_mw",
                "average_actual_mw",
                "average_forecast_mw",
                "sample_count",
                "actual_mwh",
                "forecast_mwh",
            ]
        )
    working = matched.copy()
    working["date"] = working["start_time"].dt.tz_convert(timezone_name).dt.strftime("%Y-%m-%d")
    grouped = working.groupby("date", sort=True)
    rows = []
    for day, group in grouped:
        errors = group["forecast_mw"] - group["actual_mw"]
        interval = group["interval_hours"] if "interval_hours" in group.columns else 1.0
        rows.append(
            {
                "date": day,
                "mae_mw": float(errors.abs().mean()),
                "rmse_mw": float(np.sqrt(np.mean(np.square(errors.to_numpy(dtype=float))))),
                "bias_mw": float(errors.mean()),
                "average_actual_mw": float(group["actual_mw"].mean()),
                "average_forecast_mw": float(group["forecast_mw"].mean()),
                "sample_count": int(len(group)),
                "actual_mwh": float((group["actual_mw"] * interval).sum()),
                "forecast_mwh": float((group["forecast_mw"] * interval).sum()),
            }
        )
    return pd.DataFrame(rows)


def error_histogram(frame: pd.DataFrame, bins: int = 24) -> dict:
    matched = matched_rows(frame)
    if matched.empty:
        return {"bins": [], "counts": []}
    errors = matched["error_mw"].to_numpy(dtype=float)
    counts, edges = np.histogram(errors, bins=bins)
    bins_out = [
        {"from": float(edges[i]), "to": float(edges[i + 1]), "count": int(counts[i])}
        for i in range(len(counts))
    ]
    return {"bins": bins_out, "counts": [int(v) for v in counts]}


def accuracy_by_hour(frame: pd.DataFrame, timezone_name: str) -> list[dict]:
    matched = matched_rows(frame)
    if matched.empty:
        return []
    working = matched.copy()
    working["hour"] = working["start_time"].dt.tz_convert(timezone_name).dt.hour
    rows = []
    for hour, group in working.groupby("hour"):
        errors = group["forecast_mw"] - group["actual_mw"]
        rows.append(
            {
                "hour": int(hour),
                "mae_mw": float(errors.abs().mean()),
                "bias_mw": float(errors.mean()),
                "sample_count": int(len(group)),
                "average_actual_mw": float(group["actual_mw"].mean()),
                "average_forecast_mw": float(group["forecast_mw"].mean()),
            }
        )
    return sorted(rows, key=lambda item: item["hour"])


def worst_periods(frame: pd.DataFrame, limit: int = 10) -> list[dict]:
    matched = matched_rows(frame)
    if matched.empty:
        return []
    worst = matched.sort_values("abs_error_mw", ascending=False).head(limit)
    return [
        {
            "start_time": _ts(row.start_time),
            "actual_mw": float(row.actual_mw),
            "forecast_mw": float(row.forecast_mw),
            "error_mw": float(row.error_mw),
            "abs_error_mw": float(row.abs_error_mw),
            "forecast_publish_time": _ts(row.forecast_publish_time) if pd.notna(row.forecast_publish_time) else None,
        }
        for row in worst.itertuples(index=False)
    ]


def worst_days(daily: pd.DataFrame, limit: int = 5) -> list[dict]:
    if daily.empty:
        return []
    worst = daily.sort_values("mae_mw", ascending=False).head(limit)
    return worst.to_dict(orient="records")


def series_points(frame: pd.DataFrame, granularity: str, timezone_name: str) -> list[dict]:
    if frame.empty:
        return []
    working = frame.copy()
    if granularity == "half_hourly":
        return [_point(row) for row in working.itertuples(index=False)]
    if granularity == "hourly":
        working["bucket"] = working["start_time"].dt.floor("h")
        return _aggregate_points(working, "bucket")
    if granularity == "daily":
        working["bucket"] = working["start_time"].dt.tz_convert(timezone_name).dt.normalize()
        return _aggregate_points(working, "bucket")
    raise ValueError(f"Unsupported granularity: {granularity}")


def _aggregate_points(frame: pd.DataFrame, bucket_col: str) -> list[dict]:
    points = []
    for bucket, group in frame.groupby(bucket_col, sort=True):
        matched = group.dropna(subset=["actual_mw", "forecast_mw"])
        hours = group["interval_hours"] if "interval_hours" in group.columns else 1.0
        matched_hours = matched["interval_hours"] if "interval_hours" in matched.columns else 1.0
        actual_mean = float(group["actual_mw"].mean()) if group["actual_mw"].notna().any() else None
        forecast_mean = float(matched["forecast_mw"].mean()) if not matched.empty else None
        error_mean = float(matched["error_mw"].mean()) if not matched.empty else None
        abs_error_mean = float(matched["abs_error_mw"].mean()) if not matched.empty else None
        points.append(
            {
                "start_time": _ts(bucket),
                "actual_mw": actual_mean,
                "forecast_mw": forecast_mean,
                "error_mw": error_mean,
                "abs_error_mw": abs_error_mean,
                "pct_error": float((error_mean / actual_mean) * 100) if error_mean is not None and actual_mean not in (None, 0) else None,
                "actual_mwh": float((group["actual_mw"] * hours).sum()) if group["actual_mw"].notna().any() else None,
                "forecast_mwh": float((matched["forecast_mw"] * matched_hours).sum()) if not matched.empty else None,
                "sample_count": int(len(matched)),
            }
        )
    return points


def _point(row: object) -> dict:
    actual = getattr(row, "actual_mw", None)
    forecast = getattr(row, "forecast_mw", None)
    error = getattr(row, "error_mw", None)
    abs_error = getattr(row, "abs_error_mw", None)
    pct = getattr(row, "pct_error", None)
    return {
        "start_time": _ts(getattr(row, "start_time")),
        "actual_mw": _num(actual),
        "forecast_mw": _num(forecast),
        "error_mw": _num(error),
        "abs_error_mw": _num(abs_error),
        "pct_error": _num(pct),
        "actual_mwh": _num(actual) * float(getattr(row, "interval_hours", 1.0) or 1.0)
        if actual is not None and pd.notna(actual)
        else None,
        "forecast_mwh": _num(forecast) * float(getattr(row, "interval_hours", 1.0) or 1.0)
        if forecast is not None and pd.notna(forecast)
        else None,
        "forecast_publish_time": _ts(getattr(row, "forecast_publish_time", None)),
        "cutoff": _ts(getattr(row, "cutoff", None)),
        "sample_count": 1 if forecast is not None and pd.notna(forecast) and actual is not None and pd.notna(actual) else 0,
    }


def _num(value: object) -> float | None:
    if value is None or (isinstance(value, float) and np.isnan(value)) or pd.isna(value):
        return None
    return float(value)


def _ts(value: object) -> datetime | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, datetime):
        return value
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.to_pydatetime()

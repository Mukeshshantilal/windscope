from datetime import date, datetime

import pandas as pd
from sqlalchemy.orm import Session

from app.analytics.matching import (
    actuals_frame,
    expected_hours,
    forecasts_frame,
    half_hourly_display_frame,
    select_forecasts,
)
from app.analytics.metrics import (
    accuracy_by_hour,
    accuracy_metrics,
    coverage_stats,
    daily_accuracy,
    error_histogram,
    matched_rows,
    series_points,
    worst_days,
    worst_periods,
)
from app.core.config import Settings
from app.core.timeutils import delivery_range_utc, hour_floor_utc
from app.services.actual_generation import ActualGenerationService
from app.services.forecast_selection import ForecastSelectionService
from app.services.wind_forecast import WindForecastService


class ForecastAccuracyService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.settings = settings
        self.actuals = ActualGenerationService(db)
        self.forecasts = WindForecastService(db)
        self.selection = ForecastSelectionService()

    def matched_frame(
        self,
        from_date: date,
        to_date: date,
        *,
        mode: str,
        cutoff_hour: int | None = None,
        cutoff_minute: int | None = None,
    ) -> tuple[pd.DataFrame, datetime, datetime]:
        start, end = delivery_range_utc(from_date, to_date, self.settings.display_timezone)
        actual_rows = self.actuals.list_between(start, end)
        forecast_rows = self.forecasts.list_for_start_range(hour_floor_utc(start), end)
        frame = self.selection.selected_frame(
            actual_rows,
            forecast_rows,
            mode=mode,
            cutoff_hour=cutoff_hour if cutoff_hour is not None else self.settings.decision_cutoff_hour,
            cutoff_minute=cutoff_minute if cutoff_minute is not None else self.settings.decision_cutoff_minute,
            timezone_name=self.settings.decision_cutoff_timezone,
        )
        return frame, start, end

    def metrics(self, from_date: date, to_date: date, *, mode: str) -> dict:
        frame, start, end = self.matched_frame(from_date, to_date, mode=mode)
        matched = matched_rows(frame)
        expected = expected_hours(start, end)
        actual_times = set(pd.to_datetime(frame["start_time"], utc=True)) if not frame.empty else set()
        expected_set = set(expected)
        missing_actual = expected_set - actual_times
        missing_forecast = 0
        if not frame.empty:
            missing_forecast = int(frame["forecast_mw"].isna().sum())
        stats = accuracy_metrics(frame, mape_min_actual_mw=self.settings.mape_min_actual_mw)
        coverage = coverage_stats(
            matched_count=int(len(matched)),
            actual_count=int(len(frame)),
            expected_count=int(len(expected)),
            missing_actual_count=len(missing_actual),
            missing_forecast_count=missing_forecast,
        )
        daily = daily_accuracy(frame, self.settings.display_timezone)
        warehouse_actuals = self.actuals.stats()["count"]
        warehouse_forecasts = self.forecasts.stats()["count"]
        if warehouse_actuals == 0 and warehouse_forecasts == 0:
            empty_reason = "not_imported"
        elif int(len(matched)) == 0:
            empty_reason = "unmatched" if warehouse_actuals else "no_records_in_range"
        else:
            empty_reason = None
        return {
            **stats,
            **coverage,
            "empty_reason": empty_reason,
            "period_unit": "hour",
            "warehouse_actual_records": warehouse_actuals,
            "warehouse_forecast_records": warehouse_forecasts,
            "daily": daily,
            "by_hour": accuracy_by_hour(frame, self.settings.display_timezone),
            "histogram": error_histogram(frame),
            "worst_periods": worst_periods(frame),
            "worst_days": worst_days(daily),
            "frame": frame,
            "range_start": start,
            "range_end": end,
        }

    def series(self, from_date: date, to_date: date, *, mode: str, granularity: str) -> dict:
        payload = self.metrics(from_date, to_date, mode=mode)
        if granularity == "half_hourly":
            points = series_points(
                self._half_hourly_display(from_date, to_date, mode=mode),
                "half_hourly",
                self.settings.display_timezone,
            )
        else:
            points = series_points(payload["frame"], granularity, self.settings.display_timezone)
        return {
            **payload,
            "points": points,
        }

    def _half_hourly_display(self, from_date: date, to_date: date, *, mode: str) -> pd.DataFrame:
        start, end = delivery_range_utc(from_date, to_date, self.settings.display_timezone)
        actuals = actuals_frame(self.actuals.list_between(start, end))
        forecasts = forecasts_frame(self.forecasts.list_for_start_range(hour_floor_utc(start), end))
        selected = select_forecasts(
            forecasts,
            mode=mode,
            cutoff_hour=self.settings.decision_cutoff_hour,
            cutoff_minute=self.settings.decision_cutoff_minute,
            timezone_name=self.settings.decision_cutoff_timezone,
        )
        return half_hourly_display_frame(actuals, selected)

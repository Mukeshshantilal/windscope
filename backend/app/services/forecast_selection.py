from datetime import datetime

import pandas as pd

from app.analytics.matching import (
    DECISION_TIME,
    actuals_frame,
    cutoff_for_start,
    forecasts_frame,
    match_actuals_to_forecasts,
    select_forecasts,
)
from app.core.timeutils import ensure_utc


class ForecastSelectionService:
    """Point-in-time forecast selection.

    Algorithm:
    1. Group WINDFOR rows by target start_time.
    2. Compute a cutoff for that target.
       - decision_time: 09:50 Europe/London on the UK day before delivery
         (configurable; documented as an assumption).
       - latest_before_delivery: the delivery period start_time itself.
    3. Keep revisions with publish_time <= cutoff.
    4. Choose the revision with the latest publish_time.
    5. If none remain, the target has no eligible forecast.

    Forecasts published after the cutoff are never selected.
    """

    def selected_frame(
        self,
        actual_rows: list[dict],
        forecast_rows: list[dict],
        *,
        mode: str = DECISION_TIME,
        cutoff_hour: int,
        cutoff_minute: int,
        timezone_name: str,
    ) -> pd.DataFrame:
        actuals = actuals_frame(actual_rows)
        forecasts = forecasts_frame(forecast_rows)
        selected = select_forecasts(
            forecasts,
            mode=mode,
            cutoff_hour=cutoff_hour,
            cutoff_minute=cutoff_minute,
            timezone_name=timezone_name,
        )
        return match_actuals_to_forecasts(actuals, selected)

    def choose_revision(
        self,
        revisions: list[dict],
        start_time: datetime,
        *,
        mode: str,
        cutoff_hour: int,
        cutoff_minute: int,
        timezone_name: str,
    ) -> dict | None:
        cutoff = cutoff_for_start(
            start_time,
            mode=mode,
            cutoff_hour=cutoff_hour,
            cutoff_minute=cutoff_minute,
            timezone_name=timezone_name,
        )
        eligible = [
            row
            for row in revisions
            if ensure_utc(row["publish_time"]) <= cutoff
        ]
        if not eligible:
            return None
        return max(eligible, key=lambda row: ensure_utc(row["publish_time"]))

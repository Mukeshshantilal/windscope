from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_dep, parse_range, range_payload, settings_dep
from app.core.config import Settings
from app.repositories.store import ImportRunRepository
from app.services.actual_generation import ActualGenerationService
from app.services.forecast_accuracy import ForecastAccuracyService
from app.services.wind_forecast import WindForecastService

router = APIRouter()


@router.get("/data/quality")
def data_quality(
    date_range: tuple[date, date] = Depends(parse_range),
    db: Session = Depends(db_dep),
    settings: Settings = Depends(settings_dep),
) -> dict:
    actuals = ActualGenerationService(db).stats()
    forecasts = WindForecastService(db).stats()
    service = ForecastAccuracyService(db, settings)
    from_date, to_date = date_range
    payload = service.metrics(from_date, to_date, mode="decision_time")
    latest = ImportRunRepository(db).latest_successful()
    recent = ImportRunRepository(db).list_recent()
    return {
        "total_actual_records": actuals["count"],
        "total_forecast_records": forecasts["count"],
        "actual_timestamp_range": {"min": actuals["min_start"], "max": actuals["max_start"]},
        "forecast_timestamp_range": {"min": forecasts["min_start"], "max": forecasts["max_start"]},
        "matched_delivery_periods": payload["matched_periods"],
        "missing_actual_periods": payload["missing_actual_periods"],
        "missing_eligible_forecast_periods": payload["missing_eligible_forecast_periods"],
        "expected_periods": payload["expected_periods"],
        "period_unit": payload["period_unit"],
        "coverage_range": range_payload(from_date, to_date, settings),
        "empty_reason": payload["empty_reason"],
        "data_coverage_pct": payload["data_coverage_pct"],
        "last_successful_import": None
        if latest is None
        else {
            "dataset": latest.dataset,
            "completed_at": latest.completed_at,
            "records_processed": latest.records_processed,
        },
        "recent_imports": [
            {
                "dataset": run.dataset,
                "started_at": run.started_at,
                "completed_at": run.completed_at,
                "status": run.status,
                "records_processed": run.records_processed,
                "error_message": run.error_message,
            }
            for run in recent
        ],
        "methodology": {
            "sources": {
                "actuals": "Elexon BMRS FUELHH stream, fuelType=WIND, generation as average MW over each settlement period.",
                "forecasts": "Elexon BMRS WINDFOR stream. Hourly NESO wind generation forecast revisions.",
            },
            "decision_cutoff_assumption": {
                "hour": settings.decision_cutoff_hour,
                "minute": settings.decision_cutoff_minute,
                "timezone": settings.decision_cutoff_timezone,
                "is_assumption": True,
                "rationale": (
                    "Nord Pool N2EX GB day-ahead auction gate closure is 09:50 UK time. "
                    "WindScope uses this clock time on the UK calendar day before delivery "
                    "as a configurable proxy for purchasing-decision cutoff. It is not a "
                    "confirmed internal trading-desk rule."
                ),
            },
            "forecast_selection": (
                "For each hourly target, keep WINDFOR revisions with publishTime <= cutoff "
                "and select the latest remaining publishTime. Forecasts published after the "
                "cutoff are excluded. Missing eligible forecasts stay missing and are not "
                "filled with zero."
            ),
            "matching": (
                "FUELHH is half-hourly average MW. WINDFOR is an hourly MW forecast. "
                "Accuracy uses one observation per UTC hour: the mean of the :00 and :30 "
                "actuals, matched to the selected hourly forecast. Both half-hours must "
                "exist; incomplete hours are dropped. The forecast is not copied onto both "
                "half-hours for MAE, RMSE, bias, MAPE, or coverage. Date filters are "
                "inclusive UK delivery dates. The purchasing decision date is the previous "
                "UK calendar day. Overview and Data Quality use the same from/to window "
                "for expected-hour counts."
            ),
            "formulas": {
                "error": "Forecast - Actual",
                "mae": "mean(abs(Forecast - Actual))",
                "rmse": "sqrt(mean((Forecast - Actual)^2))",
                "bias": "mean(Forecast - Actual)",
                "mape": (
                    f"mean(abs((Actual - Forecast) / Actual)) * 100, excluding |Actual| < "
                    f"{settings.mape_min_actual_mw} MW"
                ),
            },
            "aggregation": (
                "Matched metrics are hourly. Daily average MW is the mean of those hourly MW "
                "values. Daily energy is sum(hourly MW * 1 h). Half-hourly charts show "
                "settlement-period actuals with the hourly forecast overlaid for display only."
            ),
            "limitations": [
                "FUELHH WIND and WINDFOR are related but not guaranteed to use identical plant sets.",
                "The decision cutoff is an assumption.",
                "January 2026 is GMT, so UK local time equals UTC for this assignment window.",
                "The app reads imported historical data rather than calling Elexon on every request.",
            ],
        },
    }

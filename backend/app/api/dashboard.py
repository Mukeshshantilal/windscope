from datetime import date

from fastapi import APIRouter, Depends

from app.api.deps import accuracy_service, parse_mode, parse_range, range_payload, settings_dep
from app.core.config import Settings
from app.schemas.common import SelectionMode
from app.services.forecast_accuracy import ForecastAccuracyService

router = APIRouter()


@router.get("/dashboard/summary")
def dashboard_summary(
    date_range: tuple[date, date] = Depends(parse_range),
    mode: SelectionMode = Depends(parse_mode),
    settings: Settings = Depends(settings_dep),
    service: ForecastAccuracyService = Depends(accuracy_service),
) -> dict:
    from_date, to_date = date_range
    payload = service.metrics(from_date, to_date, mode=mode)
    return {
        "range": range_payload(from_date, to_date, settings),
        "selection_mode": mode,
        "decision_cutoff": {
            "hour": settings.decision_cutoff_hour,
            "minute": settings.decision_cutoff_minute,
            "timezone": settings.decision_cutoff_timezone,
            "is_assumption": True,
        },
        "kpis": {
            "average_actual_mw": payload["average_actual_mw"],
            "average_forecast_mw": payload["average_forecast_mw"],
            "mae_mw": payload["mae_mw"],
            "rmse_mw": payload["rmse_mw"],
            "bias_mw": payload["bias_mw"],
            "data_coverage_pct": payload["data_coverage_pct"],
            "matched_periods": payload["matched_periods"],
            "expected_periods": payload["expected_periods"],
            "period_unit": payload["period_unit"],
        },
        "empty_reason": payload["empty_reason"],
        "accuracy_summary": {
            "mape_pct": payload["mape_pct"],
            "mape_sample_count": payload["mape_sample_count"],
            "mape_excluded_count": payload["mape_excluded_count"],
            "overforecast_count": payload["overforecast_count"],
            "underforecast_count": payload["underforecast_count"],
            "p50_abs_error_mw": payload["p50_abs_error_mw"],
            "p90_abs_error_mw": payload["p90_abs_error_mw"],
            "p95_abs_error_mw": payload["p95_abs_error_mw"],
        },
        "worst_days": payload["worst_days"],
        "daily_error": payload["daily"].to_dict(orient="records"),
        "forecast_coverage": {
            "actual_periods": payload["actual_periods"],
            "matched_periods": payload["matched_periods"],
            "missing_actual_periods": payload["missing_actual_periods"],
            "missing_eligible_forecast_periods": payload["missing_eligible_forecast_periods"],
            "actual_coverage_pct": payload["actual_coverage_pct"],
            "data_coverage_pct": payload["data_coverage_pct"],
        },
    }

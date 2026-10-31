from datetime import date

from fastapi import APIRouter, Depends

from app.api.deps import accuracy_service, parse_mode, parse_range, settings_dep
from app.core.config import Settings
from app.schemas.common import SelectionMode
from app.services.forecast_accuracy import ForecastAccuracyService

router = APIRouter()


def _strip_frame(payload: dict) -> dict:
    data = dict(payload)
    data.pop("frame", None)
    daily = data.get("daily")
    if daily is not None and hasattr(daily, "to_dict"):
        data["daily"] = daily.to_dict(orient="records")
    return data


@router.get("/accuracy/metrics")
def accuracy_metrics(
    date_range: tuple[date, date] = Depends(parse_range),
    mode: SelectionMode = Depends(parse_mode),
    settings: Settings = Depends(settings_dep),
    service: ForecastAccuracyService = Depends(accuracy_service),
) -> dict:
    from_date, to_date = date_range
    payload = _strip_frame(service.metrics(from_date, to_date, mode=mode))
    payload["mape_notes"] = (
        f"MAPE excludes periods where |actual| < {settings.mape_min_actual_mw} MW, "
        "including zeros. Missing observations are never treated as zero."
    )
    payload["selection_mode"] = mode
    return payload


@router.get("/accuracy/daily")
def accuracy_daily(
    date_range: tuple[date, date] = Depends(parse_range),
    mode: SelectionMode = Depends(parse_mode),
    service: ForecastAccuracyService = Depends(accuracy_service),
) -> dict:
    from_date, to_date = date_range
    payload = service.metrics(from_date, to_date, mode=mode)
    return {"items": payload["daily"].to_dict(orient="records"), "selection_mode": mode}


@router.get("/accuracy/distribution")
def accuracy_distribution(
    date_range: tuple[date, date] = Depends(parse_range),
    mode: SelectionMode = Depends(parse_mode),
    service: ForecastAccuracyService = Depends(accuracy_service),
) -> dict:
    from_date, to_date = date_range
    payload = service.metrics(from_date, to_date, mode=mode)
    return {
        "histogram": payload["histogram"],
        "by_hour": payload["by_hour"],
        "worst_periods": payload["worst_periods"],
        "overforecast_count": payload["overforecast_count"],
        "underforecast_count": payload["underforecast_count"],
        "exact_count": payload["exact_count"],
        "selection_mode": mode,
    }

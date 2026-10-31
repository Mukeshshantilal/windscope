from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query

from app.analytics.matching import cutoff_for_start
from app.api.deps import accuracy_service, db_dep, parse_mode, parse_range, settings_dep
from app.core.config import Settings
from app.core.timeutils import delivery_range_utc, ensure_utc, hour_floor_utc
from app.schemas.common import SelectionMode
from app.services.actual_generation import ActualGenerationService
from app.services.forecast_accuracy import ForecastAccuracyService
from app.services.forecast_selection import ForecastSelectionService
from app.services.wind_forecast import WindForecastService
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/forecasts/targets")
def forecast_targets(
    date_range: tuple[date, date] = Depends(parse_range),
    settings: Settings = Depends(settings_dep),
    service: ForecastAccuracyService = Depends(accuracy_service),
) -> dict:
    from_date, to_date = date_range
    start, end = delivery_range_utc(from_date, to_date, settings.display_timezone)
    times = service.forecasts.target_times(hour_floor_utc(start), end)
    return {"items": times, "count": len(times)}


@router.get("/forecasts/revisions")
def forecast_revisions(
    start_time: datetime = Query(..., description="Target delivery timestamp (UTC)"),
    mode: SelectionMode = Depends(parse_mode),
    db: Session = Depends(db_dep),
    settings: Settings = Depends(settings_dep),
) -> dict:
    target = hour_floor_utc(start_time)
    forecast_service = WindForecastService(db)
    actual_service = ActualGenerationService(db)
    revisions = forecast_service.revisions(target)
    if not revisions:
        nearby = forecast_service.revisions(start_time)
        if not nearby:
            raise HTTPException(
                status_code=404,
                detail="No WINDFOR revisions found for that target timestamp.",
            )
        revisions = nearby
        target = start_time

    cutoff = cutoff_for_start(
        target,
        mode=mode,
        cutoff_hour=settings.decision_cutoff_hour,
        cutoff_minute=settings.decision_cutoff_minute,
        timezone_name=settings.decision_cutoff_timezone,
    )
    selected = ForecastSelectionService().choose_revision(
        revisions,
        target,
        mode=mode,
        cutoff_hour=settings.decision_cutoff_hour,
        cutoff_minute=settings.decision_cutoff_minute,
        timezone_name=settings.decision_cutoff_timezone,
    )
    actuals = actual_service.list_between(target, target + timedelta(hours=1))
    actual_mw = None
    if len(actuals) == 2:
        actual_mw = sum(item["generation_mw"] for item in actuals) / 2

    selected_publish = selected["publish_time"] if selected else None
    items = []
    for row in revisions:
        items.append(
            {
                "publish_time": row["publish_time"],
                "generation_mw": row["generation_mw"],
                "eligible_at_decision": ensure_utc(row["publish_time"]) <= cutoff,
                "selected": selected_publish is not None
                and ensure_utc(row["publish_time"]) == ensure_utc(selected_publish),
            }
        )

    return {
        "target_start_time": target,
        "actual_mw": actual_mw,
        "actual_half_hours": actuals,
        "decision_cutoff": cutoff,
        "selection_mode": mode,
        "selected": selected,
        "revisions": items,
        "decision_cutoff_assumption": {
            "hour": settings.decision_cutoff_hour,
            "minute": settings.decision_cutoff_minute,
            "timezone": settings.decision_cutoff_timezone,
            "is_assumption": True,
        },
    }

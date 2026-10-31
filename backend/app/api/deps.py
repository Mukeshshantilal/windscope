from datetime import date

from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.timeutils import decision_dates_for_delivery, delivery_range_utc
from app.db.session import get_db
from app.schemas.common import Granularity, SelectionMode
from app.services.forecast_accuracy import ForecastAccuracyService


def settings_dep() -> Settings:
    return get_settings()


def db_dep(db: Session = Depends(get_db)) -> Session:
    return db


def parse_range(
    from_date: date = Query(default=date(2026, 1, 1), alias="from"),
    to_date: date = Query(default=date(2026, 1, 31), alias="to"),
    settings: Settings = Depends(settings_dep),
) -> tuple[date, date]:
    if from_date > to_date:
        raise HTTPException(status_code=400, detail="`from` must be on or before `to`.")
    if from_date < settings.supported_delivery_start or to_date > settings.supported_delivery_end:
        raise HTTPException(
            status_code=400,
            detail=(
                "Date range must fall within the supported delivery window "
                f"{settings.supported_delivery_start.isoformat()} to "
                f"{settings.supported_delivery_end.isoformat()}."
            ),
        )
    return from_date, to_date


def parse_mode(
    selection: SelectionMode = Query(default="decision_time"),
) -> SelectionMode:
    return selection


def parse_granularity(
    granularity: Granularity = Query(default="daily"),
) -> Granularity:
    return granularity


def accuracy_service(
    db: Session = Depends(db_dep),
    settings: Settings = Depends(settings_dep),
) -> ForecastAccuracyService:
    return ForecastAccuracyService(db, settings)


def range_payload(from_date: date, to_date: date, settings: Settings) -> dict:
    start, end = delivery_range_utc(from_date, to_date, settings.display_timezone)
    decision_from, decision_to = decision_dates_for_delivery(from_date, to_date)
    return {
        "from": from_date,
        "to": to_date,
        "basis": "delivery",
        "timezone": settings.display_timezone,
        "start_utc": start,
        "end_utc_exclusive": end,
        "decision_from": decision_from,
        "decision_to": decision_to,
        "resolution": "hourly",
    }

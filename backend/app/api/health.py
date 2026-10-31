from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import db_dep, settings_dep
from app.core.config import Settings
from app.repositories.store import ActualRepository, ForecastRepository, ImportRunRepository

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(db_dep), settings: Settings = Depends(settings_dep)) -> dict:
    database = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        database = f"error: {exc}"

    latest = ImportRunRepository(db).latest_successful()
    actual_records = ActualRepository(db).count()
    forecast_records = ForecastRepository(db).count()
    imported = actual_records > 0 and forecast_records > 0
    return {
        "status": "ok" if database == "ok" else "degraded",
        "service": settings.app_name,
        "database": database,
        "warehouse": {
            "actual_records": actual_records,
            "forecast_records": forecast_records,
            "imported": imported,
        },
        "import_hint": (
            "From backend/: python -m app.cli import-historical. "
            "Or: docker compose --profile import run --rm importer"
        ),
        "last_successful_import": None
        if latest is None or latest.completed_at is None
        else {
            "dataset": latest.dataset,
            "completed_at": latest.completed_at,
            "records_processed": latest.records_processed,
        },
        "decision_cutoff": {
            "hour": settings.decision_cutoff_hour,
            "minute": settings.decision_cutoff_minute,
            "timezone": settings.decision_cutoff_timezone,
            "is_assumption": True,
        },
    }

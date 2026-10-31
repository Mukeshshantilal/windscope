from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, time, timezone

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.timeutils import parse_elexon_datetime, utc_now
from app.repositories.store import ActualRepository, ForecastRepository, ImportRunRepository
from app.services.elexon_client import ElexonAPIClient

logger = logging.getLogger(__name__)


class DataImportService:
    def __init__(self, db: Session, settings: Settings, client: ElexonAPIClient | None = None) -> None:
        self.db = db
        self.settings = settings
        self.client = client or ElexonAPIClient(settings)
        self.actuals = ActualRepository(db)
        self.forecasts = ForecastRepository(db)
        self.runs = ImportRunRepository(db)

    def import_historical(self) -> dict:
        actuals = self.import_actuals(
            self.settings.import_actuals_start,
            self.settings.import_actuals_end,
        )
        forecasts = self.import_forecasts(
            self.settings.import_forecast_publish_start,
            self.settings.import_forecast_publish_end,
        )
        return {"actuals": actuals, "forecasts": forecasts}

    def import_actuals(self, start: date, end: date, chunk_days: int = 7) -> dict:
        run = self.runs.start("FUELHH", utc_now())
        self.db.commit()
        inserted = 0
        processed = 0
        try:
            cursor = start
            while cursor <= end:
                chunk_end = min(cursor + timedelta(days=chunk_days - 1), end)
                rows = self.client.fetch_fuelhh_wind(cursor, chunk_end)
                payload = []
                seen: set[datetime] = set()
                for row in rows:
                    start_time = parse_elexon_datetime(row["startTime"])
                    generation = row.get("generation")
                    if generation is None or start_time in seen:
                        continue
                    seen.add(start_time)
                    payload.append(
                        {
                            "start_time": start_time,
                            "generation_mw": float(generation),
                            "source": "FUELHH",
                            "imported_at": utc_now(),
                        }
                    )
                processed += len(payload)
                inserted += self.actuals.bulk_insert_ignore(payload)
                self.db.commit()
                logger.info("Imported FUELHH WIND %s to %s (%s rows)", cursor, chunk_end, len(payload))
                cursor = chunk_end + timedelta(days=1)
            if processed == 0:
                raise RuntimeError(
                    f"Elexon FUELHH returned 0 WIND records for {start} to {end}. "
                    "Import refused so empty results are not treated as success."
                )
            self.runs.complete(
                run,
                status="success",
                records_processed=processed,
                error_message=None,
                completed_at=utc_now(),
            )
            self.db.commit()
            return {"dataset": "FUELHH", "records_processed": processed, "records_inserted": inserted, "status": "success"}
        except Exception as exc:
            self.db.rollback()
            self.runs.complete(
                run,
                status="failed",
                records_processed=processed,
                error_message=str(exc),
                completed_at=utc_now(),
            )
            self.db.commit()
            raise

    def import_forecasts(self, publish_start: date, publish_end: date, chunk_hours: int = 12) -> dict:
        run = self.runs.start("WINDFOR", utc_now())
        self.db.commit()
        inserted = 0
        processed = 0
        try:
            cursor = datetime.combine(publish_start, time.min, tzinfo=timezone.utc)
            end_dt = datetime.combine(publish_end + timedelta(days=1), time.min, tzinfo=timezone.utc)
            while cursor < end_dt:
                chunk_end = min(cursor + timedelta(hours=chunk_hours), end_dt)
                rows = self.client.fetch_windfor(cursor, chunk_end - timedelta(seconds=1))
                payload = []
                seen: set[tuple[datetime, datetime]] = set()
                for row in rows:
                    start_time = parse_elexon_datetime(row["startTime"])
                    publish_time = parse_elexon_datetime(row["publishTime"])
                    generation = row.get("generation")
                    key = (start_time, publish_time)
                    if generation is None or key in seen:
                        continue
                    seen.add(key)
                    payload.append(
                        {
                            "start_time": start_time,
                            "publish_time": publish_time,
                            "generation_mw": float(generation),
                            "source": "WINDFOR",
                            "imported_at": utc_now(),
                        }
                    )
                processed += len(payload)
                inserted += self.forecasts.bulk_insert_ignore(payload)
                self.db.commit()
                logger.info("Imported WINDFOR publish %s to %s (%s rows)", cursor, chunk_end, len(payload))
                cursor = chunk_end
            if processed == 0:
                raise RuntimeError(
                    f"Elexon WINDFOR returned 0 records for publish {publish_start} to {publish_end}. "
                    "Import refused so empty results are not treated as success."
                )
            self.runs.complete(
                run,
                status="success",
                records_processed=processed,
                error_message=None,
                completed_at=utc_now(),
            )
            self.db.commit()
            return {"dataset": "WINDFOR", "records_processed": processed, "records_inserted": inserted, "status": "success"}
        except Exception as exc:
            self.db.rollback()
            self.runs.complete(
                run,
                status="failed",
                records_processed=processed,
                error_message=str(exc),
                completed_at=utc_now(),
            )
            self.db.commit()
            raise

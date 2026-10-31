from datetime import datetime

from sqlalchemy.orm import Session

from app.core.timeutils import ensure_utc
from app.repositories.store import ForecastRepository


class WindForecastService:
    def __init__(self, db: Session) -> None:
        self.repo = ForecastRepository(db)

    def list_for_start_range(self, start: datetime, end: datetime) -> list[dict]:
        rows = self.repo.list_for_start_range(start, end)
        return [
            {
                "start_time": ensure_utc(row.start_time),
                "publish_time": ensure_utc(row.publish_time),
                "generation_mw": row.generation_mw,
                "source": row.source,
            }
            for row in rows
        ]

    def revisions(self, start_time: datetime) -> list[dict]:
        rows = self.repo.list_revisions(start_time)
        return [
            {
                "start_time": ensure_utc(row.start_time),
                "publish_time": ensure_utc(row.publish_time),
                "generation_mw": row.generation_mw,
                "source": row.source,
            }
            for row in rows
        ]

    def target_times(self, start: datetime, end: datetime) -> list[datetime]:
        return self.repo.distinct_start_times(start, end)

    def stats(self) -> dict:
        return {
            "count": self.repo.count(),
            "min_start": self.repo.min_start(),
            "max_start": self.repo.max_start(),
        }

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.timeutils import ensure_utc
from app.repositories.store import ActualRepository


class ActualGenerationService:
    def __init__(self, db: Session) -> None:
        self.repo = ActualRepository(db)

    def list_between(self, start: datetime, end: datetime) -> list[dict]:
        rows = self.repo.list_between(start, end)
        return [
            {
                "start_time": ensure_utc(row.start_time),
                "generation_mw": row.generation_mw,
                "source": row.source,
            }
            for row in rows
        ]

    def stats(self) -> dict:
        return {
            "count": self.repo.count(),
            "min_start": self.repo.min_start(),
            "max_start": self.repo.max_start(),
        }

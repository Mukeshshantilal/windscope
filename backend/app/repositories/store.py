from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.entities import ImportRun, WindActual, WindForecast


class ActualRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_between(self, start: datetime, end: datetime) -> list[WindActual]:
        stmt = (
            select(WindActual)
            .where(WindActual.start_time >= start, WindActual.start_time < end)
            .order_by(WindActual.start_time)
        )
        return list(self.db.scalars(stmt).all())

    def count(self) -> int:
        return int(self.db.scalar(select(func.count()).select_from(WindActual)) or 0)

    def min_start(self) -> datetime | None:
        return self.db.scalar(select(func.min(WindActual.start_time)))

    def max_start(self) -> datetime | None:
        return self.db.scalar(select(func.max(WindActual.start_time)))

    def bulk_insert_ignore(self, rows: list[dict]) -> int:
        if not rows:
            return 0
        bind = self.db.get_bind()
        if bind.dialect.name == "postgresql":
            stmt = pg_insert(WindActual).values(rows).on_conflict_do_nothing(
                index_elements=["start_time"]
            )
            result = self.db.execute(stmt)
            return int(result.rowcount or 0)
        inserted = 0
        for row in rows:
            exists = self.db.scalar(select(WindActual.id).where(WindActual.start_time == row["start_time"]))
            if exists:
                continue
            self.db.add(WindActual(**row))
            inserted += 1
        return inserted


class ForecastRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_start_range(self, start: datetime, end: datetime) -> list[WindForecast]:
        stmt = (
            select(WindForecast)
            .where(WindForecast.start_time >= start, WindForecast.start_time < end)
            .order_by(WindForecast.start_time, WindForecast.publish_time)
        )
        return list(self.db.scalars(stmt).all())

    def list_revisions(self, start_time: datetime) -> list[WindForecast]:
        stmt = (
            select(WindForecast)
            .where(WindForecast.start_time == start_time)
            .order_by(WindForecast.publish_time)
        )
        return list(self.db.scalars(stmt).all())

    def distinct_start_times(self, start: datetime, end: datetime) -> list[datetime]:
        stmt = (
            select(WindForecast.start_time)
            .where(WindForecast.start_time >= start, WindForecast.start_time < end)
            .distinct()
            .order_by(WindForecast.start_time)
        )
        return list(self.db.scalars(stmt).all())

    def count(self) -> int:
        return int(self.db.scalar(select(func.count()).select_from(WindForecast)) or 0)

    def min_start(self) -> datetime | None:
        return self.db.scalar(select(func.min(WindForecast.start_time)))

    def max_start(self) -> datetime | None:
        return self.db.scalar(select(func.max(WindForecast.start_time)))

    def bulk_insert_ignore(self, rows: list[dict]) -> int:
        if not rows:
            return 0
        bind = self.db.get_bind()
        if bind.dialect.name == "postgresql":
            stmt = pg_insert(WindForecast).values(rows).on_conflict_do_nothing(
                index_elements=["start_time", "publish_time"]
            )
            result = self.db.execute(stmt)
            return int(result.rowcount or 0)
        inserted = 0
        for row in rows:
            exists = self.db.scalar(
                select(WindForecast.id).where(
                    WindForecast.start_time == row["start_time"],
                    WindForecast.publish_time == row["publish_time"],
                )
            )
            if exists:
                continue
            self.db.add(WindForecast(**row))
            inserted += 1
        return inserted


class ImportRunRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def start(self, dataset: str, started_at: datetime) -> ImportRun:
        run = ImportRun(
            dataset=dataset,
            started_at=started_at,
            status="running",
            records_processed=0,
        )
        self.db.add(run)
        self.db.flush()
        return run

    def complete(self, run: ImportRun, *, status: str, records_processed: int, error_message: str | None, completed_at: datetime) -> None:
        run.status = status
        run.records_processed = records_processed
        run.error_message = error_message
        run.completed_at = completed_at

    def latest_successful(self) -> ImportRun | None:
        stmt = (
            select(ImportRun)
            .where(ImportRun.status == "success")
            .order_by(ImportRun.completed_at.desc())
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def list_recent(self, limit: int = 20) -> list[ImportRun]:
        stmt = select(ImportRun).order_by(ImportRun.started_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())

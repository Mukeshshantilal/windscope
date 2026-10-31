import os

os.environ.setdefault("DATABASE_URL", "sqlite://")

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import SessionLocal, engine, get_db
from app.main import app
from app.models.entities import WindActual, WindForecast


UTC = timezone.utc


@pytest.fixture
def db() -> Session:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db: Session) -> TestClient:
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def utc(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


def seed_decision_example(db: Session) -> None:
    """Two half-hours on 2 Jan 2026 with three forecast revisions."""
    db.add_all(
        [
            WindActual(start_time=utc(2026, 1, 2, 0, 0), generation_mw=1000, source="FUELHH"),
            WindActual(start_time=utc(2026, 1, 2, 0, 30), generation_mw=1100, source="FUELHH"),
            WindForecast(
                start_time=utc(2026, 1, 2, 0, 0),
                publish_time=utc(2026, 1, 1, 5, 30),
                generation_mw=1500,
                source="WINDFOR",
            ),
            WindForecast(
                start_time=utc(2026, 1, 2, 0, 0),
                publish_time=utc(2026, 1, 1, 8, 30),
                generation_mw=1200,
                source="WINDFOR",
            ),
            WindForecast(
                start_time=utc(2026, 1, 2, 0, 0),
                publish_time=utc(2026, 1, 1, 10, 30),
                generation_mw=900,
                source="WINDFOR",
            ),
        ]
    )
    db.commit()

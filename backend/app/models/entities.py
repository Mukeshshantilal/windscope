from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WindActual(Base):
    __tablename__ = "wind_actuals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    generation_mw: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="FUELHH")
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("start_time", name="uq_wind_actuals_start_time"),
        Index("ix_wind_actuals_start_time", "start_time"),
    )


class WindForecast(Base):
    __tablename__ = "wind_forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    publish_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    generation_mw: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="WINDFOR")
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("start_time", "publish_time", name="uq_wind_forecasts_revision"),
        Index("ix_wind_forecasts_start_time", "start_time"),
        Index("ix_wind_forecasts_publish_time", "publish_time"),
        Index("ix_wind_forecasts_start_publish", "start_time", "publish_time"),
    )


class ImportRun(Base):
    __tablename__ = "import_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    records_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

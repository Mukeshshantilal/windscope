from functools import lru_cache
from datetime import date
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Decision cutoff values are documented assumptions."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "WindScope"
    database_url: str = "postgresql+psycopg2://windscope:windscope@localhost:5434/windscope"
    frontend_dist: str = ""
    cors_origins: str = (
        "http://localhost:5174,http://localhost:4173,http://localhost:8088,"
        "http://localhost:80,http://localhost"
    )

    @field_validator("database_url")
    @classmethod
    def sqlalchemy_database_url(cls, value: str) -> str:
        """Accept postgres:// and postgresql:// from managed hosts."""
        url = value
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://") :]
        if url.startswith("postgresql://") and "+" not in url.split("://", 1)[0]:
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url

    elexon_base_url: str = "https://data.elexon.co.uk/bmrs/api/v1"
    elexon_timeout_seconds: float = 60.0
    elexon_max_retries: int = 5
    elexon_retry_backoff_seconds: float = 1.5

    # ASSUMPTION: GB day-ahead purchasing cutoff.
    # Nord Pool N2EX GB day-ahead auction gate closure is 09:50 UK time.
    # This is used as a configurable proxy for "forecasts available when
    # the purchasing decision was made". It is not a confirmed internal
    # trading-desk rule for any specific utility.
    decision_cutoff_hour: int = 9
    decision_cutoff_minute: int = 50
    decision_cutoff_timezone: str = "Europe/London"
    display_timezone: str = "Europe/London"

    mape_min_actual_mw: float = 1.0

    supported_delivery_start: date = date(2026, 1, 1)
    supported_delivery_end: date = date(2026, 2, 1)
    import_actuals_start: date = date(2026, 1, 1)
    import_actuals_end: date = date(2026, 2, 1)
    import_forecast_publish_start: date = date(2025, 12, 30)
    import_forecast_publish_end: date = date(2026, 2, 1)

    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    def frontend_dist_path(self) -> Path | None:
        if not self.frontend_dist:
            return None
        path = Path(self.frontend_dist)
        return path if path.is_dir() else None


@lru_cache
def get_settings() -> Settings:
    return Settings()

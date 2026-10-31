from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

UTC = ZoneInfo("UTC")


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def parse_elexon_datetime(value: str) -> datetime:
    return ensure_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))


def decision_cutoff_utc(
    start_time: datetime,
    *,
    cutoff_hour: int,
    cutoff_minute: int,
    timezone_name: str,
) -> datetime:
    """Return the decision cutoff for a delivery period start time.

    Assumption: the purchasing decision for a UK local delivery date is made
    on the previous UK local calendar day at the configured clock time.
    Forecasts published after this instant are not eligible.
    """
    start_time = ensure_utc(start_time)
    tz = ZoneInfo(timezone_name)
    local = start_time.astimezone(tz)
    decision_date = local.date() - timedelta(days=1)
    local_cutoff = datetime.combine(
        decision_date,
        time(cutoff_hour, cutoff_minute),
        tzinfo=tz,
    )
    return local_cutoff.astimezone(UTC)


def delivery_range_utc(from_date: date, to_date: date, timezone_name: str) -> tuple[datetime, datetime]:
    """Inclusive local delivery dates converted to a half-open UTC interval."""
    tz = ZoneInfo(timezone_name)
    start = datetime.combine(from_date, time.min, tzinfo=tz).astimezone(UTC)
    end = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=tz).astimezone(UTC)
    return start, end


def decision_dates_for_delivery(from_date: date, to_date: date) -> tuple[date, date]:
    """Purchasing-decision dates for an inclusive delivery-date window.

    Assumption: the decision for UK local delivery date D is made on D-1.
    """
    return from_date - timedelta(days=1), to_date - timedelta(days=1)


def hour_floor_utc(start_time: datetime) -> datetime:
    value = ensure_utc(start_time)
    return value.replace(minute=0, second=0, microsecond=0)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

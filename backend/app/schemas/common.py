from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

SelectionMode = Literal["decision_time", "latest_before_delivery"]
Granularity = Literal["daily", "hourly", "half_hourly"]


class DecisionCutoffInfo(BaseModel):
    hour: int
    minute: int
    timezone: str
    is_assumption: bool = True
    description: str = (
        "Default 09:50 Europe/London on the UK calendar day before delivery. "
        "Aligned with Nord Pool N2EX GB day-ahead auction gate closure as a "
        "proxy for purchasing-decision time. This is an assumption, not a "
        "confirmed internal market rule."
    )


class DateRangeInfo(BaseModel):
    from_date: date = Field(alias="from")
    to_date: date = Field(alias="to")
    timezone: str
    start_utc: datetime
    end_utc_exclusive: datetime

    model_config = {"populate_by_name": True}

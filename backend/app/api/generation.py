from datetime import date
from io import StringIO

import pandas as pd
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.api.deps import accuracy_service, parse_granularity, parse_mode, parse_range, range_payload, settings_dep
from app.core.config import Settings
from app.analytics.metrics import matched_rows
from app.schemas.common import Granularity, SelectionMode
from app.services.forecast_accuracy import ForecastAccuracyService

router = APIRouter()


@router.get("/generation/series")
def generation_series(
    date_range: tuple[date, date] = Depends(parse_range),
    mode: SelectionMode = Depends(parse_mode),
    granularity: Granularity = Depends(parse_granularity),
    settings: Settings = Depends(settings_dep),
    service: ForecastAccuracyService = Depends(accuracy_service),
) -> dict:
    from_date, to_date = date_range
    payload = service.series(from_date, to_date, mode=mode, granularity=granularity)
    return {
        "range": range_payload(from_date, to_date, settings),
        "selection_mode": mode,
        "granularity": granularity,
        "points": payload["points"],
        "matched_periods": payload["matched_periods"],
        "expected_periods": payload["expected_periods"],
        "period_unit": payload["period_unit"],
        "empty_reason": payload["empty_reason"],
    }


@router.get("/generation/table")
def generation_table(
    date_range: tuple[date, date] = Depends(parse_range),
    mode: SelectionMode = Depends(parse_mode),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    sort: str = Query(default="start_time"),
    direction: str = Query(default="asc"),
    service: ForecastAccuracyService = Depends(accuracy_service),
) -> dict:
    from_date, to_date = date_range
    frame, _, _ = service.matched_frame(from_date, to_date, mode=mode)
    if frame.empty:
        return {"items": [], "total": 0, "page": page, "page_size": page_size}

    allowed = {
        "start_time",
        "actual_mw",
        "forecast_mw",
        "error_mw",
        "abs_error_mw",
        "pct_error",
        "forecast_publish_time",
    }
    sort_key = sort if sort in allowed else "start_time"
    working = frame.copy()
    working = working.sort_values(sort_key, ascending=direction != "desc", na_position="last")
    total = int(len(working))
    start_idx = (page - 1) * page_size
    page_df = working.iloc[start_idx : start_idx + page_size]
    items = []
    for row in page_df.itertuples(index=False):
        items.append(
            {
                "start_time": row.start_time,
                "decision_cutoff": row.cutoff if hasattr(row, "cutoff") else None,
                "forecast_publish_time": row.forecast_publish_time,
                "forecast_mw": None if pd.isna(row.forecast_mw) else float(row.forecast_mw),
                "actual_mw": None if pd.isna(row.actual_mw) else float(row.actual_mw),
                "error_mw": None if pd.isna(row.error_mw) else float(row.error_mw),
                "abs_error_mw": None if pd.isna(row.abs_error_mw) else float(row.abs_error_mw),
                "pct_error": None if pd.isna(row.pct_error) else float(row.pct_error),
            }
        )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/generation/export")
def generation_export(
    date_range: tuple[date, date] = Depends(parse_range),
    mode: SelectionMode = Depends(parse_mode),
    service: ForecastAccuracyService = Depends(accuracy_service),
) -> StreamingResponse:
    from_date, to_date = date_range
    frame, _, _ = service.matched_frame(from_date, to_date, mode=mode)
    export = matched_rows(frame) if not frame.empty else frame
    columns = [
        "start_time",
        "cutoff",
        "forecast_publish_time",
        "forecast_mw",
        "actual_mw",
        "error_mw",
        "abs_error_mw",
        "pct_error",
    ]
    buffer = StringIO()
    if export.empty:
        pd.DataFrame(columns=columns).to_csv(buffer, index=False)
    else:
        export[columns].to_csv(buffer, index=False)
    buffer.seek(0)
    filename = f"windscope-generation-{from_date.isoformat()}-to-{to_date.isoformat()}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

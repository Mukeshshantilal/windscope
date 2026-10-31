from datetime import date

from app.analytics.matching import (
    actuals_frame,
    cutoff_for_start,
    expected_hours,
    forecasts_frame,
    match_actuals_to_forecasts,
    select_forecasts,
)
from app.core.timeutils import decision_cutoff_utc, delivery_range_utc
from tests.conftest import utc


def test_cutoff_is_previous_uk_day_at_configured_clock() -> None:
    start = utc(2026, 1, 2, 0, 0)
    cutoff = decision_cutoff_utc(
        start,
        cutoff_hour=9,
        cutoff_minute=50,
        timezone_name="Europe/London",
    )
    assert cutoff == utc(2026, 1, 1, 9, 50)


def test_excludes_forecasts_published_after_cutoff() -> None:
    forecasts = forecasts_frame(
        [
            {"start_time": utc(2026, 1, 2, 0), "publish_time": utc(2026, 1, 1, 8, 30), "generation_mw": 1200},
            {"start_time": utc(2026, 1, 2, 0), "publish_time": utc(2026, 1, 1, 10, 30), "generation_mw": 900},
        ]
    )
    selected = select_forecasts(
        forecasts,
        mode="decision_time",
        cutoff_hour=9,
        cutoff_minute=50,
        timezone_name="Europe/London",
    )
    assert len(selected) == 1
    assert selected.iloc[0]["generation_mw"] == 1200
    assert selected.iloc[0]["publish_time"].to_pydatetime() == utc(2026, 1, 1, 8, 30)


def test_multiple_revisions_keep_latest_eligible() -> None:
    forecasts = forecasts_frame(
        [
            {"start_time": utc(2026, 1, 2, 0), "publish_time": utc(2026, 1, 1, 3, 30), "generation_mw": 1800},
            {"start_time": utc(2026, 1, 2, 0), "publish_time": utc(2026, 1, 1, 5, 30), "generation_mw": 1500},
            {"start_time": utc(2026, 1, 2, 0), "publish_time": utc(2026, 1, 1, 8, 30), "generation_mw": 1200},
            {"start_time": utc(2026, 1, 2, 0), "publish_time": utc(2026, 1, 1, 10, 30), "generation_mw": 900},
        ]
    )
    selected = select_forecasts(
        forecasts,
        mode="decision_time",
        cutoff_hour=9,
        cutoff_minute=50,
        timezone_name="Europe/London",
    )
    assert selected.iloc[0]["generation_mw"] == 1200


def test_missing_eligible_forecast_omits_target() -> None:
    forecasts = forecasts_frame(
        [
            {"start_time": utc(2026, 1, 2, 0), "publish_time": utc(2026, 1, 1, 10, 30), "generation_mw": 900},
        ]
    )
    selected = select_forecasts(
        forecasts,
        mode="decision_time",
        cutoff_hour=9,
        cutoff_minute=50,
        timezone_name="Europe/London",
    )
    assert selected.empty


def test_duplicate_revisions_are_collapsed() -> None:
    forecasts = forecasts_frame(
        [
            {"start_time": utc(2026, 1, 2, 0), "publish_time": utc(2026, 1, 1, 8, 30), "generation_mw": 1200},
            {"start_time": utc(2026, 1, 2, 0), "publish_time": utc(2026, 1, 1, 8, 30), "generation_mw": 9999},
        ]
    )
    selected = select_forecasts(
        forecasts,
        mode="decision_time",
        cutoff_hour=9,
        cutoff_minute=50,
        timezone_name="Europe/London",
    )
    assert len(selected) == 1
    assert selected.iloc[0]["generation_mw"] == 1200


def test_latest_before_delivery_can_use_later_revision() -> None:
    forecasts = forecasts_frame(
        [
            {"start_time": utc(2026, 1, 2, 12), "publish_time": utc(2026, 1, 1, 8, 30), "generation_mw": 1200},
            {"start_time": utc(2026, 1, 2, 12), "publish_time": utc(2026, 1, 2, 8, 30), "generation_mw": 800},
        ]
    )
    selected = select_forecasts(
        forecasts,
        mode="latest_before_delivery",
        cutoff_hour=9,
        cutoff_minute=50,
        timezone_name="Europe/London",
    )
    assert selected.iloc[0]["generation_mw"] == 800


def test_matching_uses_hourly_mean_actual_not_duplicated_forecast() -> None:
    actuals = actuals_frame(
        [
            {"start_time": utc(2026, 1, 2, 0, 0), "generation_mw": 1000},
            {"start_time": utc(2026, 1, 2, 0, 30), "generation_mw": 1100},
        ]
    )
    forecasts = forecasts_frame(
        [
            {"start_time": utc(2026, 1, 2, 0, 0), "publish_time": utc(2026, 1, 1, 8, 30), "generation_mw": 1200},
        ]
    )
    selected = select_forecasts(
        forecasts,
        mode="decision_time",
        cutoff_hour=9,
        cutoff_minute=50,
        timezone_name="Europe/London",
    )
    matched = match_actuals_to_forecasts(actuals, selected)
    assert len(matched) == 1
    assert matched.iloc[0]["actual_mw"] == 1050.0
    assert matched.iloc[0]["forecast_mw"] == 1200.0
    assert matched.iloc[0]["error_mw"] == 150.0


def test_incomplete_hour_is_not_matched() -> None:
    actuals = actuals_frame(
        [
            {"start_time": utc(2026, 1, 2, 0, 0), "generation_mw": 1000},
        ]
    )
    forecasts = forecasts_frame(
        [
            {"start_time": utc(2026, 1, 2, 0, 0), "publish_time": utc(2026, 1, 1, 8, 30), "generation_mw": 1200},
        ]
    )
    selected = select_forecasts(
        forecasts,
        mode="decision_time",
        cutoff_hour=9,
        cutoff_minute=50,
        timezone_name="Europe/London",
    )
    matched = match_actuals_to_forecasts(actuals, selected)
    assert matched.empty


def test_date_boundary_january_first_uses_december_cutoff() -> None:
    cutoff = cutoff_for_start(
        utc(2026, 1, 1, 0, 0),
        mode="decision_time",
        cutoff_hour=9,
        cutoff_minute=50,
        timezone_name="Europe/London",
    )
    assert cutoff == utc(2025, 12, 31, 9, 50)


def test_expected_hours_are_consistent_for_the_same_delivery_window() -> None:
    start, end = delivery_range_utc(date(2026, 1, 1), date(2026, 1, 31), "Europe/London")
    wider_start, wider_end = delivery_range_utc(date(2026, 1, 1), date(2026, 2, 1), "Europe/London")
    assert len(expected_hours(start, end)) == 31 * 24
    assert len(expected_hours(wider_start, wider_end)) == 32 * 24


def test_february_first_uses_january_31_cutoff() -> None:
    cutoff = cutoff_for_start(
        utc(2026, 2, 1, 23, 30),
        mode="decision_time",
        cutoff_hour=9,
        cutoff_minute=50,
        timezone_name="Europe/London",
    )
    assert cutoff == utc(2026, 1, 31, 9, 50)

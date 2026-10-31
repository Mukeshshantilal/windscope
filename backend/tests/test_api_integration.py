from tests.conftest import seed_decision_example


def test_accuracy_metrics_use_decision_time_forecast(client, db) -> None:
    seed_decision_example(db)

    response = client.get(
        "/api/accuracy/metrics",
        params={"from": "2026-01-02", "to": "2026-01-02", "selection": "decision_time"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["sample_count"] == 1
    assert payload["mae_mw"] == 150.0
    assert payload["bias_mw"] == 150.0
    assert payload["average_forecast_mw"] == 1200.0
    assert payload["average_actual_mw"] == 1050.0
    assert payload["period_unit"] == "hour"


def test_future_published_forecast_does_not_leak_into_dashboard(client, db) -> None:
    seed_decision_example(db)
    summary = client.get(
        "/api/dashboard/summary",
        params={"from": "2026-01-02", "to": "2026-01-02", "selection": "decision_time"},
    )
    assert summary.status_code == 200
    assert summary.json()["kpis"]["average_forecast_mw"] == 1200.0

    revisions = client.get(
        "/api/forecasts/revisions",
        params={"start_time": "2026-01-02T00:00:00Z", "selection": "decision_time"},
    )
    assert revisions.status_code == 200
    body = revisions.json()
    selected = body["selected"]
    assert selected["generation_mw"] == 1200
    after_cutoff = [row for row in body["revisions"] if row["generation_mw"] == 900][0]
    assert after_cutoff["eligible_at_decision"] is False
    assert after_cutoff["selected"] is False


def test_health_endpoint(client) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert body["warehouse"]["imported"] is False
    assert body["warehouse"]["actual_records"] == 0


def test_quality_uses_the_same_expected_hours_as_overview(client, db) -> None:
    seed_decision_example(db)
    params = {"from": "2026-01-02", "to": "2026-01-02", "selection": "decision_time"}
    summary = client.get("/api/dashboard/summary", params=params)
    quality = client.get("/api/data/quality", params=params)
    assert summary.status_code == 200
    assert quality.status_code == 200
    assert summary.json()["kpis"]["expected_periods"] == quality.json()["expected_periods"] == 24
    assert summary.json()["kpis"]["matched_periods"] == quality.json()["matched_delivery_periods"] == 1

from __future__ import annotations

import logging
import time
from datetime import date, datetime
from typing import Any

import httpx

from app.core.config import Settings
from app.core.timeutils import UTC

logger = logging.getLogger(__name__)


class ElexonAPIError(RuntimeError):
    """Raised when the Elexon BMRS API cannot be used as a data source."""


class ElexonAPIClient:
    """HTTP client for Elexon BMRS dataset stream endpoints."""

    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self.settings = settings
        self._own_client = client is None
        self.client = client or httpx.Client(timeout=settings.elexon_timeout_seconds)

    def close(self) -> None:
        if self._own_client:
            self.client.close()

    def __enter__(self) -> ElexonAPIClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def fetch_fuelhh_wind(self, settlement_from: date, settlement_to: date) -> list[dict[str, Any]]:
        params = {
            "settlementDateFrom": settlement_from.isoformat(),
            "settlementDateTo": settlement_to.isoformat(),
            "fuelType": "WIND",
        }
        rows = self._get_json("/datasets/FUELHH/stream", params)
        return [row for row in rows if str(row.get("fuelType", "")).upper() == "WIND"]

    def fetch_windfor(self, publish_from: datetime, publish_to: datetime) -> list[dict[str, Any]]:
        params = {
            "publishDateTimeFrom": _rfc3339(publish_from),
            "publishDateTimeTo": _rfc3339(publish_to),
        }
        return self._get_json("/datasets/WINDFOR/stream", params)

    def _get_json(self, path: str, params: dict[str, str]) -> list[dict[str, Any]]:
        url = f"{self.settings.elexon_base_url.rstrip('/')}{path}"
        retries = self.settings.elexon_max_retries
        backoff = self.settings.elexon_retry_backoff_seconds
        last_error: Exception | None = None

        for attempt in range(1, retries + 1):
            try:
                response = self.client.get(
                    url,
                    params=params,
                    headers={"Accept": "application/json"},
                )
                logger.info(
                    "Elexon GET %s status=%s attempt=%s/%s",
                    response.url,
                    response.status_code,
                    attempt,
                    retries,
                )
                if response.status_code == 429 or response.status_code >= 500:
                    last_error = ElexonAPIError(
                        f"Elexon {path} returned HTTP {response.status_code}: {response.text[:400]}"
                    )
                    logger.warning("%s", last_error)
                    time.sleep(backoff * attempt)
                    continue
                if response.status_code >= 400:
                    detail = response.text[:800]
                    raise ElexonAPIError(
                        f"Elexon {path} returned HTTP {response.status_code}: {detail}"
                    )
                payload = _parse_payload(response)
                logger.info("Elexon %s returned %s records", path, len(payload))
                time.sleep(0.15)
                return payload
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = ElexonAPIError(f"Elexon {path} network error: {exc}")
                logger.warning("Elexon %s network error (attempt %s/%s): %s", path, attempt, retries, exc)
                time.sleep(backoff * attempt)

        if last_error:
            raise last_error
        raise ElexonAPIError(f"Elexon {path} failed without a response")


def _parse_payload(response: httpx.Response) -> list[dict[str, Any]]:
    try:
        payload = response.json()
    except ValueError as exc:
        snippet = response.text[:400]
        raise ElexonAPIError(f"Elexon returned non-JSON body: {snippet}") from exc

    if payload is None:
        raise ElexonAPIError("Elexon returned an empty JSON document")
    if isinstance(payload, dict) and "data" in payload:
        data = payload["data"]
        if not isinstance(data, list):
            raise ElexonAPIError(f"Elexon data field was {type(data).__name__}, expected list")
        return data
    if isinstance(payload, list):
        return payload
    raise ElexonAPIError(f"Unexpected Elexon payload type: {type(payload).__name__}")


def _rfc3339(value: datetime) -> str:
    aware = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    return aware.strftime("%Y-%m-%dT%H:%M:%SZ")

"""Minimal aprs.fi API authentication check."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from aiohttp import ClientError, ClientSession

from .const import API_URL, VERSION


class AprsFiError(Exception):
    """The aprs.fi request failed."""


class AprsFiAuthenticationError(AprsFiError):
    """The aprs.fi API key was rejected."""


class AprsFiRateLimitError(AprsFiError):
    """The aprs.fi API rate limit was reached."""

    def __init__(self, retry_after_seconds: int | None = None) -> None:
        self.retry_after_seconds = retry_after_seconds
        detail = (
            f"; retry after {retry_after_seconds} seconds"
            if retry_after_seconds is not None
            else ""
        )
        super().__init__(f"HTTP 429{detail}")


@dataclass(frozen=True)
class Position:
    """Normalized location returned by aprs.fi."""

    callsign: str
    latitude: float
    longitude: float
    last_seen: datetime
    course: float | None = None
    speed_kmh: float | None = None
    altitude_m: float | None = None
    symbol: str | None = None
    comment: str | None = None


def position_age_minutes(position: Position, now: datetime | None = None) -> int:
    """Return the non-negative age of a position in whole minutes."""
    current_time = now or datetime.now(UTC)
    return max(0, int((current_time - position.last_seen).total_seconds() // 60))


def is_position_stale(
    position: Position,
    max_age_minutes: int,
    now: datetime | None = None,
) -> bool:
    """Return whether a position is older than the configured limit."""
    current_time = now or datetime.now(UTC)
    return current_time - position.last_seen > timedelta(minutes=max_age_minutes)


def position_status(
    position: Position | None,
    max_age_minutes: int,
    now: datetime | None = None,
) -> str:
    """Return a stable translated state key for station freshness."""
    if position is None:
        return "no_position"
    if is_position_stale(position, max_age_minutes, now):
        return "stale"
    return "current"


async def async_validate_api(
    session: ClientSession,
    api_key: str,
    callsigns: tuple[str, ...],
) -> None:
    """Verify the API key with a location query."""
    await async_get_positions(session, api_key, callsigns)


async def async_get_positions(
    session: ClientSession,
    api_key: str,
    callsigns: tuple[str, ...],
) -> dict[str, Position]:
    """Return the latest valid positions for the requested callsigns."""
    params = {
        "name": ",".join(callsigns),
        "what": "loc",
        "apikey": api_key,
        "format": "json",
    }
    headers = {"User-Agent": f"APRSMonitor/{VERSION} (+https://github.com/DjangoToni/aprs-tracker)"}
    try:
        async with asyncio.timeout(10):
            async with session.get(API_URL, params=params, headers=headers) as response:
                if response.status in (401, 403):
                    raise AprsFiAuthenticationError(f"HTTP {response.status}")
                if response.status == 429:
                    raise AprsFiRateLimitError(
                        parse_retry_after(response.headers.get("Retry-After"))
                    )
                if response.status != 200:
                    raise AprsFiError(f"HTTP {response.status}")
                payload: dict[str, Any] = await response.json(content_type=None)
    except AprsFiAuthenticationError:
        raise
    except (ClientError, TimeoutError, ValueError) as err:
        raise AprsFiError(str(err)) from err

    validate_api_response(payload)
    return parse_positions(payload)


def validate_api_response(payload: dict[str, Any]) -> None:
    """Classify an aprs.fi JSON response."""
    if payload.get("result") == "ok":
        return

    description = str(payload.get("description", "Unknown aprs.fi error"))
    lowered = description.lower()
    if "auth" in lowered or "api key" in lowered or "apikey" in lowered:
        raise AprsFiAuthenticationError(description)
    raise AprsFiError(description)


def parse_positions(payload: dict[str, Any]) -> dict[str, Position]:
    """Parse location entries and ignore malformed positions."""
    positions: dict[str, Position] = {}
    entries = payload.get("entries", [])
    if not isinstance(entries, list):
        return positions

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        try:
            callsign = str(entry["name"]).upper()
            latitude = float(entry["lat"])
            longitude = float(entry["lng"])
            timestamp = int(entry.get("lasttime", entry.get("time")))
        except (KeyError, TypeError, ValueError):
            continue
        if not callsign or abs(latitude) > 90 or abs(longitude) > 180:
            continue

        positions[callsign] = Position(
            callsign=callsign,
            latitude=latitude,
            longitude=longitude,
            last_seen=datetime.fromtimestamp(timestamp, UTC),
            course=_optional_float(entry.get("course")),
            speed_kmh=_optional_float(entry.get("speed")),
            altitude_m=_optional_float(entry.get("altitude")),
            symbol=_optional_text(entry.get("symbol")),
            comment=_optional_text(entry.get("comment")),
        )
    return positions


def _optional_float(value: Any) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _optional_text(value: Any) -> str | None:
    return str(value) if value not in (None, "") else None


def parse_retry_after(value: object) -> int | None:
    """Parse a non-negative Retry-After delay in seconds."""
    try:
        seconds = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return seconds if seconds >= 0 else None

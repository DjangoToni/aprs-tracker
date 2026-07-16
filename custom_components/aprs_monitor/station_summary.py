"""Aggregate station health without exposing station identifiers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .api import Position, position_status


@dataclass(frozen=True)
class StationSummary:
    """Aggregate freshness counts and overall integration status."""

    status: str
    current: int
    stale: int
    missing: int


def build_station_summary(
    callsigns: Sequence[str],
    positions: Mapping[str, Position],
    max_position_age: int | Mapping[str, int],
    api_connected: bool,
) -> StationSummary:
    """Return aggregate station state for dashboards and automations."""
    counts = {"current": 0, "stale": 0, "no_position": 0}
    for callsign in callsigns:
        age_limit = (
            max_position_age[callsign]
            if isinstance(max_position_age, Mapping)
            else max_position_age
        )
        counts[position_status(positions.get(callsign), age_limit)] += 1

    if not api_connected or counts["current"] == 0:
        status = "error"
    elif counts["current"] == len(callsigns):
        status = "ok"
    else:
        status = "degraded"
    return StationSummary(
        status,
        counts["current"],
        counts["stale"],
        counts["no_position"],
    )

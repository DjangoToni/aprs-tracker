"""Privacy-preserving diagnostics data helpers for APRS Monitor."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from .api import Position, is_position_stale, position_age_minutes


def build_station_diagnostics(
    callsigns: Sequence[str],
    positions: Mapping[str, Position],
    max_position_age: int | Mapping[str, int],
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Return anonymized station diagnostics without location or packet data."""
    diagnostics: list[dict[str, Any]] = []
    for index, callsign in enumerate(callsigns, start=1):
        position = positions.get(callsign)
        station: dict[str, Any] = {
            "station": f"station_{index}",
            "has_position": position is not None,
        }
        if position is not None:
            age_limit = (
                max_position_age[callsign]
                if isinstance(max_position_age, Mapping)
                else max_position_age
            )
            station.update(
                {
                    "position_age_minutes": position_age_minutes(position, now),
                    "position_stale": is_position_stale(
                        position,
                        age_limit,
                        now,
                    ),
                    "fields_present": {
                        "course": position.course is not None,
                        "speed": position.speed_kmh is not None,
                        "altitude": position.altitude_m is not None,
                        "symbol": position.symbol is not None,
                        "comment": position.comment is not None,
                    },
                }
            )
        diagnostics.append(station)
    return diagnostics

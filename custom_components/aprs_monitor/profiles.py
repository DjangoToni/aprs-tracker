"""Normalized per-station APRS Monitor profiles."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .const import (
    CONF_DISPLAY_NAME,
    CONF_HOME_RADIUS,
    CONF_MAX_POSITION_AGE,
    CONF_MOVEMENT_SPEED_THRESHOLD,
)
from .validation import (
    normalize_home_radius,
    normalize_max_position_age,
    normalize_movement_speed_threshold,
)


@dataclass(frozen=True)
class StationProfile:
    """Effective display and threshold settings for one callsign."""

    display_name: str
    max_position_age: int
    home_radius_km: float
    movement_speed_threshold_kmh: float


def build_station_profiles(
    callsigns: Sequence[str],
    raw_profiles: Mapping[str, Any],
    default_max_position_age: int,
    default_home_radius: float,
    default_movement_speed_threshold: float,
) -> dict[str, StationProfile]:
    """Normalize stored profiles and safely fall back to global defaults."""
    profiles: dict[str, StationProfile] = {}
    for callsign in callsigns:
        raw = raw_profiles.get(callsign, {})
        if not isinstance(raw, Mapping):
            raw = {}
        display_name = str(raw.get(CONF_DISPLAY_NAME, "")).strip()[:64] or callsign
        profiles[callsign] = StationProfile(
            display_name=display_name,
            max_position_age=(
                normalize_max_position_age(raw.get(CONF_MAX_POSITION_AGE))
                or default_max_position_age
            ),
            home_radius_km=(
                normalize_home_radius(raw.get(CONF_HOME_RADIUS)) or default_home_radius
            ),
            movement_speed_threshold_kmh=(
                normalize_movement_speed_threshold(
                    raw.get(CONF_MOVEMENT_SPEED_THRESHOLD)
                )
                or default_movement_speed_threshold
            ),
        )
    return profiles

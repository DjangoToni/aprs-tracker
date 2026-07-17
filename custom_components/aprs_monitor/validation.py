"""Pure input validation for APRS Monitor."""

from __future__ import annotations

import re

from .const import (
    MAX_CALLSIGNS,
    MAX_HOME_RADIUS,
    MAX_MAX_POSITION_AGE,
    MAX_MOVEMENT_SPEED_THRESHOLD,
    MAX_UPDATE_INTERVAL,
    MIN_HOME_RADIUS,
    MIN_MAX_POSITION_AGE,
    MIN_MOVEMENT_SPEED_THRESHOLD,
    MIN_UPDATE_INTERVAL,
)

_CALLSIGN_RE = re.compile(r"^[A-Z0-9]{1,6}(?:-(?:[0-9]|1[0-5]))?$", re.IGNORECASE)


def normalize_callsigns(value: object) -> tuple[str, ...]:
    """Normalize 1–20 exact callsigns or return an empty tuple on error."""
    if isinstance(value, str):
        raw_value = value
    elif isinstance(value, (list, tuple)) and all(isinstance(item, str) for item in value):
        raw_value = ",".join(value)
    else:
        return ()
    callsigns = tuple(
        dict.fromkeys(
            part.strip().upper() for part in raw_value.replace("\n", ",").split(",") if part.strip()
        )
    )
    if (
        not callsigns
        or len(callsigns) > MAX_CALLSIGNS
        or any(_CALLSIGN_RE.fullmatch(callsign) is None for callsign in callsigns)
    ):
        return ()
    return callsigns


def normalize_update_interval(value: object) -> int | None:
    """Return a valid polling interval in minutes or None."""
    try:
        interval = int(value)
    except (TypeError, ValueError):
        return None
    if MIN_UPDATE_INTERVAL <= interval <= MAX_UPDATE_INTERVAL:
        return interval
    return None


def normalize_max_position_age(value: object) -> int | None:
    """Return a valid maximum position age in minutes or None."""
    try:
        max_age = int(value)
    except (TypeError, ValueError):
        return None
    if MIN_MAX_POSITION_AGE <= max_age <= MAX_MAX_POSITION_AGE:
        return max_age
    return None


def normalize_home_radius(value: object) -> float | None:
    """Return a valid home proximity radius in kilometers or None."""
    try:
        radius = float(value)
    except (TypeError, ValueError):
        return None
    if MIN_HOME_RADIUS <= radius <= MAX_HOME_RADIUS:
        return round(radius, 2)
    return None


def normalize_movement_speed_threshold(value: object) -> float | None:
    """Return a valid movement threshold in kilometers per hour or None."""
    try:
        threshold = float(value)
    except (TypeError, ValueError):
        return None
    if MIN_MOVEMENT_SPEED_THRESHOLD <= threshold <= MAX_MOVEMENT_SPEED_THRESHOLD:
        return round(threshold, 2)
    return None

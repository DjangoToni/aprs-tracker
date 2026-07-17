"""Config-entry option migration for APRS Monitor."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .const import (
    CONF_CALLSIGNS,
    CONF_DISPLAY_NAME,
    CONF_HOME_RADIUS,
    CONF_MAP_MARKER_STYLE,
    CONF_MAX_POSITION_AGE,
    CONF_MOVEMENT_SPEED_THRESHOLD,
    CONF_STATION_PROFILES,
    CONF_UPDATE_INTERVAL,
    DEFAULT_HOME_RADIUS,
    DEFAULT_MAP_MARKER_STYLE,
    DEFAULT_MAX_POSITION_AGE,
    DEFAULT_MOVEMENT_SPEED_THRESHOLD,
    DEFAULT_UPDATE_INTERVAL,
    MAP_MARKER_STYLES,
)
from .profiles import build_station_profiles
from .validation import (
    normalize_callsigns,
    normalize_home_radius,
    normalize_max_position_age,
    normalize_movement_speed_threshold,
    normalize_update_interval,
)


def normalized_runtime_options(
    entry_data: Mapping[str, Any],
    entry_options: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return safe options while preserving unknown future option keys."""
    options = dict(entry_options) if isinstance(entry_options, Mapping) else {}
    callsigns = normalize_callsigns(options.get(CONF_CALLSIGNS))
    if not callsigns:
        callsigns = normalize_callsigns(entry_data.get(CONF_CALLSIGNS))
    if not callsigns:
        callsigns = ()

    update_interval = (
        normalize_update_interval(options.get(CONF_UPDATE_INTERVAL)) or DEFAULT_UPDATE_INTERVAL
    )
    max_position_age = (
        normalize_max_position_age(options.get(CONF_MAX_POSITION_AGE)) or DEFAULT_MAX_POSITION_AGE
    )
    home_radius = normalize_home_radius(options.get(CONF_HOME_RADIUS)) or DEFAULT_HOME_RADIUS
    movement_threshold = (
        normalize_movement_speed_threshold(options.get(CONF_MOVEMENT_SPEED_THRESHOLD))
        or DEFAULT_MOVEMENT_SPEED_THRESHOLD
    )
    map_marker_style = options.get(CONF_MAP_MARKER_STYLE)
    if map_marker_style not in MAP_MARKER_STYLES:
        map_marker_style = DEFAULT_MAP_MARKER_STYLE
    raw_profiles = options.get(CONF_STATION_PROFILES)
    if not isinstance(raw_profiles, Mapping):
        raw_profiles = {}
    profiles = build_station_profiles(
        callsigns,
        raw_profiles,
        max_position_age,
        home_radius,
        movement_threshold,
    )
    options.update(
        {
            CONF_CALLSIGNS: list(callsigns),
            CONF_UPDATE_INTERVAL: update_interval,
            CONF_MAX_POSITION_AGE: max_position_age,
            CONF_HOME_RADIUS: home_radius,
            CONF_MOVEMENT_SPEED_THRESHOLD: movement_threshold,
            CONF_MAP_MARKER_STYLE: map_marker_style,
            CONF_STATION_PROFILES: {
                callsign: {
                    CONF_DISPLAY_NAME: profile.display_name,
                    CONF_MAX_POSITION_AGE: profile.max_position_age,
                    CONF_HOME_RADIUS: profile.home_radius_km,
                    CONF_MOVEMENT_SPEED_THRESHOLD: (profile.movement_speed_threshold_kmh),
                }
                for callsign, profile in profiles.items()
            },
        }
    )
    return options

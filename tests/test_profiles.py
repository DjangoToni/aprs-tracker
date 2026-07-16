"""Tests for per-station profile normalization."""

from custom_components.aprs_monitor.const import (
    CONF_DISPLAY_NAME,
    CONF_HOME_RADIUS,
    CONF_MAX_POSITION_AGE,
    CONF_MOVEMENT_SPEED_THRESHOLD,
)
from custom_components.aprs_monitor.profiles import build_station_profiles


def test_profiles_inherit_global_defaults_and_normalize_name() -> None:
    profiles = build_station_profiles(("HB9ABC",), {}, 120, 25.0, 1.0)
    profile = profiles["HB9ABC"]
    assert profile.display_name == "HB9ABC"
    assert profile.max_position_age == 120
    assert profile.home_radius_km == 25.0
    assert profile.movement_speed_threshold_kmh == 1.0


def test_profiles_apply_individual_values_and_ignore_removed_callsigns() -> None:
    raw = {
        "HB9ABC": {
            CONF_DISPLAY_NAME: "  Einsatzfahrzeug  ",
            CONF_MAX_POSITION_AGE: 30,
            CONF_HOME_RADIUS: 5.5,
            CONF_MOVEMENT_SPEED_THRESHOLD: 3.0,
        },
        "HB9REMOVED": {CONF_DISPLAY_NAME: "Old"},
    }
    profiles = build_station_profiles(("HB9ABC",), raw, 120, 25.0, 1.0)
    assert set(profiles) == {"HB9ABC"}
    assert profiles["HB9ABC"].display_name == "Einsatzfahrzeug"
    assert profiles["HB9ABC"].max_position_age == 30
    assert profiles["HB9ABC"].home_radius_km == 5.5
    assert profiles["HB9ABC"].movement_speed_threshold_kmh == 3.0

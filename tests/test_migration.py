"""Tests for robust config-entry option migration."""

from custom_components.aprs_monitor.const import (
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
)
from custom_components.aprs_monitor.migration import normalized_runtime_options


def test_legacy_options_gain_complete_profiles_and_preserve_unknown_keys() -> None:
    options = normalized_runtime_options(
        {CONF_CALLSIGNS: ["HB9ABC", "HB9XYZ"]},
        {CONF_HOME_RADIUS: 50, "future_option": "keep"},
    )
    assert options["future_option"] == "keep"
    assert options[CONF_CALLSIGNS] == ["HB9ABC", "HB9XYZ"]
    assert options[CONF_MAP_MARKER_STYLE] == DEFAULT_MAP_MARKER_STYLE
    assert options[CONF_STATION_PROFILES]["HB9ABC"] == {
        CONF_DISPLAY_NAME: "HB9ABC",
        CONF_MAX_POSITION_AGE: DEFAULT_MAX_POSITION_AGE,
        CONF_HOME_RADIUS: 50.0,
        CONF_MOVEMENT_SPEED_THRESHOLD: DEFAULT_MOVEMENT_SPEED_THRESHOLD,
    }


def test_damaged_options_fall_back_to_data_and_valid_defaults() -> None:
    options = normalized_runtime_options(
        {CONF_CALLSIGNS: ["HB9SFE"]},
        {
            CONF_CALLSIGNS: 123,
            CONF_UPDATE_INTERVAL: "broken",
            CONF_MAX_POSITION_AGE: -1,
            CONF_HOME_RADIUS: None,
            CONF_MAP_MARKER_STYLE: "unsupported",
            CONF_MOVEMENT_SPEED_THRESHOLD: [],
            CONF_STATION_PROFILES: "not-a-dictionary",
        },
    )
    assert options[CONF_CALLSIGNS] == ["HB9SFE"]
    assert options[CONF_UPDATE_INTERVAL] == DEFAULT_UPDATE_INTERVAL
    assert options[CONF_MAX_POSITION_AGE] == DEFAULT_MAX_POSITION_AGE
    assert options[CONF_HOME_RADIUS] == DEFAULT_HOME_RADIUS
    assert options[CONF_MAP_MARKER_STYLE] == DEFAULT_MAP_MARKER_STYLE
    assert options[CONF_MOVEMENT_SPEED_THRESHOLD] == DEFAULT_MOVEMENT_SPEED_THRESHOLD
    assert set(options[CONF_STATION_PROFILES]) == {"HB9SFE"}

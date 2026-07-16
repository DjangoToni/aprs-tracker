"""Tests for APRS symbol translation."""

from custom_components.aprs_monitor.aprs_symbols import (
    DEFAULT_APRS_ICON,
    aprs_symbol_character,
    aprs_symbol_icon,
)


def test_maps_common_aprs_station_types() -> None:
    assert aprs_symbol_icon("/>") == "mdi:car"
    assert aprs_symbol_icon("\\b") == "mdi:bicycle"
    assert aprs_symbol_icon("/^" ) == "mdi:airplane"
    assert aprs_symbol_icon("/_") == "mdi:weather-partly-cloudy"
    assert aprs_symbol_icon("/s") == "mdi:ferry"


def test_unknown_or_missing_symbol_uses_safe_map_marker() -> None:
    assert aprs_symbol_icon("/~") == DEFAULT_APRS_ICON
    assert aprs_symbol_icon(None) == DEFAULT_APRS_ICON
    assert aprs_symbol_icon("  ") == DEFAULT_APRS_ICON


def test_extracts_station_type_without_changing_raw_symbol() -> None:
    assert aprs_symbol_character("/>") == ">"
    assert aprs_symbol_character("\\b") == "b"
    assert aprs_symbol_character(None) is None

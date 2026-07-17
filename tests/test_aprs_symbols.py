"""Tests for APRS symbol translation."""

from custom_components.aprs_monitor.aprs_symbols import (
    DEFAULT_APRS_ICON,
    aprs_symbol_character,
    aprs_symbol_icon,
    aprs_symbol_picture_url,
)


def test_maps_common_aprs_station_types() -> None:
    assert aprs_symbol_icon("/>") == "mdi:car"
    assert aprs_symbol_icon("\\b") == "mdi:bicycle"
    assert aprs_symbol_icon("/^") == "mdi:airplane"
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


def test_builds_local_picture_urls_for_printable_aprs_codes() -> None:
    assert aprs_symbol_picture_url("/>") == ("/api/aprs_monitor/symbol/2f-3e.png")
    assert aprs_symbol_picture_url("\\b") == ("/api/aprs_monitor/symbol/5c-62.png")
    assert aprs_symbol_picture_url(">") == ("/api/aprs_monitor/symbol/2f-3e.png")
    assert aprs_symbol_picture_url("/>", "safe token") == (
        "/api/aprs_monitor/symbol/2f-3e.png?token=safe%20token"
    )
    assert aprs_symbol_picture_url(None) is None
    assert aprs_symbol_picture_url("/\n") is None

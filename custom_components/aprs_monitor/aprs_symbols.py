"""Translate APRS symbols into Home Assistant map icons."""

from __future__ import annotations

DEFAULT_APRS_ICON = "mdi:map-marker"

# APRS normally uses a table character followed by a station-type character,
# for example ``/>`` for a car. The last character is sufficient for choosing
# a useful Home Assistant map icon without changing the original APRS value.
APRS_SYMBOL_ICONS: dict[str, str] = {
    "'": "mdi:airplane",
    "-": "mdi:home-map-marker",
    "<": "mdi:motorbike",
    ">": "mdi:car",
    "C": "mdi:kayaking",
    "O": "mdi:balloon",
    "R": "mdi:rv-truck",
    "S": "mdi:rocket-launch",
    "U": "mdi:bus",
    "W": "mdi:weather-partly-cloudy",
    "X": "mdi:helicopter",
    "Y": "mdi:sail-boat",
    "[": "mdi:run",
    "^": "mdi:airplane",
    "_": "mdi:weather-partly-cloudy",
    "a": "mdi:ambulance",
    "b": "mdi:bicycle",
    "e": "mdi:horse",
    "f": "mdi:fire-truck",
    "g": "mdi:airplane",
    "h": "mdi:hospital-building",
    "j": "mdi:jeepney",
    "k": "mdi:truck",
    "l": "mdi:laptop",
    "m": "mdi:radio-tower",
    "p": "mdi:dog",
    "r": "mdi:radio-tower",
    "s": "mdi:ferry",
    "u": "mdi:truck",
    "v": "mdi:van-passenger",
    "y": "mdi:home-map-marker",
}


def aprs_symbol_character(symbol: str | None) -> str | None:
    """Return the station-type character from an APRS symbol."""
    if symbol is None:
        return None
    normalized = symbol.strip()
    return normalized[-1] if normalized else None


def aprs_symbol_icon(symbol: str | None) -> str:
    """Return a safe MDI icon for an APRS symbol."""
    character = aprs_symbol_character(symbol)
    return APRS_SYMBOL_ICONS.get(character, DEFAULT_APRS_ICON)

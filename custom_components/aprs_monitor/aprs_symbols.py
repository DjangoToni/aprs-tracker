"""Translate APRS symbols into Home Assistant map icons."""

from __future__ import annotations

import re
from urllib.parse import quote

DEFAULT_APRS_ICON = "mdi:map-marker"
_SYMBOL_CODE = re.compile(r"^(?P<table>[2-7][0-9a-f])-(?P<symbol>[2-7][0-9a-f])$")

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


def aprs_symbol_picture_url(
    symbol: str | None,
    access_token: str | None = None,
) -> str | None:
    """Return a local picture URL encoding a safe printable APRS symbol."""
    if symbol is None or any(ord(value) < 32 or ord(value) > 126 for value in symbol):
        return None
    normalized = symbol.strip()
    if not normalized:
        return None
    table = normalized[0] if len(normalized) > 1 else "/"
    character = normalized[-1]
    if not all(32 <= ord(value) <= 126 for value in (table, character)):
        return None
    if table not in {"/", "\\"} and not table.isalnum():
        return None
    url = f"/api/aprs_monitor/symbol/{ord(table):02x}-{ord(character):02x}.png"
    if access_token is not None:
        return f"{url}?token={quote(access_token, safe='')}"
    return url


def decode_aprs_symbol_code(code: str) -> tuple[str, str] | None:
    """Decode a validated printable APRS table and symbol character pair."""
    match = _SYMBOL_CODE.fullmatch(code.lower())
    if match is None:
        return None
    table = chr(int(match.group("table"), 16))
    symbol = chr(int(match.group("symbol"), 16))
    if not 32 <= ord(table) <= 126 or not 33 <= ord(symbol) <= 126:
        return None
    if table not in {"/", "\\"} and not table.isalnum():
        return None
    return table, symbol

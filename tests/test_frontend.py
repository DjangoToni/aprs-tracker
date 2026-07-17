"""Static security and behavior checks for the APRS Monitor map card."""

from pathlib import Path

ROOT = Path(__file__).parents[1]
CARD = ROOT / "custom_components" / "aprs_monitor" / "frontend" / "aprs-monitor-map-card.js"


def test_map_card_uses_tracker_state_and_escapes_dynamic_html() -> None:
    source = CARD.read_text(encoding="utf-8")
    assert "this._hass.states[entityId]" in source
    assert "escapeHtml(picture)" in source
    assert "escapeHtml(name + callsign)" in source
    assert "escapeHtml(label)" in source
    assert "escapeHtml(value)" in source
    assert "callApi" not in source
    assert "aprs.fi" not in source


def test_map_card_has_local_assets_and_telemetry_tooltip() -> None:
    source = CARD.read_text(encoding="utf-8")
    assert 'new URL("vendor/leaflet/leaflet.js", FRONTEND_BASE)' in source
    assert 'new URL("vendor/leaflet/leaflet.css", FRONTEND_BASE)' in source
    assert "speed_kmh" in source
    assert "altitude_m" in source
    assert "coordinates" in source
    assert "last_seen" in source
    assert 'new CustomEvent("hass-more-info"' in source

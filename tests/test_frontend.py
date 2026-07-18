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


def test_map_card_reads_recorder_history_without_aprs_requests() -> None:
    source = CARD.read_text(encoding="utf-8")
    assert 'type: "history/history_during_period"' in source
    assert "this._hass.callWS" in source
    assert "significant_changes_only: false" in source
    assert "minimal_response: false" in source
    assert "no_attributes: false" in source
    assert "hours_to_show: 0" in source
    assert "max_history_points: 2000" in source
    assert "history_refresh_minutes: 15" in source


def test_map_card_visualizes_current_stale_and_unavailable_states() -> None:
    source = CARD.read_text(encoding="utf-8")
    assert 'return "current"' in source
    assert 'return "stale"' in source
    assert 'return "unavailable"' in source
    assert "status-current" in source
    assert "status-stale" in source
    assert "status-unavailable" in source
    assert "show_status: true" in source
    assert "usesHistoryFallback" in source

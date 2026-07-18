"""Static checks for dashboard and automation extras."""

from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_dashboard_uses_recorder_track_and_explicit_placeholders() -> None:
    dashboard = (ROOT / "examples" / "dashboard.yaml").read_text(encoding="utf-8")
    assert dashboard.count("hours_to_show: 24") == 2
    assert dashboard.count("- type: map") == 3
    assert "type: custom:aprs-monitor-map-card" in dashboard
    assert "scroll_wheel_zoom: true" in dashboard
    assert "history_refresh_minutes: 15" in dashboard
    assert "max_history_points: 2000" in dashboard
    assert "show_status: true" in dashboard
    assert 'color: "#039be5"' in dashboard
    assert "label_mode: icon" in dashboard
    assert "label_mode: state" in dashboard
    assert "attribute: map_details" in dashboard
    assert "cluster: false" in dashboard
    assert "fit_zones: true" in dashboard
    assert "device_tracker.REPLACE_WITH_FIRST_TRACKER" in dashboard
    assert "button.REPLACE_WITH_REFRESH" in dashboard
    assert "zone.REPLACE_WITH_FIRST_ZONE" in dashboard
    assert "event.REPLACE_WITH_FIRST_STATION_ACTIVITY" in dashboard


def test_blueprints_use_aprs_monitor_event_entities_and_action_selectors() -> None:
    blueprint_dir = ROOT / "blueprints" / "automation" / "aprs_monitor"
    station = (blueprint_dir / "station_activity_actions.yaml").read_text(encoding="utf-8")
    connection = (blueprint_dir / "api_connection_actions.yaml").read_text(encoding="utf-8")
    zone = (blueprint_dir / "zone_activity_actions.yaml").read_text(encoding="utf-8")
    assert "integration: aprs_monitor" in station
    assert "action: !input actions" in station
    assert "entered_zone" in station
    assert "left_zone" in station
    assert "api_unavailable" in connection
    assert "api_recovered" in connection
    assert "domain: zone" in zone
    assert "to: entered_zone" in zone
    assert "to: left_zone" in zone
    assert "zone_entity_id" in zone

"""Static checks for dashboard and automation extras."""

from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_dashboard_uses_recorder_track_and_explicit_placeholders() -> None:
    dashboard = (ROOT / "examples" / "dashboard.yaml").read_text(encoding="utf-8")
    assert "hours_to_show: 24" in dashboard
    assert "device_tracker.REPLACE_WITH_FIRST_TRACKER" in dashboard
    assert "button.REPLACE_WITH_REFRESH" in dashboard


def test_blueprints_use_aprs_monitor_event_entities_and_action_selectors() -> None:
    blueprint_dir = ROOT / "blueprints" / "automation" / "aprs_monitor"
    station = (blueprint_dir / "station_activity_actions.yaml").read_text(
        encoding="utf-8"
    )
    connection = (blueprint_dir / "api_connection_actions.yaml").read_text(
        encoding="utf-8"
    )
    assert "integration: aprs_monitor" in station
    assert "action: !input actions" in station
    assert "api_unavailable" in connection
    assert "api_recovered" in connection

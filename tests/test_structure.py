"""Static checks required for Home Assistant discovery."""

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
COMPONENT = ROOT / "custom_components" / "aprs_monitor"


def test_required_component_files_exist() -> None:
    for filename in (
        "__init__.py",
        "activity.py",
        "aprs_symbols.py",
        "binary_sensor.py",
        "button.py",
        "manifest.json",
        "migration.py",
        "profiles.py",
        "config_flow.py",
        "coordinator.py",
        "diagnostics.py",
        "diagnostics_data.py",
        "device_tracker.py",
        "event.py",
        "device_cleanup.py",
        "geo.py",
        "hub.py",
        "icons.json",
        "sensor.py",
        "station_summary.py",
        "strings.json",
        "system_health.py",
    ):
        assert (COMPONENT / filename).is_file()


def test_manifest_exposes_config_flow() -> None:
    manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["domain"] == "aprs_monitor"
    assert manifest["name"] == "APRS Monitor"
    assert manifest["config_flow"] is True
    assert manifest["version"] == "1.2.0"
    assert manifest["iot_class"] == "cloud_polling"
    assert manifest["integration_type"] == "hub"
    assert manifest["single_config_entry"] is True
    assert manifest["issue_tracker"].endswith("/issues")


def test_brand_icons_exist() -> None:
    """Ship the local brand assets required by HACS."""
    assert (COMPONENT / "brand" / "icon.png").is_file()
    assert (COMPONENT / "brand" / "icon@2x.png").is_file()


def test_platform_modules_are_preloaded_before_forwarding() -> None:
    init_source = (COMPONENT / "__init__.py").read_text(encoding="utf-8")
    assert "from . import binary_sensor as binary_sensor" in init_source
    assert "from . import button as button" in init_source
    assert "from . import device_tracker as device_tracker" in init_source
    assert "from . import event as event" in init_source
    assert "from . import sensor as sensor" in init_source


def test_course_sensor_uses_supported_degree_constant() -> None:
    sensor_source = (COMPONENT / "sensor.py").read_text(encoding="utf-8")
    assert "UnitOfAngle" not in sensor_source
    assert "native_unit=DEGREE" in sensor_source


def test_options_flow_uses_automatic_reload() -> None:
    flow_source = (COMPONENT / "config_flow.py").read_text(encoding="utf-8")
    assert "async_get_options_flow" in flow_source
    assert "class AprsMonitorOptionsFlow(config_entries.OptionsFlowWithReload)" in flow_source


def test_reauthentication_updates_existing_entry() -> None:
    flow_source = (COMPONENT / "config_flow.py").read_text(encoding="utf-8")
    assert "async_step_reauth" in flow_source
    assert "async_step_reauth_confirm" in flow_source
    assert "self._get_reauth_entry()" in flow_source
    assert "self.async_update_reload_and_abort(" in flow_source

    strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    assert "reauth_confirm" in strings["config"]["step"]
    assert "reauth_successful" in strings["config"]["abort"]


def test_diagnostics_redact_credentials_and_callsigns() -> None:
    source = (COMPONENT / "diagnostics.py").read_text(encoding="utf-8")
    assert "TO_REDACT = {CONF_API_KEY, CONF_CALLSIGNS, CONF_STATION_PROFILES}" in source
    assert "async_get_config_entry_diagnostics" in source


def test_position_current_binary_sensor_has_translations_and_icons() -> None:
    strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    icons = json.loads((COMPONENT / "icons.json").read_text(encoding="utf-8"))
    assert "position_current" in strings["entity"]["binary_sensor"]
    icon_config = icons["entity"]["binary_sensor"]["position_current"]
    assert icon_config["default"] == "mdi:map-marker-alert-outline"
    assert icon_config["state"]["on"] == "mdi:map-marker-check"
    assert "near_home" in strings["entity"]["binary_sensor"]
    near_home_icon = icons["entity"]["binary_sensor"]["near_home"]
    assert near_home_icon["state"]["on"] == "mdi:map-marker-radius"
    assert "moving" in strings["entity"]["binary_sensor"]
    moving_icon = icons["entity"]["binary_sensor"]["moving"]
    assert moving_icon["state"]["on"] == "mdi:motion-sensor"


def test_station_status_entities_have_translations_and_icons() -> None:
    strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    icons = json.loads((COMPONENT / "icons.json").read_text(encoding="utf-8"))
    sensors = strings["entity"]["sensor"]
    assert sensors["station_status"]["state"]["no_position"] == "No position"
    assert set(sensors["course_direction"]["state"]) == {
        "north",
        "northeast",
        "east",
        "southeast",
        "south",
        "southwest",
        "west",
        "northwest",
    }
    assert "position_age" in sensors
    assert "aprs_symbol" in sensors
    assert icons["entity"]["sensor"]["station_status"]["default"] == "mdi:list-status"


def test_station_activity_event_has_translations_and_icon() -> None:
    strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    icons = json.loads((COMPONENT / "icons.json").read_text(encoding="utf-8"))
    event = strings["entity"]["event"]["station_activity"]
    event_states = event["state_attributes"]["event_type"]["state"]
    assert event_states["movement_started"] == "Movement started"
    assert event_states["position_lost"] == "Position lost"
    assert event_states["entered_zone"] == "Entered zone"
    assert event_states["left_zone"] == "Left zone"
    assert icons["entity"]["event"]["station_activity"]["default"] == (
        "mdi:radio-tower"
    )


def test_hub_entities_have_translations_and_icons() -> None:
    strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    icons = json.loads((COMPONENT / "icons.json").read_text(encoding="utf-8"))
    assert "api_connected" in strings["entity"]["binary_sensor"]
    assert "refresh" in strings["entity"]["button"]
    assert "connection_activity" in strings["entity"]["event"]
    assert strings["entity"]["sensor"]["overall_status"]["state"]["error"] == (
        "Error"
    )
    assert icons["entity"]["button"]["refresh"]["default"] == "mdi:refresh"


def test_setup_cleans_only_stale_aprs_devices() -> None:
    init_source = (COMPONENT / "__init__.py").read_text(encoding="utf-8")
    assert "should_remove_aprs_device" in init_source
    assert "remove_config_entry_id=entry.entry_id" in init_source
    assert "async_remove_config_entry_device" in init_source


def test_system_health_is_translated_and_excludes_sensitive_values() -> None:
    source = (COMPONENT / "system_health.py").read_text(encoding="utf-8")
    assert "def async_register(" in source
    assert "async_check_can_reach_url" in source
    assert "CONF_API_KEY" not in source
    assert "latitude" not in source
    assert "longitude" not in source
    assert ".data or {}" not in source

    strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    health_keys = strings["system_health"]["info"]
    assert "can_reach_aprs_fi" in health_keys
    assert "last_successful_update" in health_keys


def test_coordinator_uses_core_transition_logging() -> None:
    source = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")
    assert "config_entry=config_entry" in source
    assert "last_successful_update" in source
    assert "_LOGGER.error" not in source
    assert "_LOGGER.info" not in source

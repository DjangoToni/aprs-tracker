"""Test APRS Monitor setup and coordinator behavior in Home Assistant."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

from homeassistant.components.zone import DATA_ZONE_ENTITY_IDS
from homeassistant.components.zone.const import ATTR_PASSIVE, ATTR_RADIUS
from homeassistant.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.aprs_monitor.api import AprsFiError, Position
from custom_components.aprs_monitor.const import (
    CONF_DISPLAY_NAME,
    CONF_HOME_RADIUS,
    CONF_MAP_MARKER_STYLE,
    CONF_MAX_POSITION_AGE,
    CONF_MOVEMENT_SPEED_THRESHOLD,
    CONF_STATION_PROFILES,
    DOMAIN,
    MAP_MARKER_STYLE_APRS,
)
from custom_components.aprs_monitor.geo import (
    great_circle_distance_km,
    initial_bearing_degrees,
)

from .conftest import CALLSIGN


def _states_by_unique_id(hass: HomeAssistant, entry_id: str):
    registry = er.async_get(hass)
    return {
        entry.unique_id: hass.states.get(entry.entity_id)
        for entry in er.async_entries_for_config_entry(registry, entry_id)
    }


async def test_setup_creates_tracker_and_station_entities(
    hass: HomeAssistant,
    loaded_entry,
) -> None:
    """Set up one tracker, ten sensors, three binary sensors, and one event entity."""
    states = _states_by_unique_id(hass, loaded_entry.entry_id)

    assert len(states) == 20
    assert loaded_entry.version == 2
    assert CALLSIGN in loaded_entry.options[CONF_STATION_PROFILES]
    expected_station_ids = {
        f"{loaded_entry.entry_id}_{CALLSIGN}",
        *{
            f"{loaded_entry.entry_id}_{CALLSIGN}_{suffix}"
            for suffix in (
                "speed",
                "course",
                "course_direction",
                "altitude",
                "distance_from_home",
                "bearing_from_home",
                "last_seen",
                "position_age",
                "aprs_symbol",
                "station_status",
                "position_current",
                "near_home",
                "moving",
                "station_activity",
            )
        },
    }
    expected_hub_ids = {
        f"{loaded_entry.entry_id}_{suffix}"
        for suffix in (
            "api_connected",
            "overall_status",
            "last_successful_update",
            "connection_activity",
            "refresh",
        )
    }
    assert set(states) == expected_station_ids | expected_hub_ids
    tracker = states[f"{loaded_entry.entry_id}_{CALLSIGN}"]
    assert tracker is not None
    assert tracker.attributes["latitude"] == 47.3769
    assert tracker.attributes["longitude"] == 8.5417
    assert tracker.attributes["icon"] == "mdi:car"
    assert tracker.attributes["aprs_symbol_character"] == ">"
    assert tracker.attributes["aprs_symbol_icon"] == "mdi:car"
    assert tracker.attributes["aprs_symbol_picture"].startswith(
        "/api/aprs_monitor/symbol/2f-3e.png?token="
    )
    assert "entity_picture" not in tracker.attributes
    assert tracker.attributes["map_label"] == "HB9TST · 46 km/h · SE · 408 m"
    assert tracker.attributes["map_details"] == (
        "HB9TST · 46 km/h · SE (123°) · 408 m · 47.37690, 8.54170"
    )
    assert states[f"{loaded_entry.entry_id}_{CALLSIGN}_speed"].state == "45.6"
    assert states[f"{loaded_entry.entry_id}_{CALLSIGN}_course"].state == "123.0"
    assert states[f"{loaded_entry.entry_id}_{CALLSIGN}_course_direction"].state == ("southeast")
    assert states[f"{loaded_entry.entry_id}_{CALLSIGN}_altitude"].state == "408.0"
    distance = round(great_circle_distance_km(47.0, 8.0, 47.3769, 8.5417), 2)
    bearing = round(initial_bearing_degrees(47.0, 8.0, 47.3769, 8.5417), 1)
    assert states[f"{loaded_entry.entry_id}_{CALLSIGN}_distance_from_home"].state == str(distance)
    assert states[f"{loaded_entry.entry_id}_{CALLSIGN}_bearing_from_home"].state == str(bearing)
    assert states[f"{loaded_entry.entry_id}_{CALLSIGN}_position_current"].state == "on"
    near_home = states[f"{loaded_entry.entry_id}_{CALLSIGN}_near_home"]
    assert near_home.state == "off"
    assert near_home.attributes["home_radius_km"] == 25.0
    assert near_home.attributes["distance_km"] == distance
    moving = states[f"{loaded_entry.entry_id}_{CALLSIGN}_moving"]
    assert moving.state == "on"
    assert moving.attributes["movement_speed_threshold_kmh"] == 1.0
    assert moving.attributes["speed_kmh"] == 45.6
    assert states[f"{loaded_entry.entry_id}_{CALLSIGN}_aprs_symbol"].state == "/>"
    assert states[f"{loaded_entry.entry_id}_{CALLSIGN}_station_status"].state == "current"
    position_age = states[f"{loaded_entry.entry_id}_{CALLSIGN}_position_age"]
    assert 4 <= float(position_age.state) <= 6
    activity = states[f"{loaded_entry.entry_id}_{CALLSIGN}_station_activity"]
    assert activity.state == "unknown"
    assert activity.attributes["event_type"] is None
    assert states[f"{loaded_entry.entry_id}_api_connected"].state == "on"
    overall = states[f"{loaded_entry.entry_id}_overall_status"]
    assert overall.state == "ok"
    assert overall.attributes["current_station_count"] == 1
    assert states[f"{loaded_entry.entry_id}_last_successful_update"].state != (STATE_UNAVAILABLE)
    assert states[f"{loaded_entry.entry_id}_connection_activity"].state == "unknown"
    assert states[f"{loaded_entry.entry_id}_refresh"].state == "unknown"


async def test_update_failure_and_recovery(
    hass: HomeAssistant,
    loaded_entry,
    position: Position,
) -> None:
    """Make entities unavailable after an API error and recover on success."""
    coordinator = hass.data[DOMAIN][loaded_entry.entry_id]

    with patch(
        "custom_components.aprs_monitor.coordinator.async_get_positions",
        side_effect=AprsFiError("temporary outage"),
    ):
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    states = _states_by_unique_id(hass, loaded_entry.entry_id)
    station_prefix = f"{loaded_entry.entry_id}_{CALLSIGN}"
    assert all(
        state.state == STATE_UNAVAILABLE
        for unique_id, state in states.items()
        if unique_id.startswith(station_prefix)
    )
    assert states[f"{loaded_entry.entry_id}_api_connected"].state == "off"
    assert states[f"{loaded_entry.entry_id}_overall_status"].state == "error"
    assert (
        states[f"{loaded_entry.entry_id}_connection_activity"].attributes["event_type"]
        == "api_unavailable"
    )
    assert states[f"{loaded_entry.entry_id}_last_successful_update"].state != (STATE_UNAVAILABLE)

    with patch(
        "custom_components.aprs_monitor.coordinator.async_get_positions",
        return_value={CALLSIGN: position},
    ):
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    states = _states_by_unique_id(hass, loaded_entry.entry_id)
    assert all(state.state != STATE_UNAVAILABLE for state in states.values())
    activity = states[f"{loaded_entry.entry_id}_{CALLSIGN}_station_activity"]
    assert activity.state == "unknown"
    assert activity.attributes["event_type"] is None
    assert states[f"{loaded_entry.entry_id}_api_connected"].state == "on"
    assert (
        states[f"{loaded_entry.entry_id}_connection_activity"].attributes["event_type"]
        == "api_recovered"
    )


async def test_three_callsigns_create_all_station_entities(
    hass: HomeAssistant,
    config_entry,
    position: Position,
) -> None:
    """Create a complete set of 15 entities for each of three callsigns."""
    callsigns = (CALLSIGN, "HB9TWO-7", "HB9THR-9")
    hass.config.latitude = 47.0
    hass.config.longitude = 8.0
    hass.config_entries.async_update_entry(
        config_entry,
        data={**config_entry.data, "callsigns": list(callsigns)},
    )
    positions = {callsign: replace(position, callsign=callsign) for callsign in callsigns}
    with patch(
        "custom_components.aprs_monitor.coordinator.async_get_positions",
        return_value=positions,
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    states = _states_by_unique_id(hass, config_entry.entry_id)
    assert len(states) == 50
    for callsign in callsigns:
        assert states[f"{config_entry.entry_id}_{callsign}"] is not None
        assert states[f"{config_entry.entry_id}_{callsign}_station_activity"] is not None


async def test_station_profile_applies_name_and_individual_thresholds(
    hass: HomeAssistant,
    config_entry,
    position: Position,
) -> None:
    """Apply one station profile without changing the callsign identity."""
    hass.config.latitude = 47.0
    hass.config.longitude = 8.0
    hass.config_entries.async_update_entry(
        config_entry,
        options={
            CONF_STATION_PROFILES: {
                CALLSIGN: {
                    CONF_DISPLAY_NAME: "Einsatzfahrzeug",
                    CONF_HOME_RADIUS: 100.0,
                    CONF_MAX_POSITION_AGE: 30,
                    CONF_MOVEMENT_SPEED_THRESHOLD: 50.0,
                }
            }
        },
    )
    with patch(
        "custom_components.aprs_monitor.coordinator.async_get_positions",
        return_value={CALLSIGN: position},
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    states = _states_by_unique_id(hass, config_entry.entry_id)
    tracker = states[f"{config_entry.entry_id}_{CALLSIGN}"]
    assert tracker.attributes["map_label"] == ("Einsatzfahrzeug · 46 km/h · SE · 408 m")
    assert tracker.attributes["map_details"] == (
        "Einsatzfahrzeug (HB9TST) · 46 km/h · SE (123°) · 408 m · 47.37690, 8.54170"
    )
    assert states[f"{config_entry.entry_id}_{CALLSIGN}_near_home"].state == "on"
    moving = states[f"{config_entry.entry_id}_{CALLSIGN}_moving"]
    assert moving.state == "off"
    assert moving.attributes["movement_speed_threshold_kmh"] == 50.0
    device = next(
        item
        for item in dr.async_entries_for_config_entry(dr.async_get(hass), config_entry.entry_id)
        if (DOMAIN, CALLSIGN) in item.identifiers
    )
    assert device.name == "APRS Einsatzfahrzeug"


async def test_aprs_map_marker_style_uses_local_entity_picture(
    hass: HomeAssistant,
    config_entry,
    position: Position,
) -> None:
    """Switch map markers without changing the tracker entity identity."""
    hass.config_entries.async_update_entry(
        config_entry,
        options={CONF_MAP_MARKER_STYLE: MAP_MARKER_STYLE_APRS},
    )
    with patch(
        "custom_components.aprs_monitor.coordinator.async_get_positions",
        return_value={CALLSIGN: position},
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    states = _states_by_unique_id(hass, config_entry.entry_id)
    tracker = states[f"{config_entry.entry_id}_{CALLSIGN}"]
    assert tracker.attributes["entity_picture"].startswith(
        "/api/aprs_monitor/symbol/2f-3e.png?token="
    )
    assert tracker.attributes["icon"] == "mdi:car"


async def test_near_home_radius_transition(hass: HomeAssistant, loaded_entry) -> None:
    """Update proximity when the configured radius changes."""
    coordinator = hass.data[DOMAIN][loaded_entry.entry_id]
    coordinator.station_profiles[CALLSIGN] = replace(
        coordinator.profile(CALLSIGN), home_radius_km=100.0
    )
    coordinator.async_update_listeners()
    await hass.async_block_till_done()

    states = _states_by_unique_id(hass, loaded_entry.entry_id)
    near_home = states[f"{loaded_entry.entry_id}_{CALLSIGN}_near_home"]
    assert near_home.state == "on"
    assert near_home.attributes["home_radius_km"] == 100.0
    activity = states[f"{loaded_entry.entry_id}_{CALLSIGN}_station_activity"]
    assert activity.attributes["event_type"] == "entered_home_radius"
    assert activity.attributes["home_radius_km"] == 100.0


async def test_active_zone_entry_and_exit_events(
    hass: HomeAssistant,
    loaded_entry,
    position: Position,
) -> None:
    """Emit useful zone transitions without exposing coordinates."""
    coordinator = hass.data[DOMAIN][loaded_entry.entry_id]
    hass.states.async_set(
        "zone.radio_club",
        "0",
        {
            ATTR_FRIENDLY_NAME: "Radio club",
            ATTR_LATITUDE: position.latitude,
            ATTR_LONGITUDE: position.longitude,
            ATTR_RADIUS: 500.0,
            ATTR_PASSIVE: False,
        },
    )
    await hass.async_block_till_done()
    assert "zone.radio_club" in hass.data[DATA_ZONE_ENTITY_IDS]

    with patch(
        "custom_components.aprs_monitor.coordinator.async_get_positions",
        return_value={CALLSIGN: position},
    ):
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    states = _states_by_unique_id(hass, loaded_entry.entry_id)
    activity = states[f"{loaded_entry.entry_id}_{CALLSIGN}_station_activity"]
    assert activity.attributes["event_type"] == "entered_zone"
    assert activity.attributes["zone_entity_id"] == "zone.radio_club"
    assert activity.attributes["zone_name"] == "Radio club"
    assert activity.attributes["from_zone_entity_id"] is None
    assert activity.attributes["to_zone_entity_id"] == "zone.radio_club"
    assert "latitude" not in activity.attributes
    assert "longitude" not in activity.attributes

    outside = replace(position, latitude=46.0, longitude=7.0)
    with patch(
        "custom_components.aprs_monitor.coordinator.async_get_positions",
        return_value={CALLSIGN: outside},
    ):
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    states = _states_by_unique_id(hass, loaded_entry.entry_id)
    activity = states[f"{loaded_entry.entry_id}_{CALLSIGN}_station_activity"]
    assert activity.attributes["event_type"] == "left_zone"
    assert activity.attributes["zone_entity_id"] == "zone.radio_club"
    assert activity.attributes["from_zone_entity_id"] == "zone.radio_club"
    assert activity.attributes["to_zone_entity_id"] is None


async def test_passive_zone_does_not_emit_active_zone_event(
    hass: HomeAssistant,
    loaded_entry,
    position: Position,
) -> None:
    """Follow Home Assistant semantics by ignoring passive zones as active zones."""
    coordinator = hass.data[DOMAIN][loaded_entry.entry_id]
    hass.states.async_set(
        "zone.passive_area",
        "0",
        {
            ATTR_FRIENDLY_NAME: "Passive area",
            ATTR_LATITUDE: position.latitude,
            ATTR_LONGITUDE: position.longitude,
            ATTR_RADIUS: 500.0,
            ATTR_PASSIVE: True,
        },
    )
    await hass.async_block_till_done()

    with patch(
        "custom_components.aprs_monitor.coordinator.async_get_positions",
        return_value={CALLSIGN: position},
    ):
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    states = _states_by_unique_id(hass, loaded_entry.entry_id)
    activity = states[f"{loaded_entry.entry_id}_{CALLSIGN}_station_activity"]
    assert activity.attributes["event_type"] is None


async def test_manual_refresh_button_requests_coordinator_update(
    hass: HomeAssistant,
    loaded_entry,
) -> None:
    """Make the hub refresh button call the shared coordinator."""
    registry = er.async_get(hass)
    button_entry = next(
        item
        for item in er.async_entries_for_config_entry(registry, loaded_entry.entry_id)
        if item.unique_id == f"{loaded_entry.entry_id}_refresh"
    )
    coordinator = hass.data[DOMAIN][loaded_entry.entry_id]
    with patch.object(
        coordinator,
        "async_request_refresh",
        new_callable=AsyncMock,
    ) as request_refresh:
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": button_entry.entity_id},
            blocking=True,
        )
    request_refresh.assert_awaited_once_with()


async def test_movement_threshold_transition(hass: HomeAssistant, loaded_entry) -> None:
    """Update movement when the configured speed threshold changes."""
    coordinator = hass.data[DOMAIN][loaded_entry.entry_id]
    coordinator.station_profiles[CALLSIGN] = replace(
        coordinator.profile(CALLSIGN), movement_speed_threshold_kmh=50.0
    )
    coordinator.async_update_listeners()
    await hass.async_block_till_done()

    states = _states_by_unique_id(hass, loaded_entry.entry_id)
    moving = states[f"{loaded_entry.entry_id}_{CALLSIGN}_moving"]
    assert moving.state == "off"
    assert moving.attributes["movement_speed_threshold_kmh"] == 50.0
    activity = states[f"{loaded_entry.entry_id}_{CALLSIGN}_station_activity"]
    assert activity.attributes["event_type"] == "movement_stopped"
    assert activity.attributes["movement_speed_threshold_kmh"] == 50.0


async def test_stale_position_makes_proximity_unknown(
    hass: HomeAssistant,
    loaded_entry,
    position: Position,
) -> None:
    """Do not report a stale position as outside the home radius."""
    coordinator = hass.data[DOMAIN][loaded_entry.entry_id]
    stale_position = replace(
        position,
        last_seen=datetime.now(UTC) - timedelta(minutes=180),
    )
    with patch(
        "custom_components.aprs_monitor.coordinator.async_get_positions",
        return_value={CALLSIGN: stale_position},
    ):
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    states = _states_by_unique_id(hass, loaded_entry.entry_id)
    assert states[f"{loaded_entry.entry_id}_{CALLSIGN}_near_home"].state == STATE_UNAVAILABLE
    assert states[f"{loaded_entry.entry_id}_{CALLSIGN}_position_current"].state == "off"
    assert states[f"{loaded_entry.entry_id}_{CALLSIGN}_station_status"].state == "stale"
    assert states[f"{loaded_entry.entry_id}_{CALLSIGN}_position_age"].state != (STATE_UNAVAILABLE)
    activity = states[f"{loaded_entry.entry_id}_{CALLSIGN}_station_activity"]
    assert activity.attributes["event_type"] == "position_stale"


async def test_missing_speed_makes_movement_unknown(
    hass: HomeAssistant,
    loaded_entry,
    position: Position,
) -> None:
    """Do not report missing APRS speed as station standstill."""
    coordinator = hass.data[DOMAIN][loaded_entry.entry_id]
    position_without_speed = replace(position, speed_kmh=None)
    with patch(
        "custom_components.aprs_monitor.coordinator.async_get_positions",
        return_value={CALLSIGN: position_without_speed},
    ):
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    states = _states_by_unique_id(hass, loaded_entry.entry_id)
    assert states[f"{loaded_entry.entry_id}_{CALLSIGN}_moving"].state == STATE_UNAVAILABLE
    assert states[f"{loaded_entry.entry_id}_{CALLSIGN}_position_current"].state == "on"
    tracker = states[f"{loaded_entry.entry_id}_{CALLSIGN}"]
    assert tracker.attributes["map_label"] == "HB9TST · SE · 408 m"
    assert tracker.attributes["map_details"] == ("HB9TST · SE (123°) · 408 m · 47.37690, 8.54170")


async def test_missing_position_has_explicit_station_status(
    hass: HomeAssistant,
    loaded_entry,
) -> None:
    """Expose a successful response without this station as no position."""
    coordinator = hass.data[DOMAIN][loaded_entry.entry_id]
    with patch(
        "custom_components.aprs_monitor.coordinator.async_get_positions",
        return_value={},
    ):
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    states = _states_by_unique_id(hass, loaded_entry.entry_id)
    assert states[f"{loaded_entry.entry_id}_{CALLSIGN}_station_status"].state == ("no_position")
    assert states[f"{loaded_entry.entry_id}_{CALLSIGN}_position_current"].state == "off"
    activity = states[f"{loaded_entry.entry_id}_{CALLSIGN}_station_activity"]
    assert activity.attributes["event_type"] == "position_lost"


async def test_unload_removes_runtime_states(hass: HomeAssistant, loaded_entry) -> None:
    """Unload all APRS Monitor platforms cleanly."""
    entity_ids = [
        entry.entity_id
        for entry in er.async_entries_for_config_entry(
            er.async_get(hass),
            loaded_entry.entry_id,
        )
    ]

    assert await hass.config_entries.async_unload(loaded_entry.entry_id)
    await hass.async_block_till_done()

    assert loaded_entry.entry_id not in hass.data.get(DOMAIN, {})
    assert all(hass.states.get(entity_id).state == STATE_UNAVAILABLE for entity_id in entity_ids)

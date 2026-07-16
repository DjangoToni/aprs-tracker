"""Station activity events for APRS Monitor automations."""

from __future__ import annotations

from typing import Any

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .activity import EVENT_TYPES, activity_transitions, build_activity_snapshot
from .api import Position, position_age_minutes
from .const import DOMAIN
from .geo import great_circle_distance_km
from .hub import hub_device_info, station_device_info

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create one activity event entity for every configured callsign."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            *(
                AprsStationActivityEvent(hass, coordinator, entry.entry_id, callsign)
                for callsign in coordinator.callsigns
            ),
            AprsConnectionEvent(coordinator, entry.entry_id),
        ]
    )


class AprsConnectionEvent(CoordinatorEntity, EventEntity):
    """Emit central API failure and recovery events."""

    _attr_has_entity_name = True
    _attr_translation_key = "connection_activity"
    _attr_event_types = ["api_unavailable", "api_recovered"]
    _attr_icon = "mdi:cloud-sync"

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_connection_activity"
        self._attr_device_info = hub_device_info(entry_id)
        self._connected = coordinator.last_update_success

    @property
    def available(self) -> bool:
        """Keep connection events visible during an outage."""
        return True

    def _handle_coordinator_update(self) -> None:
        """Emit only genuine changes in coordinator connectivity."""
        connected = self.coordinator.last_update_success
        if connected != self._connected:
            self._trigger_event("api_recovered" if connected else "api_unavailable")
            self._connected = connected
        super()._handle_coordinator_update()


class AprsStationActivityEvent(CoordinatorEntity, EventEntity):
    """Emit automation-friendly events after successful APRS updates."""

    _attr_has_entity_name = True
    _attr_translation_key = "station_activity"
    _attr_event_types = EVENT_TYPES
    _attr_icon = "mdi:radio-tower"

    def __init__(self, hass, coordinator, entry_id: str, callsign: str) -> None:
        super().__init__(coordinator)
        self._hass = hass
        self._callsign = callsign
        self._attr_unique_id = f"{entry_id}_{callsign}_station_activity"
        self._attr_device_info = station_device_info(coordinator, callsign)
        self._snapshot = self._activity_snapshot

    def _handle_coordinator_update(self) -> None:
        """Emit events only for transitions between successful API updates."""
        if self.coordinator.last_update_success:
            current = self._activity_snapshot
            for event_type in activity_transitions(self._snapshot, current):
                self._trigger_event(event_type, self._event_attributes(event_type))
                self.async_write_ha_state()
            self._snapshot = current
        super()._handle_coordinator_update()

    @property
    def _position(self) -> Position | None:
        return (self.coordinator.data or {}).get(self._callsign)

    @property
    def _activity_snapshot(self):
        profile = self.coordinator.profile(self._callsign)
        return build_activity_snapshot(
            self._position,
            profile.max_position_age,
            profile.movement_speed_threshold_kmh,
            profile.home_radius_km,
            self._hass.config.latitude,
            self._hass.config.longitude,
        )

    def _event_attributes(self, event_type: str) -> dict[str, Any]:
        """Return useful non-coordinate automation context for an event."""
        position = self._position
        attributes: dict[str, Any] = {
            "callsign": self._callsign,
            "status": self._activity_snapshot.status,
        }
        if position is not None:
            attributes["position_age_minutes"] = position_age_minutes(position)
            attributes["speed_kmh"] = position.speed_kmh
            attributes["distance_from_home_km"] = round(
                great_circle_distance_km(
                    self._hass.config.latitude,
                    self._hass.config.longitude,
                    position.latitude,
                    position.longitude,
                ),
                2,
            )
        if event_type in {"movement_started", "movement_stopped"}:
            attributes["movement_speed_threshold_kmh"] = (
                self.coordinator.profile(
                    self._callsign
                ).movement_speed_threshold_kmh
            )
        if event_type in {"entered_home_radius", "left_home_radius"}:
            attributes["home_radius_km"] = self.coordinator.profile(
                self._callsign
            ).home_radius_km
        return attributes

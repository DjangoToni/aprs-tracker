"""Binary sensors for APRS Monitor."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import Position, is_position_stale, position_age_minutes
from .const import DOMAIN
from .geo import great_circle_distance_km
from .hub import hub_device_info, station_device_info

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create position-freshness and proximity sensors for every callsign."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [AprsApiConnectedBinarySensor(coordinator, entry.entry_id)]
    for callsign in coordinator.callsigns:
        entities.extend(
            (
                AprsPositionCurrentBinarySensor(coordinator, entry.entry_id, callsign),
                AprsNearHomeBinarySensor(hass, coordinator, entry.entry_id, callsign),
                AprsMovingBinarySensor(coordinator, entry.entry_id, callsign),
            )
        )
    async_add_entities(entities)


class AprsApiConnectedBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Expose coordinator connectivity even while updates are failing."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True
    _attr_translation_key = "api_connected"

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_api_connected"
        self._attr_device_info = hub_device_info(entry_id)

    @property
    def available(self) -> bool:
        """Always expose the known connectivity state."""
        return True

    @property
    def is_on(self) -> bool:
        """Return whether the most recent API request succeeded."""
        return self.coordinator.last_update_success


class AprsPositionCurrentBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Indicate whether a station has a current APRS position."""

    _attr_has_entity_name = True
    _attr_translation_key = "position_current"

    def __init__(self, coordinator, entry_id: str, callsign: str) -> None:
        super().__init__(coordinator)
        self._callsign = callsign
        self._attr_unique_id = f"{entry_id}_{callsign}_position_current"
        self._attr_device_info = station_device_info(coordinator, callsign)

    @property
    def is_on(self) -> bool:
        """Return whether the latest position is within the configured age."""
        position = self._position
        return position is not None and not is_position_stale(
            position,
            self.coordinator.profile(self._callsign).max_position_age,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose freshness details for dashboards and automations."""
        position = self._position
        attributes: dict[str, Any] = {
            "stale_after_minutes": self.coordinator.profile(
                self._callsign
            ).max_position_age,
        }
        if position is not None:
            attributes["position_age_minutes"] = position_age_minutes(position)
        return attributes

    @property
    def _position(self) -> Position | None:
        return (self.coordinator.data or {}).get(self._callsign)


class AprsNearHomeBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Indicate whether a station is inside the configured home radius."""

    _attr_device_class = BinarySensorDeviceClass.PRESENCE
    _attr_has_entity_name = True
    _attr_translation_key = "near_home"

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator,
        entry_id: str,
        callsign: str,
    ) -> None:
        super().__init__(coordinator)
        self._hass = hass
        self._callsign = callsign
        self._attr_unique_id = f"{entry_id}_{callsign}_near_home"
        self._attr_device_info = station_device_info(coordinator, callsign)

    @property
    def available(self) -> bool:
        """Return whether a current position can be evaluated."""
        position = self._position
        return (
            super().available
            and position is not None
            and not is_position_stale(
                position, self.coordinator.profile(self._callsign).max_position_age
            )
        )

    @property
    def is_on(self) -> bool:
        """Return whether the station is inside the configured radius."""
        distance = self._distance_km
        return (
            distance is not None
            and distance <= self.coordinator.profile(self._callsign).home_radius_km
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the evaluated distance and configured threshold."""
        attributes: dict[str, Any] = {
            "home_radius_km": self.coordinator.profile(self._callsign).home_radius_km,
        }
        if (distance := self._distance_km) is not None:
            attributes["distance_km"] = round(distance, 2)
        return attributes

    @property
    def _distance_km(self) -> float | None:
        position = self._position
        if position is None:
            return None
        return great_circle_distance_km(
            self._hass.config.latitude,
            self._hass.config.longitude,
            position.latitude,
            position.longitude,
        )

    @property
    def _position(self) -> Position | None:
        return (self.coordinator.data or {}).get(self._callsign)


class AprsMovingBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Indicate whether a station exceeds the configured movement threshold."""

    _attr_device_class = BinarySensorDeviceClass.MOVING
    _attr_has_entity_name = True
    _attr_translation_key = "moving"

    def __init__(self, coordinator, entry_id: str, callsign: str) -> None:
        super().__init__(coordinator)
        self._callsign = callsign
        self._attr_unique_id = f"{entry_id}_{callsign}_moving"
        self._attr_device_info = station_device_info(coordinator, callsign)

    @property
    def available(self) -> bool:
        """Return whether current speed data can be evaluated."""
        position = self._position
        return (
            super().available
            and position is not None
            and position.speed_kmh is not None
            and not is_position_stale(
                position, self.coordinator.profile(self._callsign).max_position_age
            )
        )

    @property
    def is_on(self) -> bool:
        """Return whether reported speed exceeds the movement threshold."""
        position = self._position
        return (
            position is not None
            and position.speed_kmh is not None
            and position.speed_kmh
            >= self.coordinator.profile(self._callsign).movement_speed_threshold_kmh
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose reported speed and the configured threshold."""
        attributes: dict[str, Any] = {
            "movement_speed_threshold_kmh": (
                self.coordinator.profile(
                    self._callsign
                ).movement_speed_threshold_kmh
            ),
        }
        if (position := self._position) is not None and position.speed_kmh is not None:
            attributes["speed_kmh"] = position.speed_kmh
        return attributes

    @property
    def _position(self) -> Position | None:
        return (self.coordinator.data or {}).get(self._callsign)

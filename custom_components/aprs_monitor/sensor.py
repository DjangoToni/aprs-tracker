"""Sensor entities for APRS Monitor."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEGREE,
    EntityCategory,
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import Position, is_position_stale, position_age_minutes, position_status
from .const import DOMAIN
from .geo import (
    CARDINAL_DIRECTIONS,
    course_to_cardinal,
    great_circle_distance_km,
    initial_bearing_degrees,
)
from .hub import hub_device_info, station_device_info
from .station_summary import build_station_summary

PARALLEL_UPDATES = 0


@dataclass(frozen=True)
class AprsSensorDescription:
    """Describe one APRS Monitor sensor."""

    key: str
    value_fn: Callable[[Position, HomeAssistant], Any]
    device_class: SensorDeviceClass | None = None
    native_unit: str | None = None
    state_class: SensorStateClass | None = None
    entity_category: EntityCategory | None = None
    icon: str | None = None
    allow_stale: bool = False
    suggested_display_precision: int | None = None
    options: tuple[str, ...] | None = None


SENSORS = (
    AprsSensorDescription(
        key="speed",
        value_fn=lambda position, hass: position.speed_kmh,
        device_class=SensorDeviceClass.SPEED,
        native_unit=UnitOfSpeed.KILOMETERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AprsSensorDescription(
        key="course",
        value_fn=lambda position, hass: position.course,
        native_unit=DEGREE,
        state_class=SensorStateClass.MEASUREMENT_ANGLE,
        icon="mdi:compass-outline",
    ),
    AprsSensorDescription(
        key="course_direction",
        value_fn=lambda position, hass: course_to_cardinal(position.course),
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:compass-rose",
        options=CARDINAL_DIRECTIONS,
    ),
    AprsSensorDescription(
        key="altitude",
        value_fn=lambda position, hass: position.altitude_m,
        device_class=SensorDeviceClass.DISTANCE,
        native_unit=UnitOfLength.METERS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:altimeter",
    ),
    AprsSensorDescription(
        key="distance_from_home",
        value_fn=lambda position, hass: round(
            great_circle_distance_km(
                hass.config.latitude,
                hass.config.longitude,
                position.latitude,
                position.longitude,
            ),
            2,
        ),
        device_class=SensorDeviceClass.DISTANCE,
        native_unit=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:map-marker-distance",
        suggested_display_precision=2,
    ),
    AprsSensorDescription(
        key="bearing_from_home",
        value_fn=lambda position, hass: (
            round(bearing, 1)
            if (
                bearing := initial_bearing_degrees(
                    hass.config.latitude,
                    hass.config.longitude,
                    position.latitude,
                    position.longitude,
                )
            )
            is not None
            else None
        ),
        native_unit=DEGREE,
        state_class=SensorStateClass.MEASUREMENT_ANGLE,
        icon="mdi:compass-rose",
        suggested_display_precision=1,
    ),
    AprsSensorDescription(
        key="last_seen",
        value_fn=lambda position, hass: position.last_seen,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        allow_stale=True,
    ),
    AprsSensorDescription(
        key="position_age",
        value_fn=lambda position, hass: position_age_minutes(position),
        device_class=SensorDeviceClass.DURATION,
        native_unit=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:timer-marker-outline",
        allow_stale=True,
    ),
    AprsSensorDescription(
        key="aprs_symbol",
        value_fn=lambda position, hass: position.symbol,
        icon="mdi:map-marker-star",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create APRS sensors for all configured callsigns."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            *(
                AprsMonitorSensor(hass, coordinator, entry.entry_id, callsign, description)
                for callsign in coordinator.callsigns
                for description in SENSORS
            ),
            *(
                AprsStationStatusSensor(coordinator, entry.entry_id, callsign)
                for callsign in coordinator.callsigns
            ),
            AprsOverallStatusSensor(coordinator, entry.entry_id),
            AprsLastSuccessfulUpdateSensor(coordinator, entry.entry_id),
        ]
    )


class AprsMonitorSensor(CoordinatorEntity, SensorEntity):
    """Expose one value from the current station position."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator,
        entry_id: str,
        callsign: str,
        description: AprsSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self._hass = hass
        self._callsign = callsign
        self._description = description
        self._attr_unique_id = f"{entry_id}_{callsign}_{description.key}"
        self._attr_translation_key = description.key
        self._attr_device_class = description.device_class
        self._attr_native_unit_of_measurement = description.native_unit
        self._attr_state_class = description.state_class
        self._attr_entity_category = description.entity_category
        self._attr_icon = description.icon
        self._attr_suggested_display_precision = description.suggested_display_precision
        self._attr_options = list(description.options) if description.options else None
        self._attr_device_info = station_device_info(coordinator, callsign)

    @property
    def available(self) -> bool:
        """Return whether this value is present in the API response."""
        position = self._position
        return (
            super().available
            and position is not None
            and self.native_value is not None
            and (
                self._description.allow_stale
                or not is_position_stale(
                    position,
                    self.coordinator.profile(self._callsign).max_position_age,
                )
            )
        )

    @property
    def native_value(self) -> float | str | datetime | None:
        """Return the current sensor value."""
        position = self._position
        return self._description.value_fn(position, self._hass) if position else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose age diagnostics on the last-seen sensor."""
        position = self._position
        if position is None or not self._description.allow_stale:
            return None
        return {
            "position_age_minutes": position_age_minutes(position),
            "position_stale": is_position_stale(
                position,
                self.coordinator.profile(self._callsign).max_position_age,
            ),
            "stale_after_minutes": self.coordinator.profile(self._callsign).max_position_age,
        }

    @property
    def _position(self) -> Position | None:
        return (self.coordinator.data or {}).get(self._callsign)


class AprsStationStatusSensor(CoordinatorEntity, SensorEntity):
    """Expose whether the latest APRS position is current, stale, or missing."""

    _attr_has_entity_name = True
    _attr_translation_key = "station_status"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["current", "stale", "no_position"]
    _attr_icon = "mdi:list-status"

    def __init__(self, coordinator, entry_id: str, callsign: str) -> None:
        super().__init__(coordinator)
        self._callsign = callsign
        self._attr_unique_id = f"{entry_id}_{callsign}_station_status"
        self._attr_device_info = station_device_info(coordinator, callsign)

    @property
    def native_value(self) -> str:
        """Return the position freshness state."""
        return position_status(
            (self.coordinator.data or {}).get(self._callsign),
            self.coordinator.profile(self._callsign).max_position_age,
        )

    @property
    def extra_state_attributes(self) -> dict[str, int]:
        """Expose the configured freshness limit."""
        return {"stale_after_minutes": self.coordinator.profile(self._callsign).max_position_age}


class AprsOverallStatusSensor(CoordinatorEntity, SensorEntity):
    """Expose aggregate station and API health on the hub device."""

    _attr_has_entity_name = True
    _attr_translation_key = "overall_status"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["ok", "degraded", "error"]
    _attr_icon = "mdi:heart-pulse"

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_overall_status"
        self._attr_device_info = hub_device_info(entry_id)

    @property
    def available(self) -> bool:
        """Keep aggregate failure state visible during an outage."""
        return True

    @property
    def _summary(self):
        return build_station_summary(
            self.coordinator.callsigns,
            self.coordinator.data or {},
            {
                callsign: self.coordinator.profile(callsign).max_position_age
                for callsign in self.coordinator.callsigns
            },
            self.coordinator.last_update_success,
        )

    @property
    def native_value(self) -> str:
        """Return OK, degraded, or error as a translated state key."""
        return self._summary.status

    @property
    def extra_state_attributes(self) -> dict[str, int]:
        """Expose privacy-safe aggregate station counts."""
        summary = self._summary
        return {
            "configured_station_count": len(self.coordinator.callsigns),
            "current_station_count": summary.current,
            "stale_station_count": summary.stale,
            "missing_station_count": summary.missing,
        }


class AprsLastSuccessfulUpdateSensor(CoordinatorEntity, SensorEntity):
    """Expose the last successful API update on the hub device."""

    _attr_has_entity_name = True
    _attr_translation_key = "last_successful_update"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_last_successful_update"
        self._attr_device_info = hub_device_info(entry_id)

    @property
    def available(self) -> bool:
        """Keep the previous successful timestamp visible during outages."""
        return self.coordinator.last_successful_update is not None

    @property
    def native_value(self) -> datetime | None:
        """Return the last successful coordinator update."""
        return self.coordinator.last_successful_update

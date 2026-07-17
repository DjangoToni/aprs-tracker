"""GPS trackers for APRS Monitor."""

from __future__ import annotations

from typing import Any

from homeassistant.components.device_tracker import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import Position, is_position_stale, position_age_minutes
from .aprs_symbols import aprs_symbol_character, aprs_symbol_icon
from .const import DOMAIN
from .geo import course_to_cardinal_abbreviation
from .hub import station_device_info

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create one tracker for every configured callsign."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AprsMonitorTracker(coordinator, entry.entry_id, callsign)
        for callsign in coordinator.callsigns
    )


class AprsMonitorTracker(CoordinatorEntity, TrackerEntity):
    """Represent the latest known station position."""

    _attr_has_entity_name = True
    _attr_location_accuracy = 20

    def __init__(self, coordinator, entry_id: str, callsign: str) -> None:
        super().__init__(coordinator)
        self._callsign = callsign
        self._attr_unique_id = f"{entry_id}_{callsign}"
        self._attr_name = None
        self._attr_device_info = station_device_info(coordinator, callsign)

    @property
    def available(self) -> bool:
        position = self._position
        return (
            super().available
            and position is not None
            and not is_position_stale(
                position, self.coordinator.profile(self._callsign).max_position_age
            )
        )

    @property
    def latitude(self) -> float | None:
        return self._position.latitude if self._position else None

    @property
    def longitude(self) -> float | None:
        return self._position.longitude if self._position else None

    @property
    def icon(self) -> str:
        """Use the reported APRS station type on Home Assistant maps."""
        return aprs_symbol_icon(self._position.symbol if self._position else None)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        position = self._position
        if position is None:
            return {"attribution": "Data provided by aprs.fi"}
        return {
            "attribution": "Data provided by aprs.fi",
            "callsign": position.callsign,
            "course": position.course,
            "speed_kmh": position.speed_kmh,
            "altitude_m": position.altitude_m,
            "symbol": position.symbol,
            "aprs_symbol_character": aprs_symbol_character(position.symbol),
            "aprs_symbol_icon": aprs_symbol_icon(position.symbol),
            "comment": position.comment,
            "last_seen": position.last_seen.isoformat(),
            "position_age_minutes": position_age_minutes(position),
            "position_stale": is_position_stale(
                position,
                self.coordinator.profile(self._callsign).max_position_age,
            ),
            "map_label": self._map_label(position),
            "stale_after_minutes": self.coordinator.profile(
                self._callsign
            ).max_position_age,
        }

    def _map_label(self, position: Position) -> str:
        """Return a compact label for Home Assistant's standard map card."""
        parts = [self.coordinator.profile(self._callsign).display_name]
        if position.speed_kmh is not None:
            parts.append(f"{position.speed_kmh:.0f} km/h")
        if direction := course_to_cardinal_abbreviation(position.course):
            parts.append(direction)
        if position.altitude_m is not None:
            parts.append(f"{position.altitude_m:.0f} m")
        return " · ".join(parts)

    @property
    def _position(self) -> Position | None:
        return (self.coordinator.data or {}).get(self._callsign)

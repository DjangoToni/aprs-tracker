"""System health support for APRS Monitor."""

from __future__ import annotations

from typing import Any

from homeassistant.components import system_health
from homeassistant.core import HomeAssistant, callback

from .const import (
    API_URL,
    CONF_CALLSIGNS,
    CONF_HOME_RADIUS,
    CONF_MAX_POSITION_AGE,
    CONF_MOVEMENT_SPEED_THRESHOLD,
    CONF_UPDATE_INTERVAL,
    DEFAULT_HOME_RADIUS,
    DEFAULT_MAX_POSITION_AGE,
    DEFAULT_MOVEMENT_SPEED_THRESHOLD,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)


@callback
def async_register(
    hass: HomeAssistant,
    register: system_health.SystemHealthRegistration,
) -> None:
    """Register APRS Monitor system health callbacks."""
    register.async_register_info(system_health_info)


async def system_health_info(hass: HomeAssistant) -> dict[str, Any]:
    """Return non-sensitive APRS Monitor system information."""
    entries = hass.config_entries.async_entries(DOMAIN)
    coordinators = list(hass.data.get(DOMAIN, {}).values())
    coordinator = coordinators[0] if len(coordinators) == 1 else None

    configured_station_count = sum(
        len(entry.options.get(CONF_CALLSIGNS, entry.data[CONF_CALLSIGNS]))
        for entry in entries
    )
    update_interval = (
        int(coordinator.update_interval.total_seconds() // 60)
        if coordinator is not None and coordinator.update_interval is not None
        else _entry_option(entries, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    )
    max_position_age = (
        coordinator.max_position_age
        if coordinator is not None
        else _entry_option(entries, CONF_MAX_POSITION_AGE, DEFAULT_MAX_POSITION_AGE)
    )
    home_radius = (
        coordinator.home_radius_km
        if coordinator is not None
        else _entry_option(entries, CONF_HOME_RADIUS, DEFAULT_HOME_RADIUS)
    )
    movement_speed_threshold = (
        coordinator.movement_speed_threshold_kmh
        if coordinator is not None
        else _entry_option(
            entries,
            CONF_MOVEMENT_SPEED_THRESHOLD,
            DEFAULT_MOVEMENT_SPEED_THRESHOLD,
        )
    )

    return {
        "can_reach_aprs_fi": system_health.async_check_can_reach_url(hass, API_URL),
        "configured_entries": len(entries),
        "loaded_entries": len(coordinators),
        "configured_station_count": configured_station_count,
        "update_interval_minutes": update_interval,
        "max_position_age_minutes": max_position_age,
        "home_radius_km": home_radius,
        "movement_speed_threshold_kmh": movement_speed_threshold,
        "last_update_success": (
            coordinator.last_update_success if coordinator is not None else None
        ),
        "last_successful_update": (
            coordinator.last_successful_update if coordinator is not None else None
        ),
    }


def _entry_option(
    entries,
    key: str,
    default: int | float,
) -> int | float | None:
    """Return one non-sensitive option for the supported single config entry."""
    if len(entries) != 1:
        return None
    return entries[0].options.get(key, default)

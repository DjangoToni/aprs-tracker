"""Diagnostics support for APRS Monitor."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_API_KEY,
    CONF_CALLSIGNS,
    CONF_STATION_PROFILES,
    DOMAIN,
    VERSION,
)
from .diagnostics_data import build_station_diagnostics

TO_REDACT = {CONF_API_KEY, CONF_CALLSIGNS, CONF_STATION_PROFILES}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics without credentials, station IDs, or location data."""
    diagnostics: dict[str, Any] = {
        "integration_version": VERSION,
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "entry_options": async_redact_data(dict(entry.options), TO_REDACT),
        "runtime": {"loaded": False},
    }

    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator is None:
        return diagnostics

    update_interval = coordinator.update_interval
    diagnostics["runtime"] = {
        "loaded": True,
        "last_update_success": coordinator.last_update_success,
        "update_interval_minutes": (
            int(update_interval.total_seconds() // 60) if update_interval is not None else None
        ),
        "max_position_age_minutes": coordinator.max_position_age,
        "home_radius_km": coordinator.home_radius_km,
        "movement_speed_threshold_kmh": coordinator.movement_speed_threshold_kmh,
        "configured_station_count": len(coordinator.callsigns),
        "configured_profile_count": len(coordinator.station_profiles),
        "stations": build_station_diagnostics(
            coordinator.callsigns,
            coordinator.data or {},
            {
                callsign: coordinator.profile(callsign).max_position_age
                for callsign in coordinator.callsigns
            },
        ),
    }
    return diagnostics

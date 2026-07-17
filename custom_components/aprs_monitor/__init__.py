"""APRS Monitor integration setup."""

from pathlib import Path
from secrets import token_urlsafe

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import binary_sensor as binary_sensor
from . import button as button
from . import device_tracker as device_tracker
from . import event as event
from . import sensor as sensor
from .const import (
    CONF_API_KEY,
    CONF_CALLSIGNS,
    CONF_HOME_RADIUS,
    CONF_MAP_MARKER_STYLE,
    CONF_MAX_POSITION_AGE,
    CONF_MOVEMENT_SPEED_THRESHOLD,
    CONF_STATION_PROFILES,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
    PLATFORMS,
    SYMBOL_TOKEN_DATA,
)
from .coordinator import AprsMonitorCoordinator
from .device_cleanup import should_remove_aprs_device
from .migration import normalized_runtime_options
from .symbol_view import AprsSymbolRenderer, AprsSymbolView

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
_SYMBOL_ASSET_PATH = Path(__file__).parent / "aprs_symbol_assets"
_FRONTEND_PATH = Path(__file__).parent / "frontend"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the APRS Monitor component."""
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                "/api/aprs_monitor/frontend",
                str(_FRONTEND_PATH),
                True,
            )
        ]
    )
    access_token = token_urlsafe(24)
    hass.data[SYMBOL_TOKEN_DATA] = access_token
    renderer = await hass.async_add_executor_job(
        AprsSymbolRenderer,
        _SYMBOL_ASSET_PATH,
    )
    hass.http.register_view(AprsSymbolView(hass, renderer, access_token))
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up APRS Monitor from a config entry."""
    options = normalized_runtime_options(entry.data, entry.options)
    callsigns = options[CONF_CALLSIGNS]
    if not callsigns:
        raise ConfigEntryError("APRS Monitor has no valid configured callsigns")
    update_interval = options[CONF_UPDATE_INTERVAL]
    max_position_age = options[CONF_MAX_POSITION_AGE]
    home_radius = options[CONF_HOME_RADIUS]
    movement_speed_threshold = options[CONF_MOVEMENT_SPEED_THRESHOLD]
    map_marker_style = options[CONF_MAP_MARKER_STYLE]
    coordinator = AprsMonitorCoordinator(
        hass,
        entry,
        async_get_clientsession(hass),
        entry.data[CONF_API_KEY],
        tuple(callsigns),
        int(update_interval),
        int(max_position_age),
        float(home_radius),
        float(movement_speed_threshold),
        str(map_marker_style),
        options[CONF_STATION_PROFILES],
    )
    await coordinator.async_config_entry_first_refresh()

    _remove_stale_devices(hass, entry, set(callsigns))

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate legacy entries to explicit, normalized station profiles."""
    if entry.version > 2:
        return False
    if entry.version < 2:
        hass.config_entries.async_update_entry(
            entry,
            options=normalized_runtime_options(entry.data, entry.options),
            version=2,
        )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an APRS Monitor config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        domain_data = hass.data.get(DOMAIN)
        if domain_data is not None:
            domain_data.pop(entry.entry_id, None)
            if not domain_data:
                hass.data.pop(DOMAIN, None)
    return unloaded


async def async_remove_config_entry_device(
    hass: HomeAssistant,
    entry: ConfigEntry,
    device_entry: dr.DeviceEntry,
) -> bool:
    """Allow removal only after a callsign was removed from configuration."""
    callsigns = entry.options.get(CONF_CALLSIGNS, entry.data[CONF_CALLSIGNS])
    return should_remove_aprs_device(device_entry.identifiers, callsigns)


def _remove_stale_devices(
    hass: HomeAssistant,
    entry: ConfigEntry,
    configured_callsigns: set[str],
) -> None:
    """Remove devices that are certainly absent from the configured callsigns."""
    registry = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(registry, entry.entry_id):
        if should_remove_aprs_device(device.identifiers, configured_callsigns):
            registry.async_update_device(
                device.id,
                remove_config_entry_id=entry.entry_id,
            )

"""Runtime privacy audit for complete config-entry diagnostics."""

import json

from homeassistant.core import HomeAssistant

from custom_components.aprs_monitor.const import (
    CONF_DISPLAY_NAME,
    CONF_STATION_PROFILES,
)
from custom_components.aprs_monitor.diagnostics import (
    async_get_config_entry_diagnostics,
)

from .conftest import API_KEY, CALLSIGN


async def test_complete_diagnostics_exclude_all_personal_values(
    hass: HomeAssistant,
    loaded_entry,
) -> None:
    """Never serialize credentials, identifiers, profiles, or packet content."""
    secret_name = "PRIVATE STATION NAME"
    hass.config_entries.async_update_entry(
        loaded_entry,
        options={
            **loaded_entry.options,
            CONF_STATION_PROFILES: {
                CALLSIGN: {CONF_DISPLAY_NAME: secret_name},
            },
        },
    )
    diagnostics = await async_get_config_entry_diagnostics(hass, loaded_entry)
    serialized = json.dumps(diagnostics, default=str)
    for secret in (
        API_KEY,
        CALLSIGN,
        secret_name,
        "47.3769",
        "8.5417",
        "Runtime test",
    ):
        assert secret not in serialized
    assert diagnostics["runtime"]["configured_station_count"] == 1
    assert diagnostics["runtime"]["configured_profile_count"] == 1

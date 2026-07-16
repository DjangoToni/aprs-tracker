"""Test APRS Monitor config, reauth and options flows."""

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.aprs_monitor import async_migrate_entry
from custom_components.aprs_monitor.api import AprsFiAuthenticationError, AprsFiError
from custom_components.aprs_monitor.const import (
    CONF_API_KEY,
    CONF_CALLSIGNS,
    CONF_DISPLAY_NAME,
    CONF_HOME_RADIUS,
    CONF_MAX_POSITION_AGE,
    CONF_MOVEMENT_SPEED_THRESHOLD,
    CONF_STATION_PROFILES,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
    NAME,
)

from .conftest import API_KEY, CALLSIGN


async def test_user_flow_success(hass: HomeAssistant) -> None:
    """Create a unique config entry after validating aprs.fi credentials."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with (
        patch(
            "custom_components.aprs_monitor.config_flow.async_validate_api",
            return_value=None,
        ) as validate,
        patch("custom_components.aprs_monitor.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: f" {API_KEY} ", CONF_CALLSIGNS: CALLSIGN.lower()},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == NAME
    assert result["data"] == {CONF_API_KEY: API_KEY, CONF_CALLSIGNS: [CALLSIGN]}
    validate.assert_awaited_once()


async def test_user_flow_recovers_from_api_errors(hass: HomeAssistant) -> None:
    """Show precise API errors and allow retrying the same flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    user_input = {CONF_API_KEY: API_KEY, CONF_CALLSIGNS: CALLSIGN}

    with patch(
        "custom_components.aprs_monitor.config_flow.async_validate_api",
        side_effect=AprsFiAuthenticationError("rejected"),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

    with patch(
        "custom_components.aprs_monitor.config_flow.async_validate_api",
        side_effect=AprsFiError("offline"),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    with (
        patch(
            "custom_components.aprs_monitor.config_flow.async_validate_api",
            return_value=None,
        ),
        patch("custom_components.aprs_monitor.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input)
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_aborts_duplicate(hass: HomeAssistant) -> None:
    """Let Home Assistant prevent a second APRS Monitor config entry."""
    existing = MockConfigEntry(
        domain=DOMAIN,
        title=NAME,
        data={CONF_API_KEY: API_KEY, CONF_CALLSIGNS: [CALLSIGN]},
        unique_id=DOMAIN,
    )
    existing.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_reauth_updates_existing_entry(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """Replace the API key without creating another entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": config_entry.entry_id,
        },
        data=config_entry.data,
    )
    assert result["step_id"] == "reauth_confirm"

    new_api_key = "replacement-api-key"
    with (
        patch(
            "custom_components.aprs_monitor.config_flow.async_validate_api",
            return_value=None,
        ),
        patch("custom_components.aprs_monitor.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: new_api_key},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert config_entry.data[CONF_API_KEY] == new_api_key
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1


async def test_options_flow_stores_normalized_values(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """Store callsigns and update limits through the options flow."""
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_CALLSIGNS: f"{CALLSIGN.lower()}, hb9new",
            CONF_HOME_RADIUS: 50.5,
            CONF_UPDATE_INTERVAL: 10,
            CONF_MAX_POSITION_AGE: 90,
            CONF_MOVEMENT_SPEED_THRESHOLD: 2.5,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "profiles"

    profiles_input = {
        CALLSIGN: {
            CONF_DISPLAY_NAME: "Mobilstation",
            CONF_HOME_RADIUS: 12.0,
            CONF_MAX_POSITION_AGE: 30,
            CONF_MOVEMENT_SPEED_THRESHOLD: 4.0,
        },
        "HB9NEW": {
            CONF_DISPLAY_NAME: "Basis",
            CONF_HOME_RADIUS: 50.5,
            CONF_MAX_POSITION_AGE: 90,
            CONF_MOVEMENT_SPEED_THRESHOLD: 2.5,
        },
    }
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], profiles_input
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {
        CONF_CALLSIGNS: [CALLSIGN, "HB9NEW"],
        CONF_HOME_RADIUS: 50.5,
        CONF_UPDATE_INTERVAL: 10,
        CONF_MAX_POSITION_AGE: 90,
        CONF_MOVEMENT_SPEED_THRESHOLD: 2.5,
        CONF_STATION_PROFILES: profiles_input,
    }


async def test_migration_rejects_unknown_future_schema(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """Never downgrade an entry created by a newer integration version."""
    hass.config_entries.async_update_entry(config_entry, version=99)
    assert await async_migrate_entry(hass, config_entry) is False
    assert config_entry.version == 99

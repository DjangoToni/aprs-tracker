"""Fixtures for APRS Monitor runtime tests."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.aprs_monitor.api import Position
from custom_components.aprs_monitor.const import CONF_API_KEY, CONF_CALLSIGNS, DOMAIN, NAME

API_KEY = "runtime-test-api-key"
CALLSIGN = "HB9TST"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading APRS Monitor from custom_components."""
    yield


@pytest.fixture
def position() -> Position:
    """Return a current APRS position with all optional values."""
    return Position(
        callsign=CALLSIGN,
        latitude=47.3769,
        longitude=8.5417,
        last_seen=datetime.now(UTC) - timedelta(minutes=5),
        course=123.0,
        speed_kmh=45.6,
        altitude_m=408.0,
        symbol="/>",
        comment="Runtime test",
    )


@pytest.fixture
def config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Add a configured APRS Monitor entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=NAME,
        data={CONF_API_KEY: API_KEY, CONF_CALLSIGNS: [CALLSIGN]},
        unique_id=DOMAIN,
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
async def loaded_entry(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    position: Position,
) -> MockConfigEntry:
    """Set up APRS Monitor with a mocked aprs.fi response."""
    hass.config.latitude = 47.0
    hass.config.longitude = 8.0
    with patch(
        "custom_components.aprs_monitor.coordinator.async_get_positions",
        return_value={CALLSIGN: position},
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    return config_entry

"""Shared aprs.fi update coordinator."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    AprsFiAuthenticationError,
    AprsFiError,
    AprsFiRateLimitError,
    Position,
    async_get_positions,
)
from .const import NAME
from .profiles import StationProfile, build_station_profiles

_LOGGER = logging.getLogger(__name__)


class AprsMonitorCoordinator(DataUpdateCoordinator):
    """Fetch every configured station in one API request."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        session,
        api_key: str,
        callsigns: tuple[str, ...],
        update_interval: int,
        max_position_age: int,
        home_radius_km: float,
        movement_speed_threshold_kmh: float,
        map_marker_style: str,
        raw_station_profiles: dict,
    ):
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=NAME,
            update_interval=timedelta(minutes=update_interval),
        )
        self.session = session
        self.api_key = api_key
        self.callsigns = callsigns
        self.max_position_age = max_position_age
        self.home_radius_km = home_radius_km
        self.movement_speed_threshold_kmh = movement_speed_threshold_kmh
        self.map_marker_style = map_marker_style
        self.station_profiles = build_station_profiles(
            callsigns,
            raw_station_profiles,
            max_position_age,
            home_radius_km,
            movement_speed_threshold_kmh,
        )
        self.last_successful_update: datetime | None = None

    def profile(self, callsign: str) -> StationProfile:
        """Return the effective profile for a configured callsign."""
        return self.station_profiles[callsign]

    async def _async_update_data(self) -> dict[str, Position]:
        try:
            positions = await async_get_positions(
                self.session,
                self.api_key,
                self.callsigns,
            )
        except AprsFiAuthenticationError as err:
            raise ConfigEntryAuthFailed("The aprs.fi API key was rejected") from err
        except AprsFiRateLimitError as err:
            raise UpdateFailed(f"aprs.fi rate limit reached: {err}") from err
        except AprsFiError as err:
            raise UpdateFailed(f"Could not update aprs.fi: {err}") from err
        self.last_successful_update = datetime.now(UTC)
        return positions

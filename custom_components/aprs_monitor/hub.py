"""Shared APRS Monitor hub device helpers."""

from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, NAME

HUB_IDENTIFIER_PREFIX = "hub:"


def hub_device_info(entry_id: str) -> DeviceInfo:
    """Return the central integration device shared by hub entities."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{HUB_IDENTIFIER_PREFIX}{entry_id}")},
        name=NAME,
        manufacturer="APRS",
        model="aprs.fi monitor",
    )


def station_device_info(coordinator, callsign: str) -> DeviceInfo:
    """Return device information using the station's configured display name."""
    return DeviceInfo(
        identifiers={(DOMAIN, callsign)},
        name=f"APRS {coordinator.profile(callsign).display_name}",
        manufacturer="APRS",
        model="aprs.fi station",
        configuration_url=f"https://aprs.fi/{callsign}",
    )

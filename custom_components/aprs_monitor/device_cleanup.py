"""Pure device-registry cleanup decisions for APRS Monitor."""

from __future__ import annotations

from collections.abc import Iterable

from .const import DOMAIN

HUB_IDENTIFIER_PREFIX = "hub:"


def aprs_device_callsigns(identifiers: Iterable[tuple[str, str]]) -> set[str]:
    """Return APRS Monitor callsigns from device identifiers."""
    return {
        value
        for domain, value in identifiers
        if domain == DOMAIN and not value.startswith(HUB_IDENTIFIER_PREFIX)
    }


def should_remove_aprs_device(
    identifiers: Iterable[tuple[str, str]],
    configured_callsigns: Iterable[str],
) -> bool:
    """Return whether an APRS device is certainly no longer configured."""
    device_callsigns = aprs_device_callsigns(identifiers)
    return bool(device_callsigns) and device_callsigns.isdisjoint(configured_callsigns)

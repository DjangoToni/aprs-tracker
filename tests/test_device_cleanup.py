"""Tests for safe APRS device cleanup decisions."""

from custom_components.aprs_monitor.device_cleanup import (
    aprs_device_callsigns,
    should_remove_aprs_device,
)


def test_extracts_only_aprs_monitor_identifiers() -> None:
    identifiers = {
        ("aprs_monitor", "HB9ABC-7"),
        ("another_integration", "HB9XYZ"),
    }
    assert aprs_device_callsigns(identifiers) == {"HB9ABC-7"}


def test_hub_identifier_is_never_treated_as_a_removed_callsign() -> None:
    identifiers = {("aprs_monitor", "hub:entry-id")}
    assert aprs_device_callsigns(identifiers) == set()
    assert should_remove_aprs_device(identifiers, {"HB9ABC"}) is False


def test_removes_only_unconfigured_aprs_device() -> None:
    identifiers = {("aprs_monitor", "HB9OLD")}
    assert should_remove_aprs_device(identifiers, {"HB9ACTIVE"}) is True
    assert should_remove_aprs_device(identifiers, {"HB9OLD"}) is False


def test_never_removes_foreign_or_unidentified_device() -> None:
    assert should_remove_aprs_device({("another_integration", "HB9OLD")}, set()) is False
    assert should_remove_aprs_device(set(), set()) is False

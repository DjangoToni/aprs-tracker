"""Tests for local APRS callsign validation."""

from custom_components.aprs_monitor.validation import (
    normalize_callsigns,
    normalize_home_radius,
    normalize_max_position_age,
    normalize_movement_speed_threshold,
    normalize_update_interval,
)


def test_normalizes_and_deduplicates_callsigns() -> None:
    assert normalize_callsigns("hb9abc-7, HB9XYZ\nhb9abc-7") == ("HB9ABC-7", "HB9XYZ")


def test_rejects_wildcards_and_invalid_ssids() -> None:
    assert normalize_callsigns("HB9ABC*") == ()
    assert normalize_callsigns("HB9ABC-16") == ()


def test_rejects_empty_and_more_than_twenty_callsigns() -> None:
    assert normalize_callsigns("  ") == ()
    assert normalize_callsigns(",".join(f"HB{i:02d}" for i in range(21))) == ()


def test_accepts_update_interval_boundaries() -> None:
    assert normalize_update_interval(5) == 5
    assert normalize_update_interval("60") == 60


def test_rejects_invalid_update_intervals() -> None:
    assert normalize_update_interval(4) is None
    assert normalize_update_interval(61) is None
    assert normalize_update_interval("fast") is None


def test_validates_maximum_position_age() -> None:
    assert normalize_max_position_age(15) == 15
    assert normalize_max_position_age("1440") == 1440
    assert normalize_max_position_age(14) is None
    assert normalize_max_position_age(1441) is None


def test_validates_home_radius() -> None:
    assert normalize_home_radius(1) == 1.0
    assert normalize_home_radius("25.55") == 25.55
    assert normalize_home_radius(1000) == 1000.0
    assert normalize_home_radius(0.99) is None
    assert normalize_home_radius(1000.01) is None
    assert normalize_home_radius("near") is None


def test_validates_movement_speed_threshold() -> None:
    assert normalize_movement_speed_threshold(0.5) == 0.5
    assert normalize_movement_speed_threshold("2.25") == 2.25
    assert normalize_movement_speed_threshold(50) == 50.0
    assert normalize_movement_speed_threshold(0.49) is None
    assert normalize_movement_speed_threshold(50.01) is None
    assert normalize_movement_speed_threshold("fast") is None

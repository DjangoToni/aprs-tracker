"""Tests for APRS Monitor geographic calculations."""

import pytest

from custom_components.aprs_monitor.geo import (
    course_to_cardinal,
    great_circle_distance_km,
    initial_bearing_degrees,
)


def test_cardinal_distance_and_bearing() -> None:
    assert great_circle_distance_km(0, 0, 0, 1) == pytest.approx(111.195, abs=0.001)
    assert initial_bearing_degrees(0, 0, 0, 1) == pytest.approx(90)
    assert initial_bearing_degrees(0, 0, 1, 0) == pytest.approx(0)


def test_swiss_city_distance_and_bearing() -> None:
    distance = great_circle_distance_km(47.3769, 8.5417, 46.9480, 7.4474)
    bearing = initial_bearing_degrees(47.3769, 8.5417, 46.9480, 7.4474)
    assert distance == pytest.approx(95.4, abs=0.5)
    assert bearing == pytest.approx(240.5, abs=1)


def test_same_position_has_zero_distance_and_no_bearing() -> None:
    assert great_circle_distance_km(47.0, 8.0, 47.0, 8.0) == 0
    assert initial_bearing_degrees(47.0, 8.0, 47.0, 8.0) is None


def test_distance_uses_short_path_across_antimeridian() -> None:
    assert great_circle_distance_km(0, 179, 0, -179) == pytest.approx(222.39, abs=0.01)


@pytest.mark.parametrize(
    ("course", "direction"),
    [
        (0, "north"),
        (22.4, "north"),
        (22.5, "northeast"),
        (90, "east"),
        (123, "southeast"),
        (180, "south"),
        (270, "west"),
        (359.9, "north"),
        (360, "north"),
        (-90, "west"),
    ],
)
def test_course_to_cardinal(course: float, direction: str) -> None:
    assert course_to_cardinal(course) == direction


def test_missing_course_has_no_cardinal_direction() -> None:
    assert course_to_cardinal(None) is None

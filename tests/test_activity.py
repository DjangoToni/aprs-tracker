"""Tests for station activity snapshots and transitions."""

from datetime import UTC, datetime, timedelta

from custom_components.aprs_monitor.activity import (
    StationActivitySnapshot,
    activity_transitions,
    build_activity_snapshot,
)
from custom_components.aprs_monitor.api import Position


def test_snapshot_keeps_unknown_movement_distinct_from_stopped() -> None:
    position = Position(
        "HB9ABC",
        47.0,
        8.0,
        datetime.now(UTC),
        speed_kmh=None,
    )
    snapshot = build_activity_snapshot(position, 120, 1.0, 25.0, 47.0, 8.0)
    assert snapshot.status == "current"
    assert snapshot.moving is None
    assert snapshot.near_home is True


def test_stale_and_missing_positions_have_unknown_activity() -> None:
    stale = Position(
        "HB9ABC",
        47.0,
        8.0,
        datetime.now(UTC) - timedelta(minutes=121),
        speed_kmh=50.0,
    )
    assert build_activity_snapshot(stale, 120, 1.0, 25.0, 47.0, 8.0) == (
        StationActivitySnapshot("stale", None, None)
    )
    assert build_activity_snapshot(None, 120, 1.0, 25.0, 47.0, 8.0) == (
        StationActivitySnapshot("no_position", None, None)
    )


def test_emits_ordered_status_movement_and_radius_transitions() -> None:
    previous = StationActivitySnapshot("current", False, False)
    current = StationActivitySnapshot("current", True, True)
    assert activity_transitions(previous, current) == [
        "movement_started",
        "entered_home_radius",
    ]


def test_does_not_interpret_unknown_activity_as_a_transition() -> None:
    previous = StationActivitySnapshot("stale", None, None)
    current = StationActivitySnapshot("current", True, True)
    assert activity_transitions(previous, current) == ["position_current"]


def test_reports_stale_and_lost_positions() -> None:
    current = StationActivitySnapshot("current", True, False)
    stale = StationActivitySnapshot("stale", None, None)
    missing = StationActivitySnapshot("no_position", None, None)
    assert activity_transitions(current, stale) == ["position_stale"]
    assert activity_transitions(stale, missing) == ["position_lost"]

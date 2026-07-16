"""Tests for privacy-safe aggregate station health."""

from datetime import UTC, datetime, timedelta

from custom_components.aprs_monitor.api import Position
from custom_components.aprs_monitor.station_summary import build_station_summary


def test_summary_reports_ok_degraded_and_error() -> None:
    now = datetime.now(UTC)
    callsigns = ("A", "B", "C")
    current = Position("A", 47, 8, now)
    stale = Position("B", 47, 8, now - timedelta(minutes=121))
    ok = build_station_summary(callsigns, {key: current for key in callsigns}, 120, True)
    assert (ok.status, ok.current, ok.stale, ok.missing) == ("ok", 3, 0, 0)
    degraded = build_station_summary(callsigns, {"A": current, "B": stale}, 120, True)
    assert (degraded.status, degraded.current, degraded.stale, degraded.missing) == (
        "degraded",
        1,
        1,
        1,
    )
    assert build_station_summary(callsigns, {}, 120, True).status == "error"
    assert build_station_summary(callsigns, {"A": current}, 120, False).status == "error"

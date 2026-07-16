"""Tests for privacy-preserving diagnostics."""

import json
from datetime import UTC, datetime, timedelta

from custom_components.aprs_monitor.api import Position
from custom_components.aprs_monitor.diagnostics_data import build_station_diagnostics


def test_station_diagnostics_exclude_personal_and_location_data() -> None:
    now = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
    callsign = "HB9SECRET-7"
    position = Position(
        callsign=callsign,
        latitude=47.123456,
        longitude=8.654321,
        last_seen=now - timedelta(minutes=30),
        course=123.0,
        speed_kmh=45.6,
        altitude_m=789.0,
        symbol="/>",
        comment="PRIVATE COMMENT",
    )

    diagnostics = build_station_diagnostics(
        (callsign,),
        {callsign: position},
        max_position_age=120,
        now=now,
    )
    serialized = json.dumps(diagnostics)

    assert diagnostics[0]["station"] == "station_1"
    assert diagnostics[0]["position_age_minutes"] == 30
    assert diagnostics[0]["position_stale"] is False
    assert diagnostics[0]["fields_present"]["comment"] is True
    assert callsign not in serialized
    assert "47.123456" not in serialized
    assert "8.654321" not in serialized
    assert "PRIVATE COMMENT" not in serialized
    assert position.last_seen.isoformat() not in serialized


def test_station_diagnostics_report_missing_position_anonymously() -> None:
    diagnostics = build_station_diagnostics(("HB9SECRET",), {}, 120)
    assert diagnostics == [{"station": "station_1", "has_position": False}]

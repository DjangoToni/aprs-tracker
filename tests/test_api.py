"""Tests for aprs.fi response classification."""

from datetime import UTC, datetime, timedelta

import pytest

from custom_components.aprs_monitor.api import (
    AprsFiAuthenticationError,
    AprsFiError,
    AprsFiRateLimitError,
    Position,
    async_get_positions,
    is_position_stale,
    parse_positions,
    parse_retry_after,
    position_age_minutes,
    position_status,
    validate_api_response,
)


class _RateLimitedResponse:
    status = 429
    headers = {"Retry-After": "90"}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None


class _RateLimitedSession:
    def get(self, *args, **kwargs):
        return _RateLimitedResponse()


def test_accepts_success_response() -> None:
    validate_api_response({"result": "ok", "found": 0, "entries": []})


def test_classifies_invalid_api_key() -> None:
    with pytest.raises(AprsFiAuthenticationError):
        validate_api_response(
            {"result": "fail", "description": "authentication failed: wrong API key"}
        )


def test_classifies_other_api_failure() -> None:
    with pytest.raises(AprsFiError, match="rate limit"):
        validate_api_response({"result": "fail", "description": "rate limit exceeded"})


def test_rate_limit_error_preserves_retry_delay() -> None:
    error = AprsFiRateLimitError(120)
    assert error.retry_after_seconds == 120
    assert str(error) == "HTTP 429; retry after 120 seconds"
    assert parse_retry_after("60") == 60
    assert parse_retry_after("invalid") is None
    assert parse_retry_after(-1) is None


async def test_http_429_is_classified_without_json_parsing() -> None:
    with pytest.raises(AprsFiRateLimitError) as error:
        await async_get_positions(_RateLimitedSession(), "key", ("HB9ABC",))
    assert error.value.retry_after_seconds == 90


def test_parses_position() -> None:
    positions = parse_positions(
        {
            "entries": [
                {
                    "name": "HB9ABC-7",
                    "lat": "47.375",
                    "lng": "8.535",
                    "lasttime": "1783944000",
                    "course": "123",
                    "speed": "83.34",
                    "altitude": "457.2",
                    "symbol": "/>",
                    "comment": "Test",
                }
            ]
        }
    )
    position = positions["HB9ABC-7"]
    assert position.last_seen == datetime.fromtimestamp(1783944000, UTC)
    assert position.latitude == 47.375
    assert position.longitude == 8.535
    assert position.speed_kmh == 83.34


def test_ignores_invalid_position() -> None:
    assert parse_positions({"entries": {}}) == {}
    assert (
        parse_positions({"entries": [{"name": "BAD", "lat": "99", "lng": "8", "lasttime": "1"}]})
        == {}
    )


def test_position_freshness_uses_last_seen_timestamp() -> None:
    now = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
    position = Position("HB9ABC", 47.0, 8.0, now - timedelta(minutes=121))
    assert position_age_minutes(position, now) == 121
    assert is_position_stale(position, 120, now) is True


def test_position_is_fresh_at_limit_and_future_age_is_zero() -> None:
    now = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
    at_limit = Position("HB9ABC", 47.0, 8.0, now - timedelta(minutes=120))
    from_future = Position("HB9XYZ", 47.0, 8.0, now + timedelta(minutes=1))
    assert is_position_stale(at_limit, 120, now) is False
    assert position_age_minutes(from_future, now) == 0


def test_position_status_distinguishes_current_stale_and_missing() -> None:
    now = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
    current = Position("HB9ABC", 47.0, 8.0, now - timedelta(minutes=120))
    stale = Position("HB9XYZ", 47.0, 8.0, now - timedelta(minutes=121))
    assert position_status(current, 120, now) == "current"
    assert position_status(stale, 120, now) == "stale"
    assert position_status(None, 120, now) == "no_position"

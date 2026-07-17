"""Pure station-activity transition logic."""

from __future__ import annotations

from dataclasses import dataclass

from .api import Position, position_status
from .geo import great_circle_distance_km

EVENT_TYPES = [
    "position_current",
    "position_stale",
    "position_lost",
    "movement_started",
    "movement_stopped",
    "entered_home_radius",
    "left_home_radius",
    "entered_zone",
    "left_zone",
]


@dataclass(frozen=True)
class StationActivitySnapshot:
    """Values needed to detect meaningful station transitions."""

    status: str
    moving: bool | None
    near_home: bool | None
    zone_entity_id: str | None = None
    zone_name: str | None = None


def build_activity_snapshot(
    position: Position | None,
    max_position_age: int,
    movement_speed_threshold_kmh: float,
    home_radius_km: float,
    home_latitude: float,
    home_longitude: float,
) -> StationActivitySnapshot:
    """Build an activity snapshot without mistaking unknown data for false."""
    status = position_status(position, max_position_age)
    if position is None or status != "current":
        return StationActivitySnapshot(status, None, None)

    moving = (
        position.speed_kmh >= movement_speed_threshold_kmh
        if position.speed_kmh is not None
        else None
    )
    distance = great_circle_distance_km(
        home_latitude,
        home_longitude,
        position.latitude,
        position.longitude,
    )
    return StationActivitySnapshot(status, moving, distance <= home_radius_km)


def activity_transitions(
    previous: StationActivitySnapshot,
    current: StationActivitySnapshot,
) -> list[str]:
    """Return ordered event types for transitions between successful updates."""
    events: list[str] = []
    if previous.status != current.status:
        events.append(
            {
                "current": "position_current",
                "stale": "position_stale",
                "no_position": "position_lost",
            }[current.status]
        )

    if (
        previous.moving is not None
        and current.moving is not None
        and previous.moving != current.moving
    ):
        events.append("movement_started" if current.moving else "movement_stopped")

    if (
        previous.near_home is not None
        and current.near_home is not None
        and previous.near_home != current.near_home
    ):
        events.append(
            "entered_home_radius" if current.near_home else "left_home_radius"
        )

    if (
        previous.status == "current"
        and current.status == "current"
        and previous.zone_entity_id != current.zone_entity_id
    ):
        if previous.zone_entity_id is not None:
            events.append("left_zone")
        if current.zone_entity_id is not None:
            events.append("entered_zone")
    return events

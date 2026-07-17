"""Geographic calculations used by APRS Monitor entities."""

from __future__ import annotations

import math

EARTH_RADIUS_KM = 6371.0088
CARDINAL_DIRECTIONS = (
    "north",
    "northeast",
    "east",
    "southeast",
    "south",
    "southwest",
    "west",
    "northwest",
)
CARDINAL_ABBREVIATIONS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")


def course_to_cardinal(course: float | None) -> str | None:
    """Convert a course in degrees into an eight-point compass direction."""
    if course is None:
        return None
    normalized = course % 360
    return CARDINAL_DIRECTIONS[int((normalized + 22.5) // 45) % 8]


def course_to_cardinal_abbreviation(course: float | None) -> str | None:
    """Convert a course into a compact eight-point map abbreviation."""
    if course is None:
        return None
    normalized = course % 360
    return CARDINAL_ABBREVIATIONS[int((normalized + 22.5) // 45) % 8]


def great_circle_distance_km(
    origin_latitude: float,
    origin_longitude: float,
    target_latitude: float,
    target_longitude: float,
) -> float:
    """Return the shortest surface distance between two WGS84 coordinates."""
    origin_latitude_rad = math.radians(origin_latitude)
    target_latitude_rad = math.radians(target_latitude)
    latitude_delta = math.radians(target_latitude - origin_latitude)
    longitude_delta = math.radians(target_longitude - origin_longitude)

    haversine = (
        math.sin(latitude_delta / 2) ** 2
        + math.cos(origin_latitude_rad)
        * math.cos(target_latitude_rad)
        * math.sin(longitude_delta / 2) ** 2
    )
    central_angle = 2 * math.asin(math.sqrt(min(1.0, haversine)))
    return EARTH_RADIUS_KM * central_angle


def initial_bearing_degrees(
    origin_latitude: float,
    origin_longitude: float,
    target_latitude: float,
    target_longitude: float,
) -> float | None:
    """Return the initial bearing from origin to target, or None at the origin."""
    if origin_latitude == target_latitude and origin_longitude == target_longitude:
        return None

    origin_latitude_rad = math.radians(origin_latitude)
    target_latitude_rad = math.radians(target_latitude)
    longitude_delta = math.radians(target_longitude - origin_longitude)
    x = math.sin(longitude_delta) * math.cos(target_latitude_rad)
    y = (
        math.cos(origin_latitude_rad) * math.sin(target_latitude_rad)
        - math.sin(origin_latitude_rad)
        * math.cos(target_latitude_rad)
        * math.cos(longitude_delta)
    )
    return (math.degrees(math.atan2(x, y)) + 360) % 360

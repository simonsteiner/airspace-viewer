"""Arc interpolation utilities.

This module converts OpenAir arc segments (DA records) and arcs (DB records)
into sequences of points along the arc, so they can be rendered as part of
polygon geometries in GeoJSON or KML output.

All calculations use great-circle (spherical) geometry, which keeps arcs
accurate for the radii typically found in airspace definitions.
"""

import math
from typing import List, Tuple

from app.model.openair_types import Arc, ArcSegment, Point, PolygonSegment
from app.utils.units import nautical_miles_to_meters

EARTH_RADIUS_M = 6371000.0

# Angular resolution of interpolated arcs: one point every N degrees of sweep.
ARC_STEP_DEGREES = 5.0

LatLng = Tuple[float, float]

# Counterclockwise direction tokens: the normalized model value and the raw
# OpenAir record value ("V D=-")
CCW_TOKENS = {"CCW", "-"}


def _is_clockwise(direction: str) -> bool:
    """True unless the direction is a known counterclockwise token."""
    return direction.strip().upper() not in CCW_TOKENS


def _bearing_deg(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Initial great-circle bearing from point 1 to point 2.

    Args:
        lat1, lng1: Start point in decimal degrees.
        lat2, lng2: End point in decimal degrees.

    Returns:
        float: Bearing in degrees, normalized to [0, 360).
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lng2 - lng1)
    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(
        delta_lambda
    )
    return math.degrees(math.atan2(y, x)) % 360.0


def _distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine distance between two points in meters.

    Args:
        lat1, lng1: First point in decimal degrees.
        lat2, lng2: Second point in decimal degrees.

    Returns:
        float: Distance in meters.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def _destination(
    lat: float, lng: float, bearing_deg: float, distance_m: float
) -> LatLng:
    """Great-circle destination point given start, bearing, and distance.

    Args:
        lat, lng: Start point in decimal degrees.
        bearing_deg: Bearing in degrees.
        distance_m: Distance in meters.

    Returns:
        tuple: (lat, lng) of the destination point in decimal degrees.
    """
    delta = distance_m / EARTH_RADIUS_M
    theta = math.radians(bearing_deg)
    phi1 = math.radians(lat)
    lambda1 = math.radians(lng)
    phi2 = math.asin(
        math.sin(phi1) * math.cos(delta)
        + math.cos(phi1) * math.sin(delta) * math.cos(theta)
    )
    lambda2 = lambda1 + math.atan2(
        math.sin(theta) * math.sin(delta) * math.cos(phi1),
        math.cos(delta) - math.sin(phi1) * math.sin(phi2),
    )
    # Normalize longitude to [-180, 180) for arcs crossing the antimeridian
    lng2 = (math.degrees(lambda2) + 540.0) % 360.0 - 180.0
    return math.degrees(phi2), lng2


def _sweep_deg(angle_start: float, angle_end: float, clockwise: bool) -> float:
    """Signed angular sweep from start to end bearing in the given direction.

    Args:
        angle_start: Start bearing in degrees.
        angle_end: End bearing in degrees.
        clockwise: True for clockwise, False for counterclockwise.

    Returns:
        float: Signed sweep in degrees (positive = clockwise). A zero sweep is
            treated as a full circle.
    """
    if clockwise:
        sweep = (angle_end - angle_start) % 360.0
        return sweep if sweep != 0.0 else 360.0
    sweep = -((angle_start - angle_end) % 360.0)
    return sweep if sweep != 0.0 else -360.0


def interpolate_arc(arc: Arc) -> List[LatLng]:
    """Interpolate an arc (DB record) into points along the arc.

    The radius and start/end bearings are derived from the center, start, and
    end coordinates. Since start and end may lie at slightly different
    distances from the center, the radius is interpolated linearly along the
    sweep so the generated points connect both endpoints smoothly. The exact
    start and end coordinates are always included.

    Args:
        arc (Arc): The arc to interpolate.

    Returns:
        list: List of (lat, lng) tuples along the arc.
    """
    if arc.center is None or arc.start is None or arc.end is None:
        return []
    clockwise = _is_clockwise(arc.direction)
    radius_start = _distance_m(arc.center.lat, arc.center.lng, arc.start.lat, arc.start.lng)
    radius_end = _distance_m(arc.center.lat, arc.center.lng, arc.end.lat, arc.end.lng)
    angle_start = _bearing_deg(arc.center.lat, arc.center.lng, arc.start.lat, arc.start.lng)
    angle_end = _bearing_deg(arc.center.lat, arc.center.lng, arc.end.lat, arc.end.lng)
    sweep = _sweep_deg(angle_start, angle_end, clockwise)
    steps = max(2, math.ceil(abs(sweep) / ARC_STEP_DEGREES))

    points: List[LatLng] = [(arc.start.lat, arc.start.lng)]
    for i in range(1, steps):
        fraction = i / steps
        angle = angle_start + sweep * fraction
        radius = radius_start + (radius_end - radius_start) * fraction
        points.append(_destination(arc.center.lat, arc.center.lng, angle, radius))
    points.append((arc.end.lat, arc.end.lng))
    return points


def interpolate_arc_segment(segment: ArcSegment) -> List[LatLng]:
    """Interpolate an arc segment (DA record) into points along the arc.

    Args:
        segment (ArcSegment): The arc segment to interpolate. Radius is in
            nautical miles, angles are bearings from the center in degrees.

    Returns:
        list: List of (lat, lng) tuples along the arc.
    """
    if segment.center is None:
        return []
    clockwise = _is_clockwise(segment.direction)
    radius_m = nautical_miles_to_meters(segment.radius)
    sweep = _sweep_deg(segment.start_angle, segment.end_angle, clockwise)
    steps = max(2, math.ceil(abs(sweep) / ARC_STEP_DEGREES))
    return [
        _destination(
            segment.center.lat,
            segment.center.lng,
            segment.start_angle + sweep * i / steps,
            radius_m,
        )
        for i in range(steps + 1)
    ]


def segment_to_points(segment: PolygonSegment) -> List[LatLng]:
    """Convert any polygon segment into a list of (lat, lng) points.

    Args:
        segment (PolygonSegment): A Point, Arc, or ArcSegment.

    Returns:
        list: List of (lat, lng) tuples. Empty for unknown segment types.
    """
    if isinstance(segment, Point):
        return [(segment.lat, segment.lng)]
    if isinstance(segment, Arc):
        return interpolate_arc(segment)
    if isinstance(segment, ArcSegment):
        return interpolate_arc_segment(segment)
    return []

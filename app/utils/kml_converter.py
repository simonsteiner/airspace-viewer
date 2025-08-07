"""KML converter utilities.

This module provides utilities to convert airspace data structures into KML format for mapping and visualization.
It supports conversion of various airspace geometries (polygons, circles, lines) and includes helpers for altitude formatting.
"""

import math
from typing import Any, List

try:
    import simplekml  # type: ignore
except ImportError:
    simplekml = None  # Will raise in function if used without install

from app.model.openair_types import (
    Arc,
    ArcSegment,
    CircleGeometry,
    Point,
    PolygonGeometry,
)
from app.utils.airspace_colors import get_airspace_color
from app.utils.logging_utils import debug_log, error_log, info_log, warning_log
from app.utils.units import nautical_miles_to_meters


def altitude_to_text(altitude: Any) -> str:
    """Convert an altitude object or dictionary to a human-readable string."""
    from app.model.openair_types import Altitude, AltitudeType

    if isinstance(altitude, Altitude):
        return altitude.to_text()
    elif isinstance(altitude, dict):
        alt_type_str = altitude.get("type", "Gnd")
        try:
            alt_type = AltitudeType(alt_type_str)
        except ValueError:
            alt_type = AltitudeType.OTHER
        altitude_obj = Altitude(type=alt_type, val=altitude.get("val"))
        return altitude_obj.to_text()
    else:
        return str(altitude)


def convert_airspace_to_kml(airspaces: List[Any]) -> str:
    """Convert a list of airspace objects or dictionaries to a KML string."""
    if simplekml is None:
        raise ImportError(
            "simplekml is required for KML export. Please install it via pip."
        )
    kml = simplekml.Kml()
    info_log("kml_converter", f"Converting {len(airspaces)} airspaces to KML")
    for i, airspace_data in enumerate(airspaces):
        try:
            debug_log("kml_converter", f"Processing airspace {i+1}/{len(airspaces)}")
            if isinstance(airspace_data, dict):
                from app.model.openair_types import convert_raw_airspace

                airspace = convert_raw_airspace(airspace_data)
            else:
                airspace = airspace_data
            _add_kml_feature(kml, airspace)
        except Exception as e:
            _handle_conversion_error(airspace_data, e)
            continue
    return str(kml.kml())


def _add_kml_feature(kml, airspace: Any) -> None:
    name = airspace.name
    airspace_class = airspace.airspace_class
    lower_bound = altitude_to_text(airspace.lower_bound)
    upper_bound = altitude_to_text(airspace.upper_bound)
    description = (
        f"{name} ({airspace_class})\nLower: {lower_bound}\nUpper: {upper_bound}"
    )
    color = get_airspace_color(airspace_class)
    geom = airspace.geom
    if isinstance(geom, PolygonGeometry):
        _add_kml_polygon(kml, geom, name, description, color)
    elif isinstance(geom, CircleGeometry):
        _add_kml_circle(kml, geom, name, description, color)
    else:
        warning_log("kml_converter", f"Unknown geometry type: {type(geom)} - skipping")


def _add_kml_polygon(
    kml, geom: PolygonGeometry, name: str, description: str, color: str
) -> None:
    coordinates = []
    if geom.segments is not None:
        for segment in geom.segments:
            if isinstance(segment, Point):
                coordinates.append((segment.lng, segment.lat))
            elif isinstance(segment, (Arc, ArcSegment)):
                warning_log(
                    "kml_converter",
                    f"Skipping {type(segment).__name__} segment (not implemented)",
                )
            else:
                warning_log(
                    "kml_converter", f"Unknown segment type: {type(segment).__name__}"
                )
    if len(coordinates) > 2:
        if coordinates[0] != coordinates[-1]:
            coordinates.append(coordinates[0])
        pol = kml.newpolygon(
            name=name, description=description, outerboundaryis=coordinates
        )
        pol.style.polystyle.color = _hex_to_kml_color(color)
    elif len(coordinates) == 2:
        line = kml.newlinestring(name=name, description=description, coords=coordinates)
        line.style.linestyle.color = _hex_to_kml_color("#FF0000")
    else:
        error_log(
            "kml_converter",
            f"Polygon has insufficient points ({len(coordinates)} < 2 for line, < 3 for polygon)",
        )


def _add_kml_circle(
    kml, geom: CircleGeometry, name: str, description: str, color: str
) -> None:
    center_lat = center_lng = None
    if geom.centerpoint:
        if isinstance(geom.centerpoint, dict):
            center_lat = geom.centerpoint.get("lat")
            center_lng = geom.centerpoint.get("lng")
        elif isinstance(geom.centerpoint, list):
            center_lat = geom.centerpoint[0]
            center_lng = geom.centerpoint[1]
        elif hasattr(geom.centerpoint, "lat") and hasattr(geom.centerpoint, "lng"):
            center_lat = geom.centerpoint.lat
            center_lng = geom.centerpoint.lng
    if (
        center_lat is not None
        and center_lng is not None
        and isinstance(center_lat, (int, float))
        and isinstance(center_lng, (int, float))
        and geom.radius > 0
    ):
        radius_meters = nautical_miles_to_meters(geom.radius)
        radius_deg = radius_meters / 111320
        coordinates = []
        for i in range(36):
            angle = i * 10 * math.pi / 180
            lat = center_lat + radius_deg * math.cos(angle)
            lng = center_lng + radius_deg * math.sin(angle) / math.cos(
                math.radians(center_lat)
            )
            coordinates.append((lng, lat))
        coordinates.append(coordinates[0])
        pol = kml.newpolygon(
            name=name, description=description, outerboundaryis=coordinates
        )
        pol.style.polystyle.color = _hex_to_kml_color(color)
    else:
        error_log(
            "kml_converter",
            f"Invalid circle: centerpoint={geom.centerpoint}, radius={geom.radius}",
        )


def _hex_to_kml_color(hex_color: str) -> str:
    """Convert #RRGGBB or #AARRGGBB to KML aabbggrr format (default alpha=ff)."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 6:
        # #RRGGBB -> aabbggrr (alpha=ff)
        r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
        a = "ff"
    elif len(hex_color) == 8:
        # #AARRGGBB -> aabbggrr
        a, r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6], hex_color[6:8]
    else:
        return "ff0000ff"  # Default to opaque red
    # KML expects aabbggrr
    return f"{a}{b}{g}{r}"


def _handle_conversion_error(airspace_data: Any, error: Exception) -> None:
    if isinstance(airspace_data, dict):
        name = airspace_data.get("name", "Unknown")
        error_log("kml_converter", f"Error processing airspace {name}: {error}")
        error_log(
            "kml_converter", f"  Raw airspace data keys: {list(airspace_data.keys())}"
        )
    else:
        name = getattr(airspace_data, "name", "Unknown")
        error_log("kml_converter", f"Error processing airspace {name}: {error}")
        error_log("kml_converter", f"  Airspace object type: {type(airspace_data)}")
    import traceback

    error_log("kml_converter", f"  Traceback: {traceback.format_exc()}")

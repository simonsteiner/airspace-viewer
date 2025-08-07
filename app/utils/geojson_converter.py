"""GeoJSON converter utilities.

This module provides utilities to convert airspace data structures into GeoJSON format for mapping and visualization.
It supports conversion of various airspace geometries (polygons, circles, lines) and includes helpers for altitude formatting.
"""

import math
from typing import Any, Dict, List, Optional

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
    """Convert an altitude object or dictionary to a human-readable string.

    Args:
        altitude (Altitude | dict | any): The altitude object, dictionary, or value to convert.

    Returns:
        str: Human-readable altitude string.
    """
    from app.model.openair_types import Altitude, AltitudeType

    if isinstance(altitude, Altitude):
        return altitude.to_text()
    elif isinstance(altitude, dict):
        # Fallback for raw dictionary data - convert to Altitude object first
        alt_type_str = altitude.get("type", "Gnd")
        try:
            alt_type = AltitudeType(alt_type_str)
        except ValueError:
            alt_type = AltitudeType.OTHER
        altitude_obj = Altitude(type=alt_type, val=altitude.get("val"))
        return altitude_obj.to_text()
    else:
        return str(altitude)


def convert_airspace_to_geojson(airspaces: List[Any]) -> Dict[str, Any]:
    """Convert a list of airspace objects or dictionaries to a GeoJSON FeatureCollection.

    Args:
        airspaces (list): List of airspace objects or dictionaries.

    Returns:
        dict: GeoJSON FeatureCollection representing the airspaces.
    """
    features = []
    skipped_reasons: dict = {}

    info_log("geojson_converter", f"Converting {len(airspaces)} airspaces to GeoJSON")
    for i, airspace_data in enumerate(airspaces):
        try:
            # Debug: Print processing info
            debug_log(
                "geojson_converter", f"Processing airspace {i+1}/{len(airspaces)}"
            )

            # Convert raw data to typed Airspace object if needed
            if isinstance(airspace_data, dict):
                debug_log(
                    "geojson_converter",
                    f"  Converting raw dict data with keys: {list(airspace_data.keys())}",
                )
                from app.model.openair_types import convert_raw_airspace

                airspace = convert_raw_airspace(airspace_data)
            else:
                debug_log(
                    "geojson_converter",
                    f"  Using existing airspace object of type: {type(airspace_data)}",
                )
                airspace = airspace_data

            # Create feature from airspace
            feature = _create_geojson_feature(airspace)

            if feature["geometry"] is not None:
                debug_log(
                    "geojson_converter",
                    f"  ✓ Added feature '{airspace.name}' with {feature['geometry']['type']} geometry",
                )
                features.append(feature)
            else:
                error_log(
                    "geojson_converter",
                    f"  ✗ Skipped feature '{airspace.name}' - no valid geometry",
                )

        except Exception as e:
            _handle_conversion_error(airspace_data, e)
            continue

    # Print summary
    _print_conversion_summary(skipped_reasons, features)

    return {"type": "FeatureCollection", "features": features}


def _create_geojson_feature(airspace: Any) -> Dict[str, Any]:
    """Create a GeoJSON feature from an airspace object.

    Args:
        airspace: The airspace object to convert.

    Returns:
        dict: GeoJSON feature dictionary.
    """
    name = airspace.name
    airspace_class = airspace.airspace_class
    lower_bound = altitude_to_text(airspace.lower_bound)
    upper_bound = altitude_to_text(airspace.upper_bound)

    debug_log(
        "geojson_converter",
        f"  Successfully extracted properties: name='{name}', class='{airspace_class}'",
    )

    feature = {
        "type": "Feature",
        "properties": {
            "name": name,
            "class": airspace_class,
            "lowerBound": lower_bound,
            "upperBound": upper_bound,
            "description": f"{name} ({airspace_class})",
            "color": get_airspace_color(airspace_class),
        },
        "geometry": None,
    }

    # Process geometry
    geom = airspace.geom
    debug_log("geojson_converter", f"  Geometry type: {type(geom)}")

    if isinstance(geom, PolygonGeometry):
        feature["geometry"] = _process_polygon_geometry(geom, feature)
    elif isinstance(geom, CircleGeometry):
        feature["geometry"] = _process_circle_geometry(geom)
    else:
        warning_log(
            "geojson_converter", f"  Unknown geometry type: {type(geom)} - skipping"
        )

    return feature


def _process_polygon_geometry(
    geom: PolygonGeometry, feature: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Process a PolygonGeometry object and return a GeoJSON geometry.

    Args:
        geom (PolygonGeometry): The polygon geometry to process.
        feature (dict): The GeoJSON feature being constructed (for property updates).

    Returns:
        dict | None: GeoJSON geometry dictionary, or None if invalid.
    """
    segment_count = len(geom.segments) if geom.segments is not None else 0
    debug_log(
        "geojson_converter", f"  Processing polygon with {segment_count} segments"
    )

    coordinates = []
    if geom.segments is not None:
        for segment in geom.segments:
            if isinstance(segment, Point):
                coordinates.append(
                    [segment.lng, segment.lat]
                )  # GeoJSON uses [lon, lat]
            elif isinstance(segment, (Arc, ArcSegment)):
                # Log that we're skipping Arc/ArcSegment for now
                warning_log(
                    "geojson_converter",
                    f"    Skipping {type(segment).__name__} segment (not implemented)",
                )
            else:
                warning_log(
                    "geojson_converter",
                    f"    Unknown segment type: {type(segment).__name__}",
                )

    debug_log("geojson_converter", f"  Extracted {len(coordinates)} coordinate points")

    if len(coordinates) > 2:  # Need at least 3 points for a polygon
        # Close the polygon if not already closed
        if coordinates[0] != coordinates[-1]:
            coordinates.append(coordinates[0])
        return {"type": "Polygon", "coordinates": [coordinates]}

    elif len(coordinates) == 2:
        # Handle line obstacles (e.g., cables, power lines) as LineString
        debug_log("geojson_converter", "  ⚠ Converting 2-point polygon to LineString")

        # Update feature properties for line obstacle
        feature["properties"]["geometryType"] = "line"
        feature["properties"]["color"] = "#FF0000"  # Red color for obstacles
        feature["properties"]["description"] += " - Line Obstacle"

        return {"type": "LineString", "coordinates": coordinates}

    else:
        error_log(
            "geojson_converter",
            f"  ✗ Polygon has insufficient points ({len(coordinates)} < 2)",
        )
        return None


def _process_circle_geometry(geom: CircleGeometry) -> Optional[Dict[str, Any]]:
    """Process a CircleGeometry object and return a GeoJSON geometry.

    Args:
        geom (CircleGeometry): The circle geometry to process.

    Returns:
        dict | None: GeoJSON geometry dictionary, or None if invalid.
    """
    debug_log(
        "geojson_converter",
        f"  Processing circle with center {geom.centerpoint} and radius {geom.radius}",
    )

    center_lat = center_lng = None
    if geom.centerpoint:
        if isinstance(geom.centerpoint, dict):
            center_lat = geom.centerpoint.get("lat")
            center_lng = geom.centerpoint.get("lng")
        elif isinstance(geom.centerpoint, list):
            center_lat = geom.centerpoint[0]  # First element is latitude
            center_lng = geom.centerpoint[1]  # Second element is longitude
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
        # Convert nautical miles to degrees (more precise calculation)
        radius_meters = nautical_miles_to_meters(geom.radius)
        radius_deg = radius_meters / 111320  # meters per degree at equator

        # Create circle approximation with polygon (36 points)
        coordinates = []
        for i in range(36):  # 36 points for smooth circle
            angle = i * 10 * math.pi / 180  # 10 degrees apart
            lat = center_lat + radius_deg * math.cos(angle)
            lng = center_lng + radius_deg * math.sin(angle) / math.cos(
                math.radians(center_lat)
            )
            coordinates.append([lng, lat])

        # Close the circle
        coordinates.append(coordinates[0])
        debug_log(
            "geojson_converter",
            f"  ✓ Converted circle to polygon with {len(coordinates)} points",
        )
        return {"type": "Polygon", "coordinates": [coordinates]}
    else:
        error_log(
            "geojson_converter",
            f"  ✗ Invalid circle: centerpoint={geom.centerpoint}, radius={geom.radius}",
        )
        return None


def _handle_conversion_error(airspace_data: Any, error: Exception) -> None:
    """Handle and print errors that occur during airspace conversion.

    Args:
        airspace_data (object): The airspace data that caused the error.
        error (Exception): The exception that was raised.
    """
    if isinstance(airspace_data, dict):
        name = airspace_data.get("name", "Unknown")
        error_log("geojson_converter", f"Error processing airspace {name}: {error}")
        error_log(
            "geojson_converter",
            f"  Raw airspace data keys: {list(airspace_data.keys())}",
        )
    else:
        name = getattr(airspace_data, "name", "Unknown")
        error_log("geojson_converter", f"Error processing airspace {name}: {error}")
        error_log("geojson_converter", f"  Airspace object type: {type(airspace_data)}")

    error_log("geojson_converter", f"  Exception type: {type(error)}")
    import traceback

    error_log("geojson_converter", f"  Traceback: {traceback.format_exc()}")


def _print_conversion_summary(
    skipped_reasons: Dict[str, int],
    features: List[Dict[str, Any]],
) -> None:
    """Print a summary of the airspace conversion results, including skipped airspaces and line obstacles.

    Args:
        skipped_reasons (dict): Reasons and counts for skipped airspaces.
        features (list): List of successfully converted GeoJSON features.
    """
    if skipped_reasons:
        warning_log("geojson_converter", "\nSkipped airspaces summary:")
        for reason, count in skipped_reasons.items():
            warning_log("geojson_converter", f"  {reason}: {count} airspaces")
        total_skipped = sum(skipped_reasons.values())
        warning_log("geojson_converter", f"  Total skipped: {total_skipped}")
    else:
        info_log(
            "geojson_converter", "No airspaces were skipped due to geometry issues"
        )

    # Count converted line obstacles
    line_obstacles = sum(
        1 for f in features if f["properties"].get("geometryType") == "line"
    )
    if line_obstacles > 0:
        info_log(
            "geojson_converter",
            f"Converted {line_obstacles} 2-point polygons to LineString geometries (line obstacles)",
        )

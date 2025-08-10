"""KML converter utilities.

This module provides utilities to convert airspace data structures into KML format for mapping and visualization.
It supports conversion of various airspace geometries (polygons, circles, lines) and includes helpers for altitude formatting.
"""

import math
from typing import Any, List, Sequence, Tuple

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
from app.utils.units import feet_to_meters, nautical_miles_to_meters


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
        _add_kml_polygon_3d(kml, airspace, geom, name, description, color)
    elif isinstance(geom, CircleGeometry):
        _add_kml_circle_3d(kml, airspace, geom, name, description, color)
    else:
        warning_log("kml_converter", f"Unknown geometry type: {type(geom)} - skipping")


def _add_kml_polygon_3d(
    kml, airspace: Any, geom: PolygonGeometry, name: str, description: str, color: str
) -> None:
    """Create a 3D representation of a polygon airspace.

    If the lower bound is ground/AGL=0, we create a single polygon at the upper altitude
    and set extrude=1 so walls extend to the ground.

    If the lower bound is above ground, we build a MultiGeometry with a top face, a bottom
    face, and side walls (rectangular polygons for each edge) between lower and upper.
    """
    ring2d: List[Tuple[float, float]] = []
    if geom.segments is not None:
        for segment in geom.segments:
            if isinstance(segment, Point):
                ring2d.append((segment.lng, segment.lat))
            elif isinstance(segment, (Arc, ArcSegment)):
                warning_log(
                    "kml_converter",
                    f"Skipping {type(segment).__name__} segment (not implemented)",
                )
            else:
                warning_log(
                    "kml_converter",
                    f"Unknown segment type: {type(segment).__name__}",
                )

    if len(ring2d) < 2:
        error_log(
            "kml_converter",
            f"Polygon has insufficient points ({len(ring2d)} < 2 for line, < 3 for polygon)",
        )
        return

    # Close ring if needed
    if len(ring2d) >= 3 and ring2d[0] != ring2d[-1]:
        ring2d.append(ring2d[0])

    # Determine altitude parameters
    lower_mode, lower_m = _altitude_to_kml(airspace.lower_bound)
    upper_mode, upper_m = _altitude_to_kml(airspace.upper_bound)

    # If 2-point "polygon" -> treat as LineString obstacle (keep 2D but with extrude if useful)
    if len(ring2d) == 2:
        line = kml.newlinestring(name=name, description=description, coords=ring2d)
        line.style.linestyle.color = _hex_to_kml_color("#FF0000")
        return

    # Decide strategy
    lower_is_ground = _is_ground_lower(airspace.lower_bound)

    if lower_is_ground:
        # Single extruded polygon to ground at upper altitude
        coords_top = _ring_with_altitude(ring2d, upper_m)
        pol = kml.newpolygon(
            name=name, description=description, outerboundaryis=coords_top
        )
        pol.extrude = 1
        pol.altitudemode = upper_mode
        pol.style.polystyle.color = _hex_to_kml_color(color)
    else:
        # Build a MultiGeometry solid between lower and upper altitudes
        mg = kml.newmultigeometry(name=name, description=description)

        # Top face
        top_coords = _ring_with_altitude(ring2d, upper_m)
        top = mg.newpolygon(outerboundaryis=top_coords)
        top.altitudemode = upper_mode
        top.extrude = 0
        top.style.polystyle.color = _hex_to_kml_color(color)

        # Bottom face
        bottom_coords = _ring_with_altitude(ring2d, lower_m)
        bottom = mg.newpolygon(outerboundaryis=bottom_coords)
        bottom.altitudemode = lower_mode
        bottom.extrude = 0
        bottom.style.polystyle.color = _hex_to_kml_color(color)

        # Side walls for each edge in the ring
        edges = _iter_edges(ring2d)
        for (lon1, lat1), (lon2, lat2) in edges:
            wall_coords = [
                (lon1, lat1, lower_m),
                (lon2, lat2, lower_m),
                (lon2, lat2, upper_m),
                (lon1, lat1, upper_m),
                (lon1, lat1, lower_m),
            ]
            wall = mg.newpolygon(outerboundaryis=wall_coords)
            # Use the same mode as the top face (both faces are absolute or relative)
            wall.altitudemode = upper_mode
            wall.extrude = 0
            wall.style.polystyle.color = _hex_to_kml_color(color)


def _add_kml_circle_3d(
    kml, airspace: Any, geom: CircleGeometry, name: str, description: str, color: str
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
        coordinates: List[Tuple[float, float]] = []
        for i in range(36):
            angle = i * 10 * math.pi / 180
            lat = center_lat + radius_deg * math.cos(angle)
            lng = center_lng + radius_deg * math.sin(angle) / math.cos(
                math.radians(center_lat)
            )
            coordinates.append((lng, lat))
        if coordinates[0] != coordinates[-1]:
            coordinates.append(coordinates[0])

        lower_mode, lower_m = _altitude_to_kml(airspace.lower_bound)
        upper_mode, upper_m = _altitude_to_kml(airspace.upper_bound)
        lower_is_ground = _is_ground_lower(airspace.lower_bound)

        if lower_is_ground:
            coords_top = _ring_with_altitude(coordinates, upper_m)
            pol = kml.newpolygon(
                name=name, description=description, outerboundaryis=coords_top
            )
            pol.extrude = 1
            pol.altitudemode = upper_mode
            pol.style.polystyle.color = _hex_to_kml_color(color)
        else:
            mg = kml.newmultigeometry(name=name, description=description)

            # Top and bottom
            top = mg.newpolygon(
                outerboundaryis=_ring_with_altitude(coordinates, upper_m)
            )
            top.altitudemode = upper_mode
            top.style.polystyle.color = _hex_to_kml_color(color)
            bottom = mg.newpolygon(
                outerboundaryis=_ring_with_altitude(coordinates, lower_m)
            )
            bottom.altitudemode = lower_mode
            bottom.style.polystyle.color = _hex_to_kml_color(color)

            # Side walls
            for (lon1, lat1), (lon2, lat2) in _iter_edges(coordinates):
                wall_coords = [
                    (lon1, lat1, lower_m),
                    (lon2, lat2, lower_m),
                    (lon2, lat2, upper_m),
                    (lon1, lat1, upper_m),
                    (lon1, lat1, lower_m),
                ]
                wall = mg.newpolygon(outerboundaryis=wall_coords)
                wall.altitudemode = upper_mode
                wall.extrude = 0
                wall.style.polystyle.color = _hex_to_kml_color(color)
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


# -------------------------- Altitude helpers (3D) ---------------------------


def _altitude_to_kml(altitude: Any) -> Tuple[str, float]:
    """Return (altitudeMode, meters) for a given Altitude.

    - GND => (simplekml.AltitudeMode.relativetoground, 0.0)
    - FEET_AMSL => (simplekml.AltitudeMode.absolute, meters)
    - FEET_AGL => (simplekml.AltitudeMode.relativetoground, meters)
    - FLIGHT_LEVEL => (simplekml.AltitudeMode.absolute, meters_from_FL)
    - UNLIMITED => (simplekml.AltitudeMode.absolute, VERY_HIGH_ALT)
    - OTHER/unknown => (simplekml.AltitudeMode.absolute, 0.0)
    """
    from app.model.openair_types import Altitude as OAAltitude

    VERY_HIGH_ALT = 60000.0  # meters: visualization only

    if isinstance(altitude, OAAltitude):
        alt_type = altitude.type
        val = altitude.val
    elif isinstance(altitude, dict):
        try:
            from app.model.openair_types import AltitudeType as AT

            alt_type = AT(altitude.get("type", "Gnd"))
        except Exception:
            from app.model.openair_types import AltitudeType as AT

            alt_type = AT.OTHER
        val = altitude.get("val")
    else:
        # Unknown object, assume ground
        from app.model.openair_types import AltitudeType as AT

        alt_type = AT.GND
        val = 0

    if alt_type.name in ("GND",):
        return "relativeToGround", 0.0
    if alt_type.name == "FEET_AMSL":
        meters = float(feet_to_meters(_to_float_safe(val)))
        return "absolute", meters
    if alt_type.name == "FEET_AGL":
        meters = float(feet_to_meters(_to_float_safe(val)))
        return "relativeToGround", meters
    if alt_type.name == "FLIGHT_LEVEL":
        # FL is hundreds of feet (e.g. FL75 => 7500 ft)
        fl = _to_float_safe(val)
        meters = float(feet_to_meters(fl * 100.0))
        return "absolute", meters
    if alt_type.name == "UNLIMITED":
        return "absolute", VERY_HIGH_ALT
    # OTHER/unknown
    return "absolute", 0.0


def _is_ground_lower(altitude: Any) -> bool:
    """True if lower bound effectively touches ground (for extrude-to-ground)."""
    from app.model.openair_types import Altitude as OAAltitude
    from app.model.openair_types import AltitudeType

    if isinstance(altitude, OAAltitude):
        if altitude.type == AltitudeType.GND:
            return True
        if altitude.type == AltitudeType.FEET_AGL:
            try:
                return float(_to_float_safe(altitude.val)) <= 0.0
            except Exception:
                return True
        return False
    if isinstance(altitude, dict):
        try:
            t = AltitudeType(altitude.get("type", "Gnd"))  # type: ignore[name-defined]
        except Exception:
            return False
        if t == AltitudeType.GND:
            return True
        if t == AltitudeType.FEET_AGL:
            try:
                return float(_to_float_safe(altitude.get("val"))) <= 0.0
            except Exception:
                return True
        return False
    return True


def _ring_with_altitude(
    ring2d: Sequence[Tuple[float, float]], altitude_m: float
) -> List[Tuple[float, float, float]]:
    return [(lon, lat, float(altitude_m)) for lon, lat in ring2d]


def _iter_edges(
    ring2d: Sequence[Tuple[float, float]],
) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
    edges: List[Tuple[Tuple[float, float], Tuple[float, float]]] = []
    if len(ring2d) < 2:
        return edges
    for i in range(len(ring2d) - 1):
        edges.append((ring2d[i], ring2d[i + 1]))
    return edges


def _to_float_safe(val: Any) -> float:
    try:
        if val is None:
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        return float(str(val).strip())
    except Exception:
        return 0.0


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

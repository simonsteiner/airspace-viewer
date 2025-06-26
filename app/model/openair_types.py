"""
Airspace data structures
This module defines the data structures used for airspace representation.
"""

from dataclasses import dataclass
from typing import Union, List, Dict, Any
from enum import Enum


class AltitudeType(Enum):
    """Altitude reference types."""

    GND = "Gnd"
    FEET_AMSL = "FeetAmsl"
    FEET_AGL = "FeetAgl"
    FLIGHT_LEVEL = "FlightLevel"
    UNLIMITED = "Unlimited"
    OTHER = "Other"


@dataclass
class Altitude:
    """Represents an altitude with its reference type."""

    type: AltitudeType
    val: Union[int, float, str, None] = None

    def to_text(self) -> str:
        """Convert altitude to human-readable text."""
        from utils.units import feet_to_meters

        if self.type == AltitudeType.GND:
            return "GND"
        elif self.type == AltitudeType.FEET_AMSL:
            meters = int(feet_to_meters(self.val)) if self.val else 0
            return f"{meters} m AMSL"
        elif self.type == AltitudeType.FEET_AGL:
            meters = int(feet_to_meters(self.val)) if self.val else 0
            return f"{meters} m AGL"
        elif self.type == AltitudeType.FLIGHT_LEVEL:
            return f"FL {self.val}"
        elif self.type == AltitudeType.UNLIMITED:
            return "Unlimited"
        elif self.type == AltitudeType.OTHER:
            return f"?({self.val})"
        else:
            return str(self.val) if self.val else "Unknown"


@dataclass
class Point:
    """Represents a geographical point."""

    type: str = "Point"
    lat: float = 0.0
    lng: float = 0.0


@dataclass
class Arc:
    """Represents an arc segment."""

    type: str = "Arc"
    center: Point = None
    start: Point = None
    end: Point = None
    direction: str = "CW"  # CW or CCW


@dataclass
class ArcSegment:
    """Represents an arc segment with radius."""

    type: str = "ArcSegment"
    center: Point = None
    radius: float = 0.0
    start_angle: float = 0.0
    end_angle: float = 0.0
    direction: str = "CW"


# Union type for polygon segments
PolygonSegment = Union[Point, Arc, ArcSegment]


@dataclass
class PolygonGeometry:
    """Represents polygon geometry."""

    type: str = "Polygon"
    segments: List[PolygonSegment] = None

    def __post_init__(self):
        if self.segments is None:
            self.segments = []


@dataclass
class CircleGeometry:
    """Represents circle geometry."""

    type: str = "Circle"
    centerpoint: List[float] = None  # [lat, lng]
    radius: float = 0.0  # in nautical miles

    def __post_init__(self):
        if self.centerpoint is None:
            self.centerpoint = [0.0, 0.0]


# Union type for geometries
AirspaceGeometry = Union[PolygonGeometry, CircleGeometry]


@dataclass
class Airspace:
    """Represents an airspace."""

    name: str = ""
    class_: str = ""  # Using class_ to avoid Python keyword conflict
    lower_bound: Altitude = None
    upper_bound: Altitude = None
    geom: AirspaceGeometry = None

    def __post_init__(self):
        if self.lower_bound is None:
            self.lower_bound = Altitude(AltitudeType.GND)
        if self.upper_bound is None:
            self.upper_bound = Altitude(AltitudeType.UNLIMITED)

    @property
    def airspace_class(self) -> str:
        """Get the airspace class."""
        return self.class_

    def set_airspace_class(self, value: str):
        """Set the airspace class."""
        self.class_ = value


def convert_raw_airspace(raw_data: Dict[str, Any]) -> Airspace:
    """Convert raw dictionary data to Airspace object."""

    # Parse altitude
    def parse_altitude(alt_data) -> Altitude:
        if isinstance(alt_data, dict):
            alt_type_str = alt_data.get("type", "Gnd")
            try:
                alt_type = AltitudeType(alt_type_str)
            except ValueError:
                alt_type = AltitudeType.OTHER
            return Altitude(type=alt_type, val=alt_data.get("val"))
        return Altitude(AltitudeType.GND)

    # Parse geometry
    def parse_geometry(geom_data) -> AirspaceGeometry:
        if not isinstance(geom_data, dict):
            return PolygonGeometry()

        geom_type = geom_data.get("type", "Polygon")

        if geom_type == "Circle":
            return CircleGeometry(
                type=geom_type,
                centerpoint=geom_data.get("centerpoint", [0.0, 0.0]),
                radius=geom_data.get("radius", 0.0),
            )
        else:  # Polygon
            segments = []
            for seg_data in geom_data.get("segments", []):
                if isinstance(seg_data, dict):
                    seg_type = seg_data.get("type", "Point")
                    if seg_type == "Point":
                        segments.append(
                            Point(
                                type=seg_type,
                                lat=seg_data.get("lat", 0.0),
                                lng=seg_data.get("lng", 0.0),
                            )
                        )
                    # Add Arc and ArcSegment parsing as needed

            return PolygonGeometry(type=geom_type, segments=segments)

    return Airspace(
        name=raw_data.get("name", ""),
        class_=raw_data.get("class", ""),
        lower_bound=parse_altitude(raw_data.get("lowerBound", {})),
        upper_bound=parse_altitude(raw_data.get("upperBound", {})),
        geom=parse_geometry(raw_data.get("geom", {})),
    )

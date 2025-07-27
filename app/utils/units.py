"""
Units conversion utilities
"""

from typing import Union

Number = Union[int, float]


def feet_to_meters(feet: Number) -> float:
    """Convert feet to meters."""
    return float(feet) * 0.3048


def meters_to_feet(meters: Number) -> float:
    """Convert meters to feet."""
    return float(meters) / 0.3048


def nautical_miles_to_meters(nm: Number) -> float:
    """Convert nautical miles to meters."""
    return float(nm) * 1852


def meters_to_nautical_miles(meters: Number) -> float:
    """Convert meters to nautical miles."""
    return float(meters) / 1852


def statute_miles_to_meters(miles: Number) -> float:
    """Convert statute miles to meters."""
    return float(miles) * 1609.344


def meters_to_statute_miles(meters: Number) -> float:
    """Convert meters to statute miles."""
    return float(meters) / 1609.344


def kilometers_to_meters(km: Number) -> float:
    """Convert kilometers to meters."""
    return float(km) * 1000


def meters_to_kilometers(meters: Number) -> float:
    """Convert meters to kilometers."""
    return float(meters) / 1000

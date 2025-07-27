"""Units conversion utilities.

This module provides functions for converting between various units commonly used in aviation and mapping, such as feet, meters, nautical miles, statute miles, and kilometers.

Functions:
    feet_to_meters(feet): Convert feet to meters.
    meters_to_feet(meters): Convert meters to feet.
    nautical_miles_to_meters(nm): Convert nautical miles to meters.
    meters_to_nautical_miles(meters): Convert meters to nautical miles.
    statute_miles_to_meters(miles): Convert statute miles to meters.
    meters_to_statute_miles(meters): Convert meters to statute miles.
    kilometers_to_meters(km): Convert kilometers to meters.
    meters_to_kilometers(meters): Convert meters to kilometers.
"""

from typing import Union

Number = Union[int, float]


def feet_to_meters(feet: Number) -> float:
    """Convert feet to meters.

    Args:
        feet (int | float): The value in feet.

    Returns:
        float: The value converted to meters.
    """
    return float(feet) * 0.3048


def meters_to_feet(meters: Number) -> float:
    """Convert meters to feet.

    Args:
        meters (int | float): The value in meters.

    Returns:
        float: The value converted to feet.
    """
    return float(meters) / 0.3048


def nautical_miles_to_meters(nm: Number) -> float:
    """Convert nautical miles to meters.

    Args:
        nm (int | float): The value in nautical miles.

    Returns:
        float: The value converted to meters.
    """
    return float(nm) * 1852


def meters_to_nautical_miles(meters: Number) -> float:
    """Convert meters to nautical miles.

    Args:
        meters (int | float): The value in meters.

    Returns:
        float: The value converted to nautical miles.
    """
    return float(meters) / 1852


def statute_miles_to_meters(miles: Number) -> float:
    """Convert statute miles to meters.

    Args:
        miles (int | float): The value in statute miles.

    Returns:
        float: The value converted to meters.
    """
    return float(miles) * 1609.344


def meters_to_statute_miles(meters: Number) -> float:
    """Convert meters to statute miles.

    Args:
        meters (int | float): The value in meters.

    Returns:
        float: The value converted to statute miles.
    """
    return float(meters) / 1609.344


def kilometers_to_meters(km: Number) -> float:
    """Convert kilometers to meters.

    Args:
        km (int | float): The value in kilometers.

    Returns:
        float: The value converted to meters.
    """
    return float(km) * 1000


def meters_to_kilometers(meters: Number) -> float:
    """Convert meters to kilometers.

    Args:
        meters (int | float): The value in meters.

    Returns:
        float: The value converted to kilometers.
    """
    return float(meters) / 1000

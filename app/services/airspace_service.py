"""Airspace Service Module.

Provides the `AirspaceService` class for managing, loading, and converting airspace data.

This module handles parsing OpenAir files, converting them to typed airspace objects, and generating GeoJSON for web display.
It also provides a global service instance and helper functions for use in a Flask application.
"""

import os
from typing import Any, Dict, List, Optional, Tuple

from openair import parse_file

from app.model.openair_types import convert_raw_airspace
from app.utils.file_utils import get_default_airspace_path
from app.utils.geojson_converter import convert_airspace_to_geojson
from app.utils.logging_utils import debug_log, info_log


class AirspaceService:
    """Service for managing airspace data.

    This class loads, parses, and caches airspace data from OpenAir files, converts them to typed objects,
    and generates GeoJSON for web display. It also provides statistics and debug information.
    """

    verbose: bool
    _cached_airspaces: Optional[List[Any]]
    _cached_geojson: Optional[Dict[str, Any]]
    _current_filename: Optional[str]

    def __init__(self, verbose: bool = False) -> None:
        """Initialize the AirspaceService.

        Args:
            verbose (bool): If True, enables verbose debug output.
        """
        self.verbose = verbose
        self._cached_airspaces = None
        self._cached_geojson = None
        self._current_filename = None

    def load_airspace_data(
        self, filepath: Optional[str] = None
    ) -> Tuple[Optional[List[Any]], Optional[Dict[str, Any]]]:
        """Load and process airspace data from a file.

        Args:
            filepath (str, optional): Path to the OpenAir file. If None, uses the default Switzerland file.

        Returns:
            tuple: (list of Airspace objects, GeoJSON dict)
        """
        # Use provided filepath or default Switzerland file
        if filepath is None:
            filepath = get_default_airspace_path()
        debug_log(
            "airspace_service", f"load_airspace_data called with filepath: {filepath}"
        )

        # Only reload if filepath changed or no data cached, and the file exists
        if (
            self._cached_airspaces is None or self._current_filename != filepath
        ) and os.path.exists(filepath):

            try:
                info_log("airspace_service", f"Loading airspace data from: {filepath}")

                # Use the openair library to parse the file (returns raw dictionary data)
                raw_airspaces = parse_file(filepath)
                debug_log(
                    "airspace_service",
                    f"Parsed {len(raw_airspaces)} raw airspaces from file: {filepath}",
                )

                # Convert raw data to typed Airspace objects
                self._cached_airspaces = [
                    convert_raw_airspace(raw_data) for raw_data in raw_airspaces
                ]
                debug_log(
                    "airspace_service",
                    f"Converted to {len(self._cached_airspaces)} typed airspaces.",
                )
                self._current_filename = filepath

                # Convert to GeoJSON for web display
                self._cached_geojson = convert_airspace_to_geojson(
                    self._cached_airspaces
                )

                info_log(
                    "airspace_service",
                    f"Loaded {len(self._cached_airspaces)} airspaces from {os.path.basename(filepath)}",
                )
                info_log(
                    "airspace_service",
                    f"Generated {len(self._cached_geojson['features'])} GeoJSON features",
                )

                # Debug: Print first airspace structure
                if self.verbose and self._cached_airspaces:
                    self._print_debug_info()

            except Exception as e:
                info_log("airspace_service", f"Error loading airspace data: {e}")
                import traceback

                traceback.print_exc()
                self._cached_airspaces = []
                self._cached_geojson = {"type": "FeatureCollection", "features": []}
                self._current_filename = None

        elif not os.path.exists(filepath):
            info_log("airspace_service", f"File does not exist: {filepath}")
            # If the cached file doesn't exist, reset to default
            if filepath != get_default_airspace_path():
                return self.load_airspace_data()  # Recursive call with default file

        return self._cached_airspaces, self._cached_geojson

    def load_from_uploaded_file(
        self, filepath: str, original_filename: str
    ) -> Tuple[bool, Optional[str]]:
        """Load airspace data from an uploaded file.

        Args:
            filepath (str): Path to the uploaded file.
            original_filename (str): Original filename for display purposes.

        Returns:
            tuple: (bool, str or None). True and None if successful, False and error message if failed.
        """
        try:
            info_log(
                "airspace_service",
                f"Loading airspace data from uploaded file: {filepath}",
            )
            raw_airspaces = parse_file(filepath)

            # Convert raw data to typed Airspace objects
            self._cached_airspaces = [
                convert_raw_airspace(raw_data) for raw_data in raw_airspaces
            ]

            # Convert to GeoJSON for web display
            self._cached_geojson = convert_airspace_to_geojson(self._cached_airspaces)

            # Set current filename to the original filename for display
            self._current_filename = original_filename

            info_log(
                "airspace_service",
                f"Loaded {len(self._cached_airspaces)} airspaces from {original_filename}",
            )
            info_log(
                "airspace_service",
                f"Generated {len(self._cached_geojson['features'])} GeoJSON features",
            )

            return True, None

        except Exception as e:
            info_log("airspace_service", f"Error parsing uploaded file: {e}")
            import traceback

            traceback.print_exc()
            return False, str(e)

    def reset_to_default(self) -> None:
        """Reset the service to use the default airspace data."""
        self._cached_airspaces = None
        self._cached_geojson = None
        self._current_filename = None

    def get_cached_data(self) -> Tuple[Optional[List[Any]], Optional[Dict[str, Any]]]:
        """Get currently cached airspace and GeoJSON data.

        Returns:
            tuple: (list of Airspace objects, GeoJSON dict)
        """
        debug_log(
            "airspace_service",
            f"get_cached_data called. Cached airspaces: {len(self._cached_airspaces) if self._cached_airspaces else 0}",
        )
        if self._cached_airspaces is not None and self._cached_geojson is not None:
            return self._cached_airspaces, self._cached_geojson
        else:
            debug_log("airspace_service", "Cache is empty, loading airspace data.")
            return self.load_airspace_data()

    def get_current_filename(self) -> str:
        """Get the current filename being displayed.

        Returns:
            str: The base name of the current file, or the default example filename.
        """
        return (
            os.path.basename(self._current_filename)
            if self._current_filename
            else "examples/Switzerland.txt"
        )

    def export_to_kml(self, filepath: Optional[str] = None) -> str:
        """Export loaded airspaces to a KML file using the kml_converter utility.

        Args:
            filepath (str, optional): Path to save the KML file. If None, returns KML as string.

        Returns:
            str: The KML as a string (if filepath is None), otherwise the filepath.
        """
        from app.utils.kml_converter import convert_airspace_to_kml

        airspaces, _ = self.get_cached_data()
        if not airspaces:
            airspaces, _ = self.load_airspace_data()
            if not airspaces:
                raise ValueError("No airspaces loaded to export.")

        kml_str = convert_airspace_to_kml(airspaces)

        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(kml_str)
            return filepath
        else:
            return kml_str

    def get_airspace_stats(self) -> Dict[str, Any]:
        """Get statistics about the loaded airspaces.

        Returns:
            dict: Dictionary with total airspaces and counts by class.
        """
        from typing import Any, Dict

        airspaces, _ = self.get_cached_data()

        # Handle None case
        if airspaces is None:
            return {"total_airspaces": 0, "classes": {}}

        # Count airspaces by class using typed objects
        class_counts: Dict[Any, int] = {}
        for airspace in airspaces:
            airspace_class = airspace.airspace_class
            class_counts[airspace_class] = class_counts.get(airspace_class, 0) + 1

        return {"total_airspaces": len(airspaces), "classes": class_counts}

    def _print_debug_info(self) -> None:
        """Print debug information about the first airspace object in the cache."""
        debug_log("airspace_service", "First airspace structure:")
        if self._cached_airspaces and len(self._cached_airspaces) > 0:
            first_airspace = self._cached_airspaces[0]
            debug_log(
                "airspace_service", f"Name: {getattr(first_airspace, 'name', 'N/A')}"
            )
            debug_log(
                "airspace_service",
                f"Class: {getattr(first_airspace, 'airspace_class', 'N/A')}",
            )
            lower = getattr(first_airspace, "lower_bound", None)
            upper = getattr(first_airspace, "upper_bound", None)
            debug_log(
                "airspace_service", f"Lower: {lower.to_text() if lower else 'N/A'}"
            )
            debug_log(
                "airspace_service", f"Upper: {upper.to_text() if upper else 'N/A'}"
            )
            geom = getattr(first_airspace, "geom", None)
            debug_log(
                "airspace_service",
                f"Geometry type: {type(geom).__name__ if geom else 'N/A'}",
            )
        else:
            info_log("airspace_service", "No airspace data available.")


# Global service instance
airspace_service = None


def get_airspace_service() -> AirspaceService:
    """Get the global airspace service instance for use in a Flask app.

    Returns:
        AirspaceService: The global AirspaceService instance.
    """
    global airspace_service
    if airspace_service is None:
        from flask import current_app

        verbose = current_app.config.get("VERBOSE", True)
        debug_log("airspace_service", "Creating new AirspaceService instance.")
        airspace_service = AirspaceService(verbose=verbose)
    else:
        debug_log("airspace_service", "Reusing existing AirspaceService instance.")
    return airspace_service

#!/usr/bin/env python3

import os
import json
import math
from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
import tempfile

# Import the openair library as shown in your integration example
from openair import parse_file

# Import local modules
from units import feet_to_meters, nautical_miles_to_meters
from openair_types import (
    Airspace,
    Altitude,
    AltitudeType,
    Point,
    Arc,
    ArcSegment,
    PolygonGeometry,
    CircleGeometry,
    convert_raw_airspace,
)
from airspace_colors import (
    get_airspace_color,
    get_legend_data,
    generate_javascript_colors,
    generate_complete_css,
)

app = Flask(__name__)

# Configure Flask secret key for sessions (required for flash messages)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "fallback-dev-key")

# Configure upload settings
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {"txt", "air", "openair"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# Global variable to cache parsed airspaces
_cached_airspaces = None
_cached_geojson = None
_current_filename = None

# Debug flag - set to True for detailed processing output
VERBOSE = False


def allowed_file(filename):
    """Check if uploaded file has allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def altitude_to_text(altitude):
    """Convert altitude object to human-readable text, using typed Altitude objects."""
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


def get_airspace_color(airspace_class):
    """Get color for airspace class - imported from airspace_colors module."""
    from airspace_colors import get_airspace_color as get_color

    return get_color(airspace_class)


def convert_airspace_to_geojson(airspaces):
    """Convert airspace data to GeoJSON format for mapping."""
    features = []
    skipped_reasons = {}

    for i, airspace_data in enumerate(airspaces):
        try:
            # Debug: Print processing info
            if VERBOSE:
                print(f"Processing airspace {i+1}/{len(airspaces)}")

            # Convert raw data to typed Airspace object if needed
            if isinstance(airspace_data, dict):
                if VERBOSE:
                    print(
                        f"  Converting raw dict data with keys: {list(airspace_data.keys())}"
                    )
                airspace = convert_raw_airspace(airspace_data)
            else:
                if VERBOSE:
                    print(
                        f"  Using existing airspace object of type: {type(airspace_data)}"
                    )
                airspace = airspace_data

            # Extract airspace properties using typed objects
            name = airspace.name
            airspace_class = airspace.airspace_class
            lower_bound = altitude_to_text(airspace.lower_bound)
            upper_bound = altitude_to_text(airspace.upper_bound)

            if VERBOSE:
                print(
                    f"  Successfully extracted properties: name='{name}', class='{airspace_class}'"
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

            geom = airspace.geom
            if VERBOSE:
                print(f"  Geometry type: {type(geom)}")

            if isinstance(geom, PolygonGeometry):
                # Handle polygon geometry using typed objects
                if VERBOSE:
                    print(f"  Processing polygon with {len(geom.segments)} segments")
                coordinates = []

                for segment in geom.segments:
                    if isinstance(segment, Point):
                        coordinates.append(
                            [segment.lng, segment.lat]
                        )  # GeoJSON uses [lon, lat]
                    elif isinstance(segment, (Arc, ArcSegment)):
                        # Log that we're skipping Arc/ArcSegment for now
                        print(
                            f"    Skipping {type(segment).__name__} segment (not implemented)"
                        )
                    else:
                        print(f"    Unknown segment type: {type(segment).__name__}")

                if VERBOSE:
                    print(f"  Extracted {len(coordinates)} coordinate points")
                if len(coordinates) > 2:  # Need at least 3 points for a polygon
                    # Close the polygon if not already closed
                    if coordinates[0] != coordinates[-1]:
                        coordinates.append(coordinates[0])

                    feature["geometry"] = {
                        "type": "Polygon",
                        "coordinates": [coordinates],
                    }
                elif len(coordinates) == 2:
                    # Handle line obstacles (e.g., cables, power lines) as LineString
                    if VERBOSE:
                        print(
                            f"  ⚠ Converting 2-point polygon to LineString: '{name}' ({airspace_class})"
                        )
                        print(f"  Coordinates: {coordinates}")

                    feature["geometry"] = {
                        "type": "LineString",
                        "coordinates": coordinates,
                    }

                    # Update properties to indicate this is a line obstacle
                    feature["properties"]["geometryType"] = "line"
                    # Red color for obstacles
                    feature["properties"]["color"] = "#FF0000"
                    feature["properties"][
                        "description"
                    ] = f"{name} ({airspace_class}) - Line Obstacle"
                else:
                    print(
                        f"  ✗ Polygon has insufficient points ({len(coordinates)} < 2)"
                    )
                    print(f"  name='{name}', class='{airspace_class}'")
                    print(f"  Coordinates: {coordinates}")

                    reason = f"Insufficient polygon points ({len(coordinates)})"
                    skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1

            elif isinstance(geom, CircleGeometry):
                # Handle circle geometry using typed objects
                if VERBOSE:
                    print(
                        f"  Processing circle with center {geom.centerpoint} and radius {geom.radius}"
                    )
                if (
                    geom.centerpoint
                    and "lat" in geom.centerpoint
                    and "lng" in geom.centerpoint
                    and geom.radius > 0
                ):
                    center_lat, center_lng = (
                        geom.centerpoint["lat"],
                        geom.centerpoint["lng"],
                    )

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

                    feature["geometry"] = {
                        "type": "Polygon",
                        "coordinates": [coordinates],
                    }
                else:
                    if VERBOSE:
                        print(
                            f"  ✗ Invalid circle: centerpoint={geom.centerpoint}, radius={geom.radius}"
                        )
                    reason = "Invalid circle geometry"
                    skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1
            else:
                # Handle unknown geometry types
                if VERBOSE:
                    print(f"  Unknown geometry type: {type(geom)} - skipping")
                reason = f"Unknown geometry type: {type(geom).__name__}"
                skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1

            # Only add features with valid geometry
            if feature["geometry"] is not None:
                if VERBOSE:
                    print(
                        f"  ✓ Added feature '{name}' with {feature['geometry']['type']} geometry"
                    )
                features.append(feature)
            else:
                if VERBOSE:
                    print(f"  ✗ Skipped feature '{name}' - no valid geometry")

        except Exception as e:
            # Fallback to name from raw data if available
            if isinstance(airspace_data, dict):
                name = airspace_data.get("name", "Unknown")
                print(f"Error processing airspace {name}: {e}")
                print(f"  Raw airspace data keys: {list(airspace_data.keys())}")
                print(f"  Raw airspace data: {airspace_data}")
            else:
                name = getattr(airspace_data, "name", "Unknown")
                print(f"Error processing airspace {name}: {e}")
                print(f"  Airspace object type: {type(airspace_data)}")
                print(f"  Airspace object: {airspace_data}")

            print(f"  Exception type: {type(e)}")
            import traceback

            print(f"  Traceback: {traceback.format_exc()}")
            continue

    # Print summary of skipped airspaces
    if skipped_reasons:
        print(f"\nSkipped airspaces summary:")
        for reason, count in skipped_reasons.items():
            print(f"  {reason}: {count} airspaces")
        total_skipped = sum(skipped_reasons.values())
        print(f"  Total skipped: {total_skipped}")
    else:
        print("No airspaces were skipped due to geometry issues")

    # Count converted line obstacles
    line_obstacles = sum(
        1 for f in features if f["properties"].get("geometryType") == "line"
    )
    if line_obstacles > 0:
        print(
            f"Converted {line_obstacles} 2-point polygons to LineString geometries (line obstacles)"
        )

    return {"type": "FeatureCollection", "features": features}


def load_airspace_data(filepath=None):
    """Load and process airspace data from a file."""
    global _cached_airspaces, _cached_geojson, _current_filename

    # Use provided filepath or default Switzerland file
    if filepath is None:
        filepath = os.path.join(os.path.dirname(__file__), "examples/Switzerland.txt")

    # Only reload if filepath changed or no data cached, and the file exists
    if (_cached_airspaces is None or _current_filename != filepath) and os.path.exists(
        filepath
    ):
        try:
            print(f"Loading airspace data from: {filepath}")

            # Use the openair library to parse the file (returns raw dictionary data)
            raw_airspaces = parse_file(filepath)

            # Convert raw data to typed Airspace objects
            _cached_airspaces = [
                convert_raw_airspace(raw_data) for raw_data in raw_airspaces
            ]
            _current_filename = filepath

            # Convert to GeoJSON for web display
            _cached_geojson = convert_airspace_to_geojson(_cached_airspaces)

            print(
                f"Loaded {len(_cached_airspaces)} airspaces from {os.path.basename(filepath)}"
            )
            print(f"Generated {len(_cached_geojson['features'])} GeoJSON features")

            # Debug: Print first airspace structure
            if VERBOSE:
                if _cached_airspaces:
                    print("First airspace structure:")
                    first_airspace = _cached_airspaces[0]
                    print(f"Name: {first_airspace.name}")
                    print(f"Class: {first_airspace.airspace_class}")
                    print(f"Lower: {first_airspace.lower_bound.to_text()}")
                    print(f"Upper: {first_airspace.upper_bound.to_text()}")
                    print(f"Geometry type: {type(first_airspace.geom).__name__}")

        except Exception as e:
            print(f"Error loading airspace data: {e}")
            import traceback

            traceback.print_exc()
            _cached_airspaces = []
            _cached_geojson = {"type": "FeatureCollection", "features": []}
            _current_filename = None
    elif not os.path.exists(filepath):
        print(f"File does not exist: {filepath}")
        # If the cached file doesn't exist, reset to default
        if filepath != os.path.join(
            os.path.dirname(__file__), "examples/Switzerland.txt"
        ):
            return load_airspace_data()  # Recursive call with default file

    return _cached_airspaces, _cached_geojson


@app.route("/")
def index():
    """Render the main page with airspace map."""
    # If we have cached data from an upload, use it directly
    if _cached_airspaces is not None and _cached_geojson is not None:
        airspaces = _cached_airspaces
        geojson = _cached_geojson
    else:
        # Otherwise load default data
        airspaces, geojson = load_airspace_data()

    current_file = (
        os.path.basename(_current_filename)
        if _current_filename
        else "examples/Switzerland.txt"
    )
    return render_template(
        "index.html",
        title="Airspace Viewer",
        airspace_count=len(airspaces),
        geojson=json.dumps(geojson),
        current_file=current_file,
        legend_data=get_legend_data(),
        airspace_colors_js=generate_javascript_colors(),
        airspace_colors_css=generate_complete_css(),
    )


@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload for custom airspace files."""
    global _cached_airspaces, _cached_geojson, _current_filename

    if "file" not in request.files:
        flash("No file selected", "error")
        return redirect(url_for("index"))

    file = request.files["file"]
    if file.filename == "":
        flash("No file selected", "error")
        return redirect(url_for("index"))

    if file and allowed_file(file.filename):
        # Save uploaded file to temp directory
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        try:
            # Use the openair library to parse the file directly
            from openair import parse_file

            print(f"Loading airspace data from uploaded file: {filepath}")
            raw_airspaces = parse_file(filepath)

            # Convert raw data to typed Airspace objects
            _cached_airspaces = [
                convert_raw_airspace(raw_data) for raw_data in raw_airspaces
            ]

            # Convert to GeoJSON for web display
            _cached_geojson = convert_airspace_to_geojson(_cached_airspaces)

            # Set current filename to the original filename for display
            _current_filename = filename

            print(f"Loaded {len(_cached_airspaces)} airspaces from {filename}")
            print(f"Generated {len(_cached_geojson['features'])} GeoJSON features")

            flash(
                f"Successfully loaded {len(_cached_airspaces)} airspaces from {filename}",
                "success",
            )
        except Exception as e:
            print(f"Error parsing uploaded file: {e}")
            import traceback

            traceback.print_exc()
            flash(f"Error parsing file: {str(e)}", "error")

        # Clean up temp file
        try:
            os.remove(filepath)
        except:
            pass
    else:
        flash(
            "Invalid file type. Please upload .txt, .air, or .openair files.", "error"
        )

    return redirect(url_for("index"))


@app.route("/reset")
def reset_to_default():
    """Reset to default Switzerland airspace file."""
    global _cached_airspaces, _cached_geojson, _current_filename
    _cached_airspaces = None
    _cached_geojson = None
    _current_filename = None
    flash("Reset to default Switzerland airspace data", "info")
    return redirect(url_for("index"))


@app.route("/api/airspaces")
def api_airspaces():
    """API endpoint to get airspace data as GeoJSON."""
    airspaces, geojson = load_airspace_data()
    return jsonify(geojson)


@app.route("/api/stats")
def api_stats():
    """API endpoint to get airspace statistics."""
    airspaces, _ = load_airspace_data()

    # Count airspaces by class using typed objects
    class_counts = {}
    for airspace in airspaces:
        airspace_class = airspace.airspace_class
        class_counts[airspace_class] = class_counts.get(airspace_class, 0) + 1

    return jsonify({"total_airspaces": len(airspaces), "classes": class_counts})


if __name__ == "__main__":
    # Load airspaces on startup for debugging
    load_airspace_data()
    app.run(debug=True, port=5002)

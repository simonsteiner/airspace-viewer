"""API routes for the Airspace Viewer application."""

from flask import Blueprint, Response, jsonify

from app.services.airspace_service import get_airspace_service

api_bp = Blueprint("api", __name__, url_prefix="/api")


# Export KML route
@api_bp.route("/export_kml")
def export_kml():
    """API endpoint to export airspaces as KML."""
    service = get_airspace_service()
    kml_str = service.export_to_kml()
    kml_bytes = kml_str.encode("utf-8")

    if not kml_bytes:
        return jsonify({"error": "No airspaces to export"}), 404
    return Response(
        kml_bytes,
        mimetype="application/vnd.google-earth.kml+xml",
        headers={"Content-Disposition": "attachment; filename=airspaces.kml"},
    )


@api_bp.route("/airspaces")
def get_airspaces():
    """API endpoint to get airspace data as GeoJSON."""
    service = get_airspace_service()
    _, geojson = service.get_cached_data()
    return jsonify(geojson)


@api_bp.route("/stats")
def get_stats():
    """API endpoint to get airspace statistics."""
    service = get_airspace_service()
    stats = service.get_airspace_stats()
    return jsonify(stats)

#!/usr/bin/env python3

from flask import Blueprint, jsonify

from app.services.airspace_service import get_airspace_service

api_bp = Blueprint("api", __name__, url_prefix="/api")


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

#!/usr/bin/env python3

import json
from flask import Blueprint, render_template, request, flash, redirect, url_for
from services.airspace_service import get_airspace_service
from utils.file_utils import allowed_file, get_secure_filepath, cleanup_temp_file
from utils.airspace_colors import (
    get_legend_data,
    generate_javascript_colors,
    generate_complete_css,
)


main_bp = Blueprint("main", __name__)


@main_bp.route("/health")
def health_check():
    """Health check endpoint for load balancer and monitoring."""
    return {"status": "healthy", "message": "Airspace Viewer is running"}, 200


@main_bp.route("/")
def index():
    """Render the main page with airspace map."""
    service = get_airspace_service()
    airspaces, geojson = service.get_cached_data()
    current_file = service.get_current_filename()

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


@main_bp.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload for custom airspace files."""
    from flask import current_app

    if "file" not in request.files:
        flash("No file selected", "error")
        return redirect(url_for("main.index"))

    file = request.files["file"]
    if file.filename == "":
        flash("No file selected", "error")
        return redirect(url_for("main.index"))

    if file and allowed_file(file.filename, current_app.config["ALLOWED_EXTENSIONS"]):
        # Save uploaded file to temp directory
        filepath = get_secure_filepath(
            file.filename, current_app.config["UPLOAD_FOLDER"]
        )
        file.save(filepath)

        # Process the uploaded file
        service = get_airspace_service()
        success, error_msg = service.load_from_uploaded_file(filepath, file.filename)

        if success:
            airspace_count = len(service.get_cached_data()[0])
            flash(
                f"Successfully loaded {airspace_count} airspaces from {file.filename}",
                "success",
            )
        else:
            flash(f"Error parsing file: {error_msg}", "error")

        # Clean up temp file
        cleanup_temp_file(filepath)
    else:
        flash(
            "Invalid file type. Please upload .txt, .air, or .openair files.", "error"
        )

    return redirect(url_for("main.index"))


@main_bp.route("/reset")
def reset_to_default():
    """Reset to default Switzerland airspace file."""
    service = get_airspace_service()
    service.reset_to_default()
    flash("Reset to default Switzerland airspace data", "info")
    return redirect(url_for("main.index"))

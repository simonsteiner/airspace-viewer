"""Main web routes for the Airspace Viewer Flask application."""

import json

from flask import (
    Blueprint,
    Response,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from app.services.airspace_service import get_airspace_service
from app.utils.airspace_colors import (
    generate_complete_css,
    generate_javascript_colors,
    get_legend_data,
)
from app.utils.file_utils import allowed_file, cleanup_temp_file, get_secure_filepath

main_bp = Blueprint("main", __name__)


@main_bp.route("/health")
def health_check():
    """Health check endpoint for load balancer and monitoring."""
    return {"status": "healthy", "message": "Airspace Viewer is running"}, 200


@main_bp.route("/")
def index():
    """Render the main page with airspace map."""
    service = get_airspace_service()
    airspaces, _ = service.get_cached_data()
    current_file = service.get_current_filename()

    return render_template(
        "index.html",
        title="Airspace Viewer",
        airspace_count=len(airspaces or []),
        current_file=current_file,
        legend_data=get_legend_data(),
    )


@main_bp.route("/config.js")
def js_config():
    """Render the JavaScript configuration file."""
    service = get_airspace_service()
    _, geojson = service.get_cached_data()

    template = render_template(
        "js/config.js",
        airspace_colors_js=generate_javascript_colors(),
        geojson=json.dumps(geojson),
    )
    return Response(template, mimetype="application/javascript")


@main_bp.route("/airspace_colors.css")
def css_colors():
    """Render the airspace colors CSS file."""
    template = render_template(
        "css/airspace_colors.css",
        airspace_colors_css=generate_complete_css(),
    )
    return Response(template, mimetype="text/css")


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
            airspaces = service.get_cached_data()[0] or []
            airspace_count = len(airspaces)
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

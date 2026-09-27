import io
from typing import Any

from flask.testing import FlaskClient

from .conftest import FIXTURES


def _upload(client: FlaskClient, name: str, data: bytes) -> Any:
    return client.post(
        "/upload",
        data={"file": (io.BytesIO(data), name)},
        content_type="multipart/form-data",
        follow_redirects=True,
    )


def test_default_file_loads(client: FlaskClient) -> None:
    geojson = client.get("/api/airspaces").get_json()
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) > 300
    classes = client.get("/api/stats").get_json()["classes"]
    assert {"CTR", "D", "Restricted", "Danger"} <= classes.keys()


def test_upload_maps_classes_and_colors(client: FlaskClient) -> None:
    response = _upload(client, "classes.txt", (FIXTURES / "classes.txt").read_bytes())
    assert response.status_code == 200
    assert b"Successfully loaded 6 airspaces from classes.txt" in response.data

    features = client.get("/api/airspaces").get_json()["features"]
    props = {f["properties"]["name"]: f["properties"] for f in features}
    assert props["Restricted Legacy"]["class"] == "Restricted"
    assert props["Restricted Legacy"]["color"] == "#ffc107"
    assert props["Danger Legacy"]["color"] == "#4caf50"
    assert props["Control Zone"]["color"] == "#f44336"
    assert props["Control Zone"]["upperBound"] == "?(4500.0.5FT)"
    assert props["Restricted V2"]["class"] == "Restricted"
    assert props["Unknown Class"]["class"] == "FOO"
    assert props["Unknown Class"]["color"] == "#999999"
    assert props[""]["class"] == "D"

    assert client.get("/api/stats").get_json() == {
        "total_airspaces": 6,
        "classes": {"Restricted": 2, "Danger": 1, "CTR": 1, "FOO": 1, "D": 1},
    }


def test_upload_invalid_file_reports_error(client: FlaskClient) -> None:
    response = _upload(client, "broken.txt", b"AC R\nAN X\nDP nonsense\n")
    assert response.status_code == 200
    assert b"Error parsing file" in response.data


def test_export_kml(client: FlaskClient) -> None:
    _upload(client, "classes.txt", (FIXTURES / "classes.txt").read_bytes())
    response = client.get("/api/export_kml")
    assert response.status_code == 200
    assert response.mimetype == "application/vnd.google-earth.kml+xml"
    assert b"Restricted Legacy (Restricted)" in response.data


def test_legend_and_assets(client: FlaskClient) -> None:
    page = client.get("/")
    assert page.status_code == 200
    assert b"Class Restricted" in page.data
    assert b".class-Restricted" in client.get("/airspace_colors.css").data
    assert b"'Restricted': '#ffc107'" in client.get("/config.js").data
    assert client.get("/health").get_json()["status"] == "healthy"

from collections.abc import Iterator
from pathlib import Path

import pytest
from flask import Flask
from flask.testing import FlaskClient

import app.services.airspace_service as airspace_service_module
from app import create_app

FIXTURES = Path(__file__).parent / "fixtures"
EXAMPLES = Path(__file__).parent.parent / "app" / "examples"


@pytest.fixture(autouse=True)
def reset_airspace_singleton() -> Iterator[None]:
    """The service is a module-global singleton; don't leak data between tests."""
    airspace_service_module.airspace_service = None
    yield
    airspace_service_module.airspace_service = None


@pytest.fixture
def app() -> Flask:
    flask_app = create_app("production")
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()

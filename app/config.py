#!/usr/bin/env python3

import os
import tempfile


class Config:
    """Application configuration."""

    # Flask settings - use SECRET_KEY as Flask expects, but fall back to FLASK_SECRET_KEY
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or os.environ.get(
        "SECRET_KEY", "fallback-dev-key"
    )

    # Upload settings
    UPLOAD_FOLDER = tempfile.gettempdir()
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {"txt", "air", "openair"}

    # Debug settings
    VERBOSE = False

    # Default airspace file - use absolute path from app directory
    DEFAULT_AIRSPACE_FILE = os.path.join(
        os.path.dirname(__file__), "examples", "Switzerland.txt"
    )


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    VERBOSE = True


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    VERBOSE = False


# Configuration mapping
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

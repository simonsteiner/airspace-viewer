"""Configuration settings for the airspace-viewer application.

This module defines configuration classes for different environments (development, production),
including settings for Flask, file uploads, and airspace file defaults.

Classes:
    Config: Base configuration class with default settings.
    DevelopmentConfig: Configuration for development environment.
    ProductionConfig: Configuration for production environment.

Attributes:
    config (dict): Mapping of environment names to configuration classes.
"""

import os
import tempfile


class Config:
    """Base application configuration.

    Attributes:
        SECRET_KEY (str): Secret key for Flask sessions.
        UPLOAD_FOLDER (str): Directory for file uploads.
        MAX_CONTENT_LENGTH (int): Maximum allowed upload size in bytes.
        ALLOWED_EXTENSIONS (set): Allowed file extensions for uploads.
        VERBOSE (bool): Verbosity flag for logging/debugging.
        DEFAULT_AIRSPACE_FILE (str): Path to the default airspace file.
    """

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
    DEBUG_LOGGING = False

    # Default airspace file - use absolute path from app directory
    DEFAULT_AIRSPACE_FILE = os.path.join(
        os.path.dirname(__file__), "examples", "Switzerland.txt"
    )


class DevelopmentConfig(Config):
    """Development environment configuration.

    Inherits from Config and enables debugging and verbose output.
    """

    VERBOSE = True
    DEBUG_LOGGING = True  # Enable debug logging in development


class ProductionConfig(Config):
    """Production environment configuration.

    Inherits from Config and disables debugging and verbose output.
    """

    VERBOSE = False
    DEBUG_LOGGING = False  # Disable debug logging in production


# Configuration mapping
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

"""WSGI entry point for the Airspace Viewer application.

This file serves as the entry point for running the Flask app in production environments (e.g., Fly.io)
or for local development. It sets up logging, configures the Python path, and creates the Flask application instance.
"""

import os
import sys

from app import create_app
from app.utils.logging_utils import (
    debug_log,
    error_log,
    info_log,
    warning_log,
)

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

print("Starting Flask application")

# Create the Flask application instance
if __name__ == "__main__":
    application = create_app("development")

    print("Running in development mode")

    # Log test messages after debug logging is enabled
    debug_log("application", "This is a debug message")
    info_log("application", "Airspace service initialized successfully")
    error_log("application", "This is an error message")
    warning_log("application", "This is a warning message")

    application.run(host="0.0.0.0", port=8000)
else:
    application = create_app("production")

    print("Running in production mode")
    # Log test messages after app context is established
    debug_log("application", "This is a debug message")
    info_log("application", "Airspace service initialized successfully")
    error_log("application", "This is an error message")
    warning_log("application", "This is a warning message")

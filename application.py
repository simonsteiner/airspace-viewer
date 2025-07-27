"""WSGI entry point for the Airspace Viewer application.

This file serves as the entry point for running the Flask app in production environments (e.g., Fly.io)
or for local development. It sets up logging, configures the Python path, and creates the Flask application instance.
"""

import logging
import os
import sys

from app import create_app
from app.utils.airspace_colors import print_airspace_colors_debug

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting Flask application")

# Create the Flask application instance
if __name__ == "__main__":
    application = create_app("development")
    application.config["VERBOSE"] = False  # Set verbose mode for development
    with application.app_context():
        print_airspace_colors_debug()
    application.debug = True
    application.run(host="0.0.0.0", port=8000)
else:
    application = create_app("production")

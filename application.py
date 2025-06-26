# This file is used to run the application with a WSGI server like Gunicorn or uWSGI.

import sys
import os
import logging

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the app directory to the Python path
app_dir = os.path.join(os.path.dirname(__file__), "app")
sys.path.insert(0, app_dir)

logger.info(f"Python path: {sys.path}")
logger.info(f"App directory: {app_dir}")
logger.info(f"Current working directory: {os.getcwd()}")

try:
    from app import create_app

    logger.info("Successfully imported create_app")

    # Create the application instance for WSGI servers
    application = create_app("production")
    logger.info("Application created successfully")

except Exception as e:
    logger.error(f"Failed to create application: {e}")
    raise

# Ensure the application variable is available at module level
if __name__ == "__main__":
    logger.info("Running application directly")
    application.run(host="0.0.0.0", port=8000)

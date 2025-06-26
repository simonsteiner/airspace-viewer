"""
WSGI entry point for AWS Elastic Beanstalk
"""

import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize application variable at module level
application = None

# Add the app directory to Python path
app_dir = os.path.join(os.path.dirname(__file__), "app")
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

logger.info(f"Added to Python path: {app_dir}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Python path: {sys.path[:3]}...")  # Show first 3 entries

# Import and create the Flask application
try:
    from app import create_app

    logger.info("Successfully imported create_app function")

    # Create the Flask application instance
    application = create_app("production")
    logger.info("Flask application created successfully for production")

    # Verify the application is callable
    if hasattr(application, "wsgi_app"):
        logger.info("Application has wsgi_app attribute - Flask app is ready")
    else:
        logger.warning("Application missing wsgi_app attribute")

except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error(f"Current directory contents: {os.listdir('.')}")
    if os.path.exists("app"):
        logger.error(f"App directory contents: {os.listdir('app')}")

    # Create a minimal WSGI application that returns an error
    def error_application(environ, start_response):
        status = "500 Internal Server Error"
        headers = [("Content-type", "text/plain")]
        start_response(status, headers)
        return [f"Import Error: {e}".encode()]

    application = error_application
    logger.error("Created error application as fallback")

except Exception as e:
    logger.error(f"Error creating application: {e}")
    import traceback

    logger.error(f"Traceback: {traceback.format_exc()}")

    # Create a minimal WSGI application that returns an error
    def error_application(environ, start_response):
        status = "500 Internal Server Error"
        headers = [("Content-type", "text/plain")]
        start_response(status, headers)
        return [f"Application Error: {e}".encode()]

    application = error_application
    logger.error("Created error application as fallback")

# Ensure application is always defined
if application is None:
    logger.error("Application is None - creating minimal error application")

    def error_application(environ, start_response):
        status = "500 Internal Server Error"
        headers = [("Content-type", "text/plain")]
        start_response(status, headers)
        return [b"Application failed to initialize"]

    application = error_application

# For local testing
if __name__ == "__main__":
    logger.info("Running application directly for testing")
    if hasattr(application, "run"):
        application.run(host="0.0.0.0", port=8000, debug=False)
    else:
        logger.error("Cannot run application directly - not a Flask app")

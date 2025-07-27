"""
WSGI entry point for AWS Elastic Beanstalk
"""

import logging
import os
import sys

from app import create_app

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting Flask application")

# Create the Flask application instance
application = create_app("production")

# Optional: for local testing
if __name__ == "__main__":
    application.debug = True
    application.run(host="0.0.0.0", port=8000)

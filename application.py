# This file is used to run the application with a WSGI server like Gunicorn or uWSGI.

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from app import create_app

# Create the application instance for WSGI servers
application = create_app("production")

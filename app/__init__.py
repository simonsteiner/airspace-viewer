"""Flask application factory and initialization logic.

It sets up configuration, registers blueprints, and initializes core services on startup.

Public Functions:
    create_app: Application factory for creating and configuring the Flask app instance.
    main: Main entry point for running the application in development mode.
"""

import os

from flask import Flask


def create_app(config_name=None):
    """Application factory function for the Flask app.

    Args:
        config_name (str, optional): The configuration name to use (e.g., 'development', 'production').
            If None, uses the FLASK_ENV environment variable or 'default'.

    Returns:
        Flask: The configured Flask application instance.

    Raises:
        Exception: If the application fails to initialize.
    """
    try:
        app = Flask(__name__)
        print(f"Configuring Flask app with config_name: {config_name}")

        # Load configuration
        if config_name is None:
            config_name = os.environ.get("FLASK_ENV", "default")

        from .config import config

        app.config.from_object(config[config_name])
        print(f"Configuration loaded: {config_name}")

        # Set logger level to INFO
        try:
            import logging

            from .utils import logging_utils

            logging_utils.set_debug_enabled(False)
            logger = logging.getLogger("airspace_viewer")
            logger.setLevel(logging.INFO)
        except Exception as e:
            print(f"Failed to set logger level to INFO: {e}")

        # Register blueprints
        from .routes.api_routes import api_bp
        from .routes.main_routes import main_bp
        from .routes.static_routes import static_bp

        app.register_blueprint(main_bp)
        app.register_blueprint(api_bp)
        app.register_blueprint(static_bp)
        print("Blueprints registered successfully")

        with app.app_context():
            try:
                from .services.airspace_service import get_airspace_service

                service = get_airspace_service()
                # Load default data on startup
                service.load_airspace_data()
                print("Airspace service initialized successfully")
            except Exception as e:
                print(f"Failed to initialize airspace service: {e}")
                # Continue without failing - service can be initialized later

        print("Flask application created successfully")
        return app

    except Exception as e:
        print(f"Failed to create Flask application: {e}")
        raise

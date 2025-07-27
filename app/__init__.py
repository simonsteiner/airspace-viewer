#!/usr/bin/env python3

import os

from flask import Flask


def create_app(config_name=None):
    """Application factory function."""
    import logging

    logger = logging.getLogger(__name__)

    try:
        app = Flask(__name__)
        logger.info(f"Flask app created, config_name: {config_name}")

        # Load configuration
        if config_name is None:
            config_name = os.environ.get("FLASK_ENV", "default")

        from .config import config

        app.config.from_object(config[config_name])
        logger.info(f"Configuration loaded: {config_name}")

        # Register blueprints
        from .routes.api_routes import api_bp
        from .routes.main_routes import main_bp
        from .routes.static_routes import static_bp

        app.register_blueprint(main_bp)
        app.register_blueprint(api_bp)
        app.register_blueprint(static_bp)
        logger.info("Blueprints registered")

        # Initialize services on startup with error handling
        with app.app_context():
            try:
                from .services.airspace_service import get_airspace_service

                service = get_airspace_service()
                # Load default data on startup
                service.load_airspace_data()
                logger.info("Airspace service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize airspace service: {e}")
                # Continue without failing - service can be initialized later

        logger.info("Application created successfully")
        return app

    except Exception as e:
        logger.error(f"Failed to create Flask application: {e}")
        raise


def main():
    """Main entry point for running the application."""
    app = create_app("development")
    app.run(debug=True, port=os.getenv("PORT", default=5002), host="0.0.0.0")


if __name__ == "__main__":
    main()

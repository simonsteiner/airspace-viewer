#!/usr/bin/env python3

import os
from flask import Flask


def create_app(config_name=None):
    """Application factory function."""
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    from config import config
    app.config.from_object(config[config_name])
    
    # Register blueprints
    from routes.main_routes import main_bp
    from routes.api_routes import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    
    # Initialize services on startup
    with app.app_context():
        from services.airspace_service import get_airspace_service
        service = get_airspace_service()
        # Load default data on startup
        service.load_airspace_data()
    
    return app


def main():
    """Main entry point for running the application."""
    app = create_app('development')
    app.run(debug=True, port=5002)


if __name__ == "__main__":
    main()

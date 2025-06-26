#!/usr/bin/env python3
"""
Simple test script to verify the application can be imported and started.
This helps diagnose issues before deployment.
"""

import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

try:
    print("Testing application import...")
    from app import create_app

    print("✓ Successfully imported create_app")

    print("Testing application creation...")
    app = create_app("production")
    print("✓ Successfully created Flask application")

    print("Testing application routes...")
    with app.test_client() as client:
        response = client.get("/health")
        print(f"✓ Health check response: {response.status_code}")

        response = client.get("/")
        print(f"✓ Main page response: {response.status_code}")

    print("✓ Application test completed successfully!")

except Exception as e:
    print(f"✗ Application test failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

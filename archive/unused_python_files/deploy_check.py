#!/usr/bin/env python3
"""
Deployment verification script to ensure all components are working correctly.
This script checks all the issues mentioned in the deployment error.
"""

import logging
import os
import sys
from datetime import datetime

import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_flask_app():
    """Check if Flask app can be imported and started."""
    try:
        logger.info("Checking Flask app import...")
        from app import application, initialize_system
        logger.info("✓ Flask app imported successfully")

        logger.info("Checking system initialization...")
        initialize_system()
        logger.info("✓ System initialized successfully")

        logger.info("Checking WSGI application...")
        assert application is not None
        logger.info("✓ WSGI application available")

        return True
    except Exception as e:
        logger.error(f"✗ Flask app check failed: {e}")
        return False

def check_port_configuration():
    """Check port configuration."""
    logger.info("Checking port configuration...")

    port = int(os.environ.get("PORT", "5000"))
    logger.info(f"✓ PORT environment variable: {port}")

    flask_env = os.environ.get("FLASK_ENV", "production")
    logger.info(f"✓ FLASK_ENV: {flask_env}")

    return True

def check_health_endpoints():
    """Check health check endpoints."""
    logger.info("Checking health endpoints...")

    base_url = "http://localhost:5000"
    endpoints = [
        ("/", {"Accept": "application/json"}),
        ("/health", {}),
        ("/ready", {})
    ]

    for endpoint, headers in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=5)
            if response.status_code == 200:
                logger.info(f"✓ {endpoint} responds with 200")
            else:
                logger.warning(f"⚠ {endpoint} responds with {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠ {endpoint} not accessible: {e}")

def check_file_references():
    """Check that all referenced files exist."""
    logger.info("Checking file references...")

    required_files = [
        "app.py",
        "web_interface.py",
        "wsgi.py",
        "Procfile",
        "deployment.json",
        "gunicorn.conf.py",
        "requirements.txt"
    ]

    for file in required_files:
        if os.path.exists(file):
            logger.info(f"✓ {file} exists")
        else:
            logger.error(f"✗ {file} missing")

def main():
    """Run all deployment checks."""
    logger.info("=== Deployment Configuration Check ===")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")

    checks = [
        check_flask_app,
        check_port_configuration,
        check_file_references,
        check_health_endpoints
    ]

    passed = 0
    total = len(checks)

    for check in checks:
        try:
            if check():
                passed += 1
        except Exception as e:
            logger.error(f"Check failed with exception: {e}")

    logger.info(f"=== Results: {passed}/{total} checks passed ===")

    if passed == total:
        logger.info("✓ All deployment checks passed! Ready for deployment.")
        return 0
    else:
        logger.error("✗ Some deployment checks failed. Please review above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
WSGI entry point for Quality Clamps Flask application
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from app import app
    application = app  # This is the WSGI application callable for Gunicorn

    # For local development only:
    # Use `python wsgi.py` to test
    # For production, use Gunicorn: `gunicorn wsgi:application --bind 127.0.0.1:8000`

except ImportError as e:
    print(f"Error importing app: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error starting application: {e}")
    sys.exit(1)
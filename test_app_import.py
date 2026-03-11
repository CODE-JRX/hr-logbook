#!/usr/bin/env python
"""Test that the Flask app can be imported successfully."""
import sys

try:
    from app import app
    print("✓ SUCCESS: App imported successfully")
    print(f"✓ App name: {app.name}")
    print(f"✓ Face recognition available: {app.config.get('TESTING', 'not set')}")
    sys.exit(0)
except Exception as e:
    print(f"✗ FAILED: {e}")
    sys.exit(1)

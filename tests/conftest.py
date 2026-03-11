"""
pytest configuration and fixtures for HR Logbook test suite.
"""
import pytest
import os
import sys
import json
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

@pytest.fixture
def app():
    """Create Flask app for testing."""
    try:
        from app import app as flask_app
        flask_app.config['TESTING'] = True
        flask_app.config['SECRET_KEY'] = 'test-secret-key'
        return flask_app
    except (ModuleNotFoundError, SystemExit) as e:
        # If face_recognition_models or pkg_resources is missing, skip
        if 'pkg_resources' in str(e) or 'face_recognition_models' in str(e):
            pytest.skip(f"Skipping app fixture: {e}")
        raise

@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create Flask CLI runner."""
    return app.test_cli_runner()

@pytest.fixture
def mock_db_cursor():
    """Create a mock database cursor."""
    cursor = Mock()
    cursor.fetchone = Mock(return_value=None)
    cursor.fetchall = Mock(return_value=[])
    cursor.rowcount = 0
    cursor.lastrowid = 0
    return cursor

@pytest.fixture
def sample_embedding():
    """Return a sample face encoding vector."""
    import numpy as np
    return np.random.rand(128).tolist()

@pytest.fixture
def sample_client_data():
    """Return sample client registration data."""
    return {
        'fname': 'John',
        'lname': 'Doe',
        'mi': 'A',
        'name_ext': 'Jr',
        'department': 'HR',
        'gender': 'M',
        'age': '30',
        'client_type': 'EMPLOYEE'
    }

@pytest.fixture
def sample_admin_data():
    """Return sample admin account data."""
    return {
        'first_name': 'Admin',
        'last_name': 'User',
        'email': 'admin@test.local',
        'password': 'SecurePass123!',
        'pin': '1234',
        'office': 'REGISTRAR'
    }

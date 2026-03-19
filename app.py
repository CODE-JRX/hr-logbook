import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, send_from_directory
from db import get_db_cursor, validate_schema
from routes.all_routes import client_bp

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-unsecure-key-for-dev')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload size
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes session timeout


def ensure_csm_form_office_column():
    """Rename the legacy CSM office column on startup when needed."""
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("SHOW COLUMNS FROM csm_form LIKE 'office'")
            office_exists = cursor.fetchone() is not None
            cursor.execute("SHOW COLUMNS FROM csm_form LIKE 'agency_visited'")
            legacy_exists = cursor.fetchone() is not None

            if not office_exists and legacy_exists:
                cursor.execute("ALTER TABLE csm_form RENAME COLUMN agency_visited TO office")
                logger.info('Renamed csm_form.agency_visited to office.')
    except Exception as e:
        logger.warning(f"Failed to ensure csm_form.office column: {e}")


def validate_startup_schema():
    """Validate database schema on startup. Warn if issues but allow app to continue."""
    logger.info("Validating database schema...")
    success, missing_tables, error_msg = validate_schema()
    
    if not success:
        logger.warning(f"Schema validation failed: {error_msg}")
        if missing_tables:
            logger.warning(f"Please run schema.sql to create missing tables: {', '.join(missing_tables)}")
    else:
        logger.info("Database schema validation passed.")


@app.context_processor
def inject_year():
    return {'year': datetime.now().year}


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle uploads larger than MAX_CONTENT_LENGTH."""
    logger.error(f"Request too large: {error}")
    return {'ok': False, 'error': 'File too large. Maximum 50MB allowed.'}, 413


@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors gracefully."""
    logger.error(f"Internal server error: {error}")
    return {'ok': False, 'error': 'Internal server error. Please try again.'}, 500




# ═════ STARTUP SEQUENCE ═════
logger.info("□ Starting HR Logbook application...")

# 1. Validate schema
validate_startup_schema()

# 2. Ensure CSM form has correct column names
ensure_csm_form_office_column()

# 3. Register blueprints
app.register_blueprint(client_bp)
from routes.backup_routes import backup_bp
app.register_blueprint(backup_bp)
from routes.employee_routes import employee_bp
app.register_blueprint(employee_bp)

# 4. Warm up face recognition caches
try:
    logger.info("□ Warming up face embedding caches...")
    from models.face_embedding_model import get_face_cache
    from models.admin_model import get_admin_face_cache
    
    # Load caches - any errors here are non-fatal
    try:
        face_cache = get_face_cache()
        logger.info(f"✓ Loaded {len(face_cache)} client face embeddings")
    except Exception as e:
        logger.warning(f"Failed to load client face cache: {e}")
    
    try:
        admin_cache = get_admin_face_cache()
        logger.info(f"✓ Loaded {len(admin_cache)} admin face embeddings")
    except Exception as e:
        logger.warning(f"Failed to load admin face cache: {e}")
        
except ImportError as e:
    logger.warning(f"Face recognition modules not available: {e}")
except Exception as e:
    logger.warning(f"Failed to warm up face caches: {e}")

logger.info("✓ Application startup complete\n")



if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

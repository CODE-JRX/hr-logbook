import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, send_from_directory
from db import get_db_cursor
from routes.all_routes import client_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-unsecure-key-for-dev')


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
                print('Renamed csm_form.agency_visited to office.')
    except Exception as e:
        print(f"Warning: Failed to ensure csm_form.office column: {e}")


@app.context_processor
def inject_year():
    return {'year': datetime.now().year}





ensure_csm_form_office_column()

app.register_blueprint(client_bp)
from routes.backup_routes import backup_bp
app.register_blueprint(backup_bp)

# Warm up face recognition caches
try:
    from models.face_embedding_model import get_face_cache
    from models.admin_model import get_admin_face_cache
    print("Warming up face embedding caches...")
    get_face_cache()
    get_admin_face_cache()
    print("Face embedding caches specialized and ready.")
except Exception as e:
    print(f"Warning: Failed to warm up face caches: {e}")


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

from db import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

def ensure_admins_table():
    # No-op for MongoDB as collections are lazy/handled by init script
    pass

def add_admin(first_name, last_name, email, password):
    db = get_db()
    ph = generate_password_hash(password)
    db.admins.insert_one({
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password_hash": ph,
        "created_at": datetime.now()
    })

def get_admin_by_email(email):
    db = get_db()
    # Normalize result to simpler dict if needed, or return None
    # We convert _id to str if we want consistency, but internal use mainly needs dict
    admin = db.admins.find_one({"email": email})
    if admin:
        # Convert ObjectId to string for session/compatibility
        admin['id'] = str(admin['_id'])
    return admin

def verify_admin_credentials(email, password):
    admin = get_admin_by_email(email)
    if not admin:
        return None
    if check_password_hash(admin.get('password_hash', ''), password):
        return admin
    return None

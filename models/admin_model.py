from db import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import numpy as np

def ensure_admins_table():
    # No-op for MongoDB as collections are lazy/handled by init script
    pass

def add_admin(first_name, last_name, email, password, embedding_list=None):
    db = get_db()
    ph = generate_password_hash(password)
    doc = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password_hash": ph,
        "created_at": datetime.now()
    }
    if embedding_list:
        doc["face_embedding"] = embedding_list
    result = db.admins.insert_one(doc)
    return str(result.inserted_id)

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


def get_admin_by_id(admin_id):
    from bson.objectid import ObjectId
    db = get_db()
    try:
        admin = db.admins.find_one({"_id": ObjectId(admin_id)})
        if admin:
            admin['id'] = str(admin['_id'])
        return admin
    except:
        return None

def update_admin_password(admin_id, new_password):
    from bson.objectid import ObjectId
    db = get_db()
    ph = generate_password_hash(new_password)
    try:
        result = db.admins.update_one(
            {"_id": ObjectId(admin_id)},
            {"$set": {"password_hash": ph, "updated_at": datetime.now()}}
        )
        return result.modified_count > 0
    except:
        return False

def find_best_admin_match(embedding_list, threshold=0.6):
    """Find the closest stored admin face embedding to the given embedding_list."""
    db = get_db()
    cursor = db.admins.find({}, {"_id": 1, "face_embedding": 1})
    target = np.array(embedding_list)
    best_id = None
    best_distance = None
    for r in cursor:
        stored_emb = r.get('face_embedding')
        if stored_emb:
            emb = np.array(stored_emb)
            dist = np.linalg.norm(emb - target)
            if best_distance is None or dist < best_distance:
                best_distance = float(dist)
                best_id = str(r['_id'])
    if best_distance is not None and best_distance <= threshold:
        return best_id, best_distance
    return None, None

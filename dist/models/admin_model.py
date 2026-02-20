from db import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import numpy as np
import json
import mysql.connector

def add_admin(first_name, last_name, email, password, embedding_list=None, pin=None):
    db = get_db()
    cursor = db.cursor()
    ph = generate_password_hash(password)
    pin_hash = generate_password_hash(pin) if pin else None
    
    query = """INSERT INTO admins (first_name, last_name, email, password_hash, pin_hash, face_embedding, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    values = (
        first_name.upper() if isinstance(first_name, str) else first_name,
        last_name.upper() if isinstance(last_name, str) else last_name,
        email.lower() if isinstance(email, str) else email,
        ph,
        pin_hash,
        json.dumps(embedding_list) if embedding_list else None,
        datetime.now()
    )
    
    try:
        cursor.execute(query, values)
        db.commit()
        last_id = cursor.lastrowid
        return str(last_id)
    except mysql.connector.Error as err:
        print(f"Error adding admin: {err}")
        return None
    finally:
        cursor.close()
        db.close()

def get_admin_by_email(email):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    email_lower = email.lower() if isinstance(email, str) else email
    
    query = "SELECT * FROM admins WHERE email = %s"
    cursor.execute(query, (email_lower,))
    admin = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    if admin:
        admin['id'] = str(admin['id'])
        emb_data = admin.get('face_embedding')
        if isinstance(emb_data, (bytes, bytearray)):
            admin['face_embedding'] = json.loads(emb_data.decode('utf-8'))
        elif isinstance(emb_data, str):
            admin['face_embedding'] = json.loads(emb_data)
    return admin

def verify_admin_credentials(email, password):
    admin = get_admin_by_email(email)
    if not admin:
        return None
    if check_password_hash(admin.get('password_hash', ''), password):
        return admin
    return None

def verify_admin_pin(admin, pin):
    if not admin or not pin:
        return False
    # If no pin hash exists, fail secure or allow? Assuming fail secure for 2FA.
    # But for backward compatibility, if pin_hash is null, we might need a policy.
    # For now, if pin_hash is set, check it.
    stored_pin_hash = admin.get('pin_hash')
    if not stored_pin_hash:
        return False # PIN is mandatory for face login now
    return check_password_hash(stored_pin_hash, pin)

def get_admin_by_id(admin_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    query = "SELECT * FROM admins WHERE id = %s"
    cursor.execute(query, (admin_id,))
    admin = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    if admin:
        admin['id'] = str(admin['id'])
        emb_data = admin.get('face_embedding')
        if isinstance(emb_data, (bytes, bytearray)):
            admin['face_embedding'] = json.loads(emb_data.decode('utf-8'))
        elif isinstance(emb_data, str):
            admin['face_embedding'] = json.loads(emb_data)
    return admin

def update_admin_password(admin_id, new_password):
    db = get_db()
    cursor = db.cursor()
    ph = generate_password_hash(new_password)
    
    query = "UPDATE admins SET password_hash = %s, updated_at = %s WHERE id = %s"
    try:
        cursor.execute(query, (ph, datetime.now(), admin_id))
        db.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error:
        return False
    finally:
        cursor.close()
        db.close()

def find_best_admin_match(embedding_list, threshold=0.6):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT id, face_embedding FROM admins WHERE face_embedding IS NOT NULL")
    target = np.array(embedding_list)
    best_id = None
    best_distance = None
    
    for r in cursor:
        stored_json = r.get('face_embedding')
        if not stored_json:
            continue
            
        if isinstance(stored_json, (bytes, bytearray)):
            stored_data = json.loads(stored_json.decode('utf-8'))
        elif isinstance(stored_json, str):
            stored_data = json.loads(stored_json)
        else:
            stored_data = stored_json
            
        # Handle both old (single list) and new (list of lists) formats
        # New format: [[...], [...], [...]]
        # Old format: [...]
        
        candidates = []
        if isinstance(stored_data, list) and len(stored_data) > 0:
            if isinstance(stored_data[0], list):
                # Request returns list of lists
                candidates = [np.array(e) for e in stored_data]
            else:
                # Legacy single embedding
                candidates = [np.array(stored_data)]
        
        # Check against all candidates for this admin
        for emb in candidates:
            dist = np.linalg.norm(emb - target)
            if best_distance is None or dist < best_distance:
                best_distance = float(dist)
                best_id = str(r['id'])
    
    cursor.close()
    db.close()
    
    if best_distance is not None and best_distance <= threshold:
        return best_id, best_distance
    return None, None

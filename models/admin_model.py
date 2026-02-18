from db import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import numpy as np
import json
import mysql.connector

def add_admin(first_name, last_name, email, password, embedding_list=None):
    db = get_db()
    cursor = db.cursor()
    ph = generate_password_hash(password)
    
    query = """INSERT INTO admins (first_name, last_name, email, password_hash, face_embedding, created_at)
               VALUES (%s, %s, %s, %s, %s, %s)"""
    values = (
        first_name.upper() if isinstance(first_name, str) else first_name,
        last_name.upper() if isinstance(last_name, str) else last_name,
        email.upper() if isinstance(email, str) else email,
        ph,
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
    email_upper = email.upper() if isinstance(email, str) else email
    
    query = "SELECT * FROM admins WHERE email = %s"
    cursor.execute(query, (email_upper,))
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
        stored_emb = r.get('face_embedding')
        if stored_emb:
            if isinstance(stored_emb, (bytes, bytearray)):
                emb = np.array(json.loads(stored_emb.decode('utf-8')))
            elif isinstance(stored_emb, str):
                emb = np.array(json.loads(stored_emb))
            else:
                emb = np.array(stored_emb)
            
            dist = np.linalg.norm(emb - target)
            if best_distance is None or dist < best_distance:
                best_distance = float(dist)
                best_id = str(r['id'])
    
    cursor.close()
    db.close()
    
    if best_distance is not None and best_distance <= threshold:
        return best_id, best_distance
    return None, None

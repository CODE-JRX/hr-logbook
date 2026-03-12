from db import get_db, get_db_cursor
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import numpy as np
import json
import mysql.connector
from models.office_model import get_office_id_by_name

# Global cache for admin face embeddings
# Structure: list of {'id': str, 'face_embedding': list of np.array}
_ADMIN_FACE_CACHE = None

def get_admin_face_cache(force_refresh=False):
    global _ADMIN_FACE_CACHE
    if _ADMIN_FACE_CACHE is None or force_refresh:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, face_embedding FROM admins WHERE face_embedding IS NOT NULL")
            rows = cursor.fetchall()
            new_cache = []
            for r in rows:
                try:
                    stored_json = r.get('face_embedding')
                    if not stored_json: continue
                        
                    if isinstance(stored_json, (bytes, bytearray)):
                        stored_data = json.loads(stored_json.decode('utf-8'))
                    elif isinstance(stored_json, str):
                        stored_data = json.loads(stored_json)
                    else:
                        stored_data = stored_json
                        
                    candidates = []
                    if isinstance(stored_data, list) and len(stored_data) > 0:
                        if isinstance(stored_data[0], list):
                            candidates = [np.array(e) for e in stored_data]
                        else:
                            candidates = [np.array(stored_data)]
                    
                    if candidates:
                        new_cache.append({
                            'id': str(r['id']),
                            'embeddings': candidates
                        })
                except Exception as e:
                    print(f"Error caching admin embedding for {r.get('id')}: {e}")
            _ADMIN_FACE_CACHE = new_cache
    return _ADMIN_FACE_CACHE

def add_admin(first_name, last_name, email, password, embedding_list=None, pin=None, office=None):
    ph = generate_password_hash(password)
    pin_hash = generate_password_hash(pin) if pin else None
    
    # Convert office name to ID if it's a string (e.g. "REGISTRAR" -> 5)
    office_id = office
    if office and isinstance(office, str) and not office.isdigit():
        from models.office_model import get_office_id_by_name
        office_id = get_office_id_by_name(office)

    query = """INSERT INTO admins (first_name, last_name, email, password_hash, pin_hash, office, face_embedding, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    values = (
        first_name.upper() if isinstance(first_name, str) else first_name,
        last_name.upper() if isinstance(last_name, str) else last_name,
        email.lower() if isinstance(email, str) else email,
        ph,
        pin_hash,
        office_id,
        json.dumps(embedding_list) if embedding_list else None,
        datetime.now()
    )
    
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, values)
            last_id = cursor.lastrowid
            
            # Update cache if initialized
            global _ADMIN_FACE_CACHE
            if _ADMIN_FACE_CACHE is not None and embedding_list:
                candidates = []
                if isinstance(embedding_list[0], list):
                    candidates = [np.array(e) for e in embedding_list]
                else:
                    candidates = [np.array(embedding_list)]
                
                _ADMIN_FACE_CACHE.append({
                    'id': str(last_id),
                    'embeddings': candidates
                })
                
            return str(last_id)
    except mysql.connector.Error as err:
        print(f"Error adding admin: {err}")
        return None

def get_admin_by_email(email):
    with get_db_cursor() as cursor:
        email_lower = email.lower() if isinstance(email, str) else email
        
        query = """SELECT a.*, o.name as office_name 
                   FROM admins a
                   LEFT JOIN offices o ON a.office = o.id
                   WHERE a.email = %s"""
        cursor.execute(query, (email_lower,))
        admin = cursor.fetchone()
        
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
    with get_db_cursor() as cursor:
        query = """SELECT a.*, o.name as office_name 
                   FROM admins a
                   LEFT JOIN offices o ON a.office = o.id
                   WHERE a.id = %s"""
        cursor.execute(query, (admin_id,))
        admin = cursor.fetchone()
        
        if admin:
            admin['id'] = str(admin['id'])
            emb_data = admin.get('face_embedding')
            if isinstance(emb_data, (bytes, bytearray)):
                admin['face_embedding'] = json.loads(emb_data.decode('utf-8'))
            elif isinstance(emb_data, str):
                admin['face_embedding'] = json.loads(emb_data)
        return admin

def update_admin_password(admin_id, new_password):
    ph = generate_password_hash(new_password)
    
    query = "UPDATE admins SET password_hash = %s, updated_at = %s WHERE id = %s"
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, (ph, datetime.now(), admin_id))
            return cursor.rowcount > 0
    except mysql.connector.Error:
        return False

def find_best_admin_match(embedding_list, threshold=0.6):
    cache = get_admin_face_cache()
    if not cache:
        return None, None
        
    target = np.array(embedding_list)
    best_id = None
    best_distance = None
    
    for item in cache:
        # Check against all candidates for this admin
        for emb in item['embeddings']:
            try:
                dist = np.linalg.norm(emb - target)
                if best_distance is None or dist < best_distance:
                    best_distance = float(dist)
                    best_id = item['id']
            except Exception as e:
                print(f"Error comparing admin embedding for {item['id']}: {e}")
                continue
    
    if best_distance is not None and best_distance <= threshold:
        return best_id, best_distance
    return None, None

def get_all_admins(office_id=None):
    """Get all admins, optionally filtered by office.
    
    Args:
        office_id: Optional office ID to filter by. If None, returns all admins.
    
    Returns:
        List of admin dictionaries with id, first_name, last_name, email, office_name, created_at.
    """
    with get_db_cursor() as cursor:
        if office_id:
            query = """SELECT a.id, a.first_name, a.last_name, a.email, a.office, 
                              o.name as office_name, a.created_at, a.updated_at
                       FROM admins a
                       LEFT JOIN offices o ON a.office = o.id
                       WHERE a.office = %s
                       ORDER BY a.first_name, a.last_name"""
            cursor.execute(query, (office_id,))
        else:
            query = """SELECT a.id, a.first_name, a.last_name, a.email, a.office, 
                              o.name as office_name, a.created_at, a.updated_at
                       FROM admins a
                       LEFT JOIN offices o ON a.office = o.id
                       ORDER BY o.name, a.first_name, a.last_name"""
            cursor.execute(query)
        
        admins = cursor.fetchall()
        return admins if admins else []

def update_admin(admin_id, first_name=None, last_name=None, email=None, office=None):
    """Update admin details.
    
    Args:
        admin_id: ID of admin to update
        first_name: Optional new first name
        last_name: Optional new last name
        email: Optional new email
        office: Optional new office ID
    
    Returns:
        True if update successful, False otherwise.
    """
    updates = []
    values = []
    
    if first_name is not None:
        updates.append("first_name = %s")
        values.append(first_name.upper() if isinstance(first_name, str) else first_name)
    
    if last_name is not None:
        updates.append("last_name = %s")
        values.append(last_name.upper() if isinstance(last_name, str) else last_name)
    
    if email is not None:
        updates.append("email = %s")
        values.append(email.lower() if isinstance(email, str) else email)
    
    if office is not None:
        updates.append("office = %s")
        values.append(office)
    
    if not updates:
        return False
    
    updates.append("updated_at = %s")
    values.append(datetime.now())
    values.append(admin_id)
    
    query = f"UPDATE admins SET {', '.join(updates)} WHERE id = %s"
    
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, tuple(values))
            
            # Refresh cache on update
            global _ADMIN_FACE_CACHE
            _ADMIN_FACE_CACHE = None
            
            return cursor.rowcount > 0
    except mysql.connector.Error as err:
        print(f"Error updating admin: {err}")
        return False

def delete_admin(admin_id):
    """Delete an admin by ID.
    
    Args:
        admin_id: ID of admin to delete
    
    Returns:
        True if deletion successful, False otherwise.
    """
    query = "DELETE FROM admins WHERE id = %s"
    
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, (admin_id,))
            
            # Refresh cache on delete
            global _ADMIN_FACE_CACHE
            _ADMIN_FACE_CACHE = None
            
            return cursor.rowcount > 0
    except mysql.connector.Error as err:
        print(f"Error deleting admin: {err}")
        return False

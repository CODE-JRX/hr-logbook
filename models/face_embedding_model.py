import json
from db import get_db, get_db_cursor
import numpy as np
import mysql.connector
from datetime import datetime

# Global cache for face embeddings
# Structure: list of {'id': int, 'client_id': str, 'embedding': np.array}
_FACE_CACHE = None

def get_face_cache(force_refresh=False):
    global _FACE_CACHE
    if _FACE_CACHE is None or force_refresh:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, client_id, embedding_json FROM face_embeddings")
            rows = cursor.fetchall()
            new_cache = []
            for r in rows:
                try:
                    stored_emb = r.get('embedding_json')
                    if isinstance(stored_emb, (bytes, bytearray)):
                        emb = np.array(json.loads(stored_emb.decode('utf-8')))
                    elif isinstance(stored_emb, str):
                        emb = np.array(json.loads(stored_emb))
                    else:
                        emb = np.array(stored_emb)
                    
                    new_cache.append({
                        'id': r.get('id'),
                        'client_id': r.get('client_id'),
                        'embedding': emb
                    })
                except Exception as e:
                    print(f"Error caching embedding for {r.get('client_id')}: {e}")
            _FACE_CACHE = new_cache
    return _FACE_CACHE

def add_face_embedding(client_id, embedding_list):
    with get_db_cursor(commit=True) as cursor:
        client_id_upper = client_id.upper() if isinstance(client_id, str) else client_id
        query = "INSERT INTO face_embeddings (client_id, embedding_json) VALUES (%s, %s)"
        cursor.execute(query, (client_id_upper, json.dumps(embedding_list)))
        last_id = cursor.lastrowid
        
        # Update cache if initialized
        cache = get_face_cache()
        cache.append({
            'id': last_id,
            'client_id': client_id_upper,
            'embedding': np.array(embedding_list)
        })


def delete_embeddings_by_client_id(client_id):
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM face_embeddings WHERE client_id = %s", (client_id,))
    
    # Update cache
    global _FACE_CACHE
    if _FACE_CACHE is not None:
        _FACE_CACHE = [item for item in _FACE_CACHE if item['client_id'] != client_id]

def update_face_embedding(client_id, embedding_list):
    # For a full update where we replace all embeddings (e.g. from edit page with 3 angles),
    # we should clear old ones first.
    # However, this function signature suggests a single embedding update. 
    # To be safe and flexible, let's just use add_face_embedding after clearing manually in the route if needed.
    # Or we can make this function clear and add. 
    # But since we might add 3 embeddings, let's keep this simple:
    # This specific function might be deprecated in favor of manual delete + add loop in route.
    pass

def get_embedding_by_client_id(client_id):
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM face_embeddings WHERE client_id = %s LIMIT 1", (client_id,))
        row = cursor.fetchone()
        if row:
            row['employee_id'] = row['client_id']
            emb_data = row.get('embedding_json')
            if isinstance(emb_data, (bytes, bytearray)):
                row['embedding_json'] = json.loads(emb_data.decode('utf-8'))
            elif isinstance(emb_data, str):
                row['embedding_json'] = json.loads(emb_data)
        return row

def find_best_match(embedding_list, threshold=0.7):
    cache = get_face_cache()
    if not cache:
        return None, None
        
    target = np.array(embedding_list)
    best_id = None
    best_distance = None
    
    for item in cache:
        try:
            dist = np.linalg.norm(item['embedding'] - target)
            if best_distance is None or dist < best_distance:
                best_distance = float(dist)
                best_id = item['client_id']
        except Exception as e:
            print(f"Error comparing embedding for {item['client_id']}: {e}")
            continue

    print(f"Face Match Debug (Cached): Checked {len(cache)} embeddings. Best ID: {best_id}, Best Dist: {best_distance}, Threshold: {threshold}")

    if best_distance is not None and best_distance <= threshold:
        return best_id, best_distance
    return None, None

def get_embeddings_by_client_id(client_id):
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM face_embeddings WHERE client_id = %s", (client_id,))
        rows = cursor.fetchall()
        for row in rows:
            emb_data = row.get('embedding_json')
            if isinstance(emb_data, (bytes, bytearray)):
                 row['embedding_json'] = json.loads(emb_data.decode('utf-8'))
            elif isinstance(emb_data, str):
                 row['embedding_json'] = json.loads(emb_data)
        return rows

def improve_client_embedding(client_id, new_embedding, match_threshold=0.5, merge_threshold=0.25, max_embeddings=3):
    existing_docs = get_embeddings_by_client_id(client_id)
    
    if not existing_docs:
        add_face_embedding(client_id, new_embedding)
        return "added_initial"

    target = np.array(new_embedding)
    closest_doc = None
    closest_dist = float('inf')
    
    for doc in existing_docs:
        emb = np.array(doc.get('embedding_json'))
        dist = np.linalg.norm(emb - target)
        if dist < closest_dist:
            closest_dist = dist
            closest_doc = doc
            closest_emb = emb

    if closest_dist > match_threshold:
        if closest_dist > 0.75: 
             return "rejected_outlier"

    # For update/insert we'll use a new cursor context
    
    if closest_dist < merge_threshold:
        with get_db_cursor(commit=True) as cursor:
            new_vec = (closest_emb * 0.8) + (target * 0.2)
            cursor.execute("UPDATE face_embeddings SET embedding_json = %s, updated_at = %s WHERE id = %s",
                           (json.dumps(new_vec.tolist()), datetime.now(), closest_doc['id']))
            
            # Update cache
            cache = get_face_cache()
            for item in cache:
                if item['id'] == closest_doc['id']:
                    item['embedding'] = new_vec
                    break
            return "merged_existing"

    if len(existing_docs) < max_embeddings:
        with get_db_cursor(commit=True) as cursor:
            query = "INSERT INTO face_embeddings (client_id, embedding_json) VALUES (%s, %s)"
            cursor.execute(query, (client_id.upper(), json.dumps(new_embedding)))
            last_id = cursor.lastrowid
            
            # Update cache
            cache = get_face_cache()
            cache.append({
                'id': last_id,
                'client_id': client_id.upper(),
                'embedding': np.array(new_embedding)
            })
            return "added_new_variant"

    if closest_doc:
        with get_db_cursor(commit=True) as cursor:
            new_vec = (closest_emb * 0.7) + (target * 0.3)
            cursor.execute("UPDATE face_embeddings SET embedding_json = %s, updated_at = %s WHERE id = %s",
                           (json.dumps(new_vec.tolist()), datetime.now(), closest_doc['id']))
            
            # Update cache
            cache = get_face_cache()
            for item in cache:
                if item['id'] == closest_doc['id']:
                    item['embedding'] = new_vec
                    break
            return "merged_limit_reached"

    return "no_action"

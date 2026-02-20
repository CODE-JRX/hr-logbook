import json
from db import get_db
import numpy as np
import mysql.connector
from datetime import datetime

def add_face_embedding(client_id, embedding_list):
    db = get_db()
    cursor = db.cursor()
    query = "INSERT INTO face_embeddings (client_id, embedding_json) VALUES (%s, %s)"
    cursor.execute(query, (client_id.upper() if isinstance(client_id, str) else client_id, json.dumps(embedding_list)))
    db.commit()
    cursor.close()
    db.close()


def delete_embeddings_by_client_id(client_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM face_embeddings WHERE client_id = %s", (client_id,))
    db.commit()
    cursor.close()
    db.close()

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
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM face_embeddings WHERE client_id = %s LIMIT 1", (client_id,))
    row = cursor.fetchone()
    if row:
        row['employee_id'] = row['client_id']
        emb_data = row.get('embedding_json')
        if isinstance(emb_data, (bytes, bytearray)):
            row['embedding_json'] = json.loads(emb_data.decode('utf-8'))
        elif isinstance(emb_data, str):
            row['embedding_json'] = json.loads(emb_data)
    cursor.close()
    db.close()
    return row

def find_best_match(embedding_list, threshold=0.7):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT client_id, embedding_json FROM face_embeddings")
    
    target = np.array(embedding_list)
    best_id = None
    best_distance = None
    count = 0
    
    for r in cursor:
        count += 1
        try:
            stored_emb = r.get('embedding_json')
            if isinstance(stored_emb, (bytes, bytearray)):
                emb = np.array(json.loads(stored_emb.decode('utf-8')))
            elif isinstance(stored_emb, str):
                emb = np.array(json.loads(stored_emb))
            else:
                emb = np.array(stored_emb)
                
            dist = np.linalg.norm(emb - target)
            if best_distance is None or dist < best_distance:
                best_distance = float(dist)
                best_id = r.get('client_id')
        except Exception as e:
            print(f"Error processing embedding for {r.get('client_id')}: {e}")
            continue

    cursor.close()
    db.close()

    print(f"Face Match Debug: Checked {count} embeddings. Best ID: {best_id}, Best Dist: {best_distance}, Threshold: {threshold}")

    if best_distance is not None and best_distance <= threshold:
        return best_id, best_distance
    return None, None

def get_embeddings_by_client_id(client_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM face_embeddings WHERE client_id = %s", (client_id,))
    rows = cursor.fetchall()
    for row in rows:
        emb_data = row.get('embedding_json')
        if isinstance(emb_data, (bytes, bytearray)):
             row['embedding_json'] = json.loads(emb_data.decode('utf-8'))
        elif isinstance(emb_data, str):
             row['embedding_json'] = json.loads(emb_data)
    cursor.close()
    db.close()
    return rows

def improve_client_embedding(client_id, new_embedding, match_threshold=0.5, merge_threshold=0.25, max_embeddings=3):
    db = get_db()
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

    cursor = db.cursor()
    if closest_dist < merge_threshold:
        new_vec = (closest_emb * 0.8) + (target * 0.2)
        cursor.execute("UPDATE face_embeddings SET embedding_json = %s, updated_at = %s WHERE id = %s",
                       (json.dumps(new_vec.tolist()), datetime.now(), closest_doc['id']))
        db.commit()
        cursor.close()
        db.close()
        return "merged_existing"

    if len(existing_docs) < max_embeddings:
        query = "INSERT INTO face_embeddings (client_id, embedding_json) VALUES (%s, %s)"
        cursor.execute(query, (client_id.upper(), json.dumps(new_embedding)))
        db.commit()
        cursor.close()
        db.close()
        return "added_new_variant"

    if closest_doc:
        new_vec = (closest_emb * 0.7) + (target * 0.3)
        cursor.execute("UPDATE face_embeddings SET embedding_json = %s, updated_at = %s WHERE id = %s",
                       (json.dumps(new_vec.tolist()), datetime.now(), closest_doc['id']))
        db.commit()
        cursor.close()
        db.close()
        return "merged_limit_reached"

    cursor.close()
    db.close()
    return "no_action"

import json
from db import get_db
import numpy as np


def add_face_embedding(client_id, embedding_list):
    """Insert a face embedding (list of floats) as JSON into face_embeddings."""
    db = get_db()
    # embedding_list is already a list of floats
    # In MongoDB we can store attributes directly, avoiding the JSON string if we want,
    # but to minimize friction with existing logic (if any relies on structure),
    # we will store it. However, Mongo supports array natively.
    # The Schema script says: embedding_json: { bsonType: "array", items: { bsonType: "double" } }
    # So we should store it as an ARRAY, not a JSON string.
    # But wait, existing code passed `json.dumps`. The schema says `embedding_json` is an array.
    # I should store it as an array to respect the schema.
    
    db.face_embeddings.insert_one({
        "client_id": client_id.upper() if isinstance(client_id, str) else client_id, # Schema calls it client_id
        "embedding_json": embedding_list # Store as list directly per schema
    })


def get_embedding_by_client_id(client_id):
    db = get_db()
    # Note: schema uses 'client_id'
    row = db.face_embeddings.find_one({"client_id": client_id})
    if row:
        # Compatibility: The caller might expect 'employee_id' key
        row['employee_id'] = row['client_id']
        # And 'embedding_json' might be expected as a string if the caller does json.loads?
        # Let's check `find_best_match` below.
        pass
    return row


def find_best_match(embedding_list, threshold=0.6):
    """Find the closest stored embedding to the given embedding_list."""
    db = get_db()
    # Fetch all embeddings
    # Optim: Project only needed fields
    cursor = db.face_embeddings.find({}, {"client_id": 1, "embedding_json": 1})
    
    target = np.array(embedding_list)
    best_id = None
    best_distance = None
    
    for r in cursor:
        try:
            # Schema says embedding_json is array of double.
            # So r['embedding_json'] should be a list.
            # If migration/seeding used json string, this checks both.
            stored_emb = r.get('embedding_json')
            if isinstance(stored_emb, str):
                emb = np.array(json.loads(stored_emb))
            else:
                emb = np.array(stored_emb)
                
            dist = np.linalg.norm(emb - target)
            if best_distance is None or dist < best_distance:
                best_distance = float(dist)
                best_id = r.get('client_id')
        except Exception:
            continue

    if best_distance is not None and best_distance <= threshold:
        return best_id, best_distance
    return None, None


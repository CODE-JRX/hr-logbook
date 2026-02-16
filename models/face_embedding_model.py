import json
from db import get_db
import numpy as np


def add_face_embedding(client_id, embedding_list):
    """Insert a face embedding (list of floats) as JSON into face_embeddings."""
    db = get_db()
    
    db.face_embeddings.insert_one({
        "client_id": client_id.upper() if isinstance(client_id, str) else client_id, # Schema calls it client_id
        "embedding_json": embedding_list # Store as list directly per schema
    })

def update_face_embedding(client_id, embedding_list):
    """Update or insert a face embedding."""
    db = get_db()
    db.face_embeddings.update_one(
        {"client_id": client_id.upper() if isinstance(client_id, str) else client_id},
        {"$set": {"embedding_json": embedding_list}},
        upsert=True
    )


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


def get_embeddings_by_client_id(client_id):
    """Retrieve all embedding documents for a client."""
    db = get_db()
    return list(db.face_embeddings.find({"client_id": client_id}))


def improve_client_embedding(client_id, new_embedding, match_threshold=0.5, merge_threshold=0.25, max_embeddings=3):
    """
    Intelligently update the client's face embeddings.
    
    Strategy:
    1. If new_embedding is surprisingly far from ALL existing ( > match_threshold), 
       do NOT update (safety check against poisoning with wrong face).
       However, the caller should have already verified this is the correct user (e.g. by manual override or previous match).
       We will assume the caller trusts this is 'client_id'. 
       BUT if it's too far, we might still want to reject it to be safe.
       
    2. checks distance to existing embeddings.
    3. If very close ( < merge_threshold) to an existing one -> Weighted Average update.
    4. If moderately different (but within match_threshold) -> Insert new embedding (if count < max).
    5. If count >= max -> Replace the one that is closest (merge) OR 
       replace the oldest/least-used (simplified: replace random or create a rolling buffer).
       For now: merge with the closest one to keep the 'center' of that cluster moving.
    """
    db = get_db()
    existing_docs = get_embeddings_by_client_id(client_id)
    
    # If no embeddings exist, just add it (though this is rare if they are logging in)
    if not existing_docs:
        add_face_embedding(client_id, new_embedding)
        return "added_initial"

    # 1. Calculate distances to all existing embeddings
    target = np.array(new_embedding)
    closest_doc = None
    closest_dist = float('inf')
    
    valid_encodings = []

    for doc in existing_docs:
        # Parse stored embedding
        stored_emb = doc.get('embedding_json')
        if isinstance(stored_emb, str):
            emb = np.array(json.loads(stored_emb))
        else:
            emb = np.array(stored_emb)
        
        valid_encodings.append((doc, emb))
        
        dist = np.linalg.norm(emb - target)
        if dist < closest_dist:
            closest_dist = dist
            closest_doc = doc
            closest_emb = emb

    # Safety: If the best match is too far, this face might not be them (or a very bad capture).
    # If the user was MANUALLY identified, we might still want to add it, but let's be cautious.
    if closest_dist > match_threshold:
        # OPTIONAL: return "rejected_too_far"
        # For now, we trust the 'client_id' assertion but maybe add as new if we have space?
        # Let's enforce a loose threshold to prevent pollution.
        # 0.6 is dlib's strict match. 0.7 or 0.8 is safer for "different look same person".
        if closest_dist > 0.75: 
             return "rejected_outlier"

    # 2. Update logic
    
    # Case A: Very close match (e.g. same face, similar angle) -> Merge/Average
    if closest_dist < merge_threshold:
        # Weighted update: 80% old, 20% new to reduce drift
        new_vec = (closest_emb * 0.8) + (target * 0.2)
        # Normalize? dlib encodings are usually approx unit length, but good to keep it clean.
        # But simple averaging is usually fine for these 128d vectors.
        
        db.face_embeddings.update_one(
            {"_id": closest_doc["_id"]},
            {"$set": {"embedding_json": new_vec.tolist(), "updated_at": datetime.now()}}
        )
        return "merged_existing"

    # Case B: Distinct enough to be a new 'look', but valid user
    # If we have space, add it.
    if len(existing_docs) < max_embeddings:
        add_face_embedding(client_id, new_embedding)
        return "added_new_variant"

    # Case C: No space, but distinct.
    # We should merge it into the closest one to maintain that cluster's center,
    # OR replace the oldest. 
    # Let's merge into closest to keep the representation robust.
    # Weighted: 70% old, 30% new (give a bit more weight to recent change)
    if closest_doc:
        new_vec = (closest_emb * 0.7) + (target * 0.3)
        db.face_embeddings.update_one(
            {"_id": closest_doc["_id"]},
            {"$set": {"embedding_json": new_vec.tolist(), "updated_at": datetime.now()}}
        )
        return "merged_limit_reached"

    return "no_action"

import json
from db import get_db_connection
import numpy as np
import face_recognition


def add_face_embedding(employee_id, embedding_list):
    """Insert a face embedding (list of floats) as JSON into face_embeddings."""
    conn = get_db_connection()
    cursor = conn.cursor()
    embedding_json = json.dumps(embedding_list)
    cursor.execute(
        "INSERT INTO face_embeddings (employee_id, embedding_json) VALUES (%s, %s)",
        (employee_id, embedding_json)
    )
    conn.commit()
    conn.close()


def get_embedding_by_employee_id(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM face_embeddings WHERE employee_id=%s", (employee_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def find_best_match(embedding_list, threshold=0.6):
    """Find the closest stored embedding to the given embedding_list.
    Returns a tuple (employee_id, distance) or (None, None) if no match below threshold.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT employee_id, embedding_json FROM face_embeddings")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None, None

    target = np.array(embedding_list)
    best_id = None
    best_distance = None
    for r in rows:
        try:
            emb = np.array(json.loads(r['embedding_json']))
            dist = np.linalg.norm(emb - target)
            if best_distance is None or dist < best_distance:
                best_distance = float(dist)
                best_id = r['employee_id']
        except Exception:
            continue

    if best_distance is not None and best_distance <= threshold:
        return best_id, best_distance
    return None, None

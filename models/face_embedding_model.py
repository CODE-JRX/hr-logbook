import json
import logging
import threading
from db import get_db, get_db_cursor
import numpy as np
import mysql.connector
from datetime import datetime

logger = logging.getLogger(__name__)

# Global cache for face embeddings with thread safety
# Structure: list of {'id': int, 'client_id': str, 'embedding': np.array}
_FACE_CACHE = None
_FACE_CACHE_LOCK = threading.RLock()  # Reentrant lock for thread safety

def get_face_cache(force_refresh=False):
    """
    Get face embeddings cache with thread-safe access.
    
    Args:
        force_refresh: Force reload from database
    
    Returns:
        List of cached embeddings
    """
    global _FACE_CACHE
    
    with _FACE_CACHE_LOCK:
        if _FACE_CACHE is None or force_refresh:
            logger.info("Loading face embeddings cache from database...")
            try:
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
                        except json.JSONDecodeError as e:
                            logger.warning(f"Corrupt embedding JSON for {r.get('client_id')}: {e}")
                            continue
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Cannot convert embedding for {r.get('client_id')}: {e}")
                            continue
                        except Exception as e:
                            logger.error(f"Error caching embedding for {r.get('client_id')}: {e}")
                            continue
                    
                    _FACE_CACHE = new_cache
                    logger.info(f"Loaded {len(new_cache)} client face embeddings")
                    
            except Exception as e:
                logger.error(f"Failed to load face cache: {e}")
                _FACE_CACHE = []  # Use empty cache as fallback
        
        return _FACE_CACHE

def add_face_embedding(client_id, embedding_list):
    """
    Add a new face embedding to database and cache.
    
    Args:
        client_id: Client identifier
        embedding_list: Face embedding as list
    
    Returns:
        Embedding ID or None if failed
    """
    try:
        with get_db_cursor(commit=True) as cursor:
            client_id_upper = client_id.upper() if isinstance(client_id, str) else client_id
            query = "INSERT INTO face_embeddings (client_id, embedding_json) VALUES (%s, %s)"
            cursor.execute(query, (client_id_upper, json.dumps(embedding_list)))
            last_id = cursor.lastrowid
            logger.info(f"Added embedding for {client_id_upper}")
            
            # Update cache if initialized (thread-safe)
            with _FACE_CACHE_LOCK:
                if _FACE_CACHE is not None:
                    _FACE_CACHE.append({
                        'id': last_id,
                        'client_id': client_id_upper,
                        'embedding': np.array(embedding_list)
                    })
            
            return last_id
    except Exception as e:
        logger.error(f"Failed to add embedding for {client_id}: {e}")
        raise


def delete_embeddings_by_client_id(client_id):
    """
    Delete all embeddings for a client from database and cache.
    
    Args:
        client_id: Client identifier
    """
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("DELETE FROM face_embeddings WHERE client_id = %s", (client_id,))
            logger.info(f"Deleted embeddings for {client_id}")
        
        # Update cache (thread-safe)
        with _FACE_CACHE_LOCK:
            global _FACE_CACHE
            if _FACE_CACHE is not None:
                _FACE_CACHE = [item for item in _FACE_CACHE if item['client_id'] != client_id]
    except Exception as e:
        logger.error(f"Failed to delete embeddings for {client_id}: {e}")
        raise


def get_embedding_by_client_id(client_id):
    """Get first embedding for a client from database."""
    try:
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
    except Exception as e:
        logger.error(f"Failed to get embedding for {client_id}: {e}")
        raise


def find_best_match(embedding_list, threshold=0.7):
    """
    Find the best matching client for a face embedding.
    
    Args:
        embedding_list: Face embedding as list
        threshold: Distance threshold for match (lower = stricter)
    
    Returns:
        Tuple of (client_id, distance) or (None, None) if no match
    """
    try:
        cache = get_face_cache()
        if not cache:
            logger.warning("Face cache is empty")
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
                logger.warning(f"Error comparing embedding for {item['client_id']}: {e}")
                continue

        logger.debug(f"Face match: checked {len(cache)} embeddings, best={best_id}, dist={best_distance}, threshold={threshold}")

        if best_distance is not None and best_distance <= threshold:
            return best_id, best_distance
        return None, None
        
    except Exception as e:
        logger.error(f"Error in face matching: {e}")
        return None, None


def get_embeddings_by_client_id(client_id):
    """Get all embeddings for a client."""
    try:
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
    except Exception as e:
        logger.error(f"Failed to get embeddings for {client_id}: {e}")
        raise


def improve_client_embedding(client_id, new_embedding, match_threshold=0.5, merge_threshold=0.25, max_embeddings=3):
    """
    Intelligently add or merge a new embedding with existing ones.
    
    Args:
        client_id: Client identifier
        new_embedding: New face embedding as list
        match_threshold: Threshold for strong match
        merge_threshold: Threshold for merging
        max_embeddings: Maximum embeddings to store per client
    
    Returns:
        Status string: 'added_initial', 'merged_existing', 'added_new_variant', etc.
    """
    try:
        existing_docs = get_embeddings_by_client_id(client_id)
        
        if not existing_docs:
            add_face_embedding(client_id, new_embedding)
            return "added_initial"

        target = np.array(new_embedding)
        closest_doc = None
        closest_dist = float('inf')
        
        for doc in existing_docs:
            try:
                emb = np.array(doc.get('embedding_json'))
                dist = np.linalg.norm(emb - target)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_doc = doc
                    closest_emb = emb
            except Exception as e:
                logger.warning(f"Error comparing embeddings: {e}")
                continue

        if closest_dist > match_threshold:
            if closest_dist > 0.75: 
                logger.warning(f"Rejected outlier embedding for {client_id}: distance={closest_dist}")
                return "rejected_outlier"

        if closest_dist < merge_threshold and closest_doc:
            with get_db_cursor(commit=True) as cursor:
                new_vec = (closest_emb * 0.8) + (target * 0.2)
                cursor.execute("UPDATE face_embeddings SET embedding_json = %s, updated_at = %s WHERE id = %s",
                               (json.dumps(new_vec.tolist()), datetime.now(), closest_doc['id']))
            
            # Update cache (thread-safe)
            with _FACE_CACHE_LOCK:
                if _FACE_CACHE is not None:
                    for item in _FACE_CACHE:
                        if item['id'] == closest_doc['id']:
                            item['embedding'] = new_vec
                            break
            logger.info(f"Merged embedding for {client_id}")
            return "merged_existing"

        if len(existing_docs) < max_embeddings:
            add_face_embedding(client_id, new_embedding)
            logger.info(f"Added new variant for {client_id}")
            return "added_new_variant"

        if closest_doc:
            with get_db_cursor(commit=True) as cursor:
                new_vec = (closest_emb * 0.7) + (target * 0.3)
                cursor.execute("UPDATE face_embeddings SET embedding_json = %s, updated_at = %s WHERE id = %s",
                               (json.dumps(new_vec.tolist()), datetime.now(), closest_doc['id']))
            
            # Update cache (thread-safe)
            with _FACE_CACHE_LOCK:
                if _FACE_CACHE is not None:
                    for item in _FACE_CACHE:
                        if item['id'] == closest_doc['id']:
                            item['embedding'] = new_vec
                            break
            logger.warning(f"Merged with limit reached for {client_id}")
            return "merged_limit_reached"

        return "no_action"
        
    except Exception as e:
        logger.error(f"Error improving embedding for {client_id}: {e}")
        raise


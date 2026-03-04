
import sys
import os
import json
import numpy as np

# Mocking parts of the system if needed, but let's try to run with real logic if possible
# Set up environment for imports
sys.path.append(os.getcwd())

from db import get_db_cursor
from models.face_embedding_model import (
    get_face_cache, 
    improve_client_embedding, 
    find_best_match, 
    delete_embeddings_by_client_id,
    _FACE_CACHE
)

def verify_learning_cache():
    print("Starting Learning Feature Cache Verification...")
    
    # Setup: Ensure test client exists
    with get_db_cursor(commit=True) as cursor:
        # First remove if exists
        cursor.execute("DELETE FROM clients WHERE client_id = 'TEST-001'")
        cursor.execute("INSERT INTO clients (client_id, fname, lname) VALUES ('TEST-001', 'Test', 'User')")

    # 1. Clear any existing test data for 'TEST-001'
    delete_embeddings_by_client_id('TEST-001')
    
    # 2. Initialize Cache
    cache = get_face_cache(force_refresh=True)
    initial_count = len(cache)
    print(f"Initial cache count: {initial_count}")
    
    # 3. Add initial embedding via improve_client_embedding
    # This should trigger add_face_embedding which updates cache
    test_emb_1 = (np.random.rand(128) * 0.1).tolist()
    res1 = improve_client_embedding('TEST-001', test_emb_1)
    print(f"Action 1 (Initial): {res1}")
    
    cache = get_face_cache()
    print(f"Cache count after initial: {len(cache)}")
    
    # Verify it's in cache
    found = any(item['client_id'] == 'TEST-001' for item in cache)
    if not found:
        print("FAIL: TEST-001 not found in cache after initial add")
        return
        
    # 4. Add a "new variant" (distinct enough but close enough to be accepted)
    # distance check in improve: match_threshold=0.5, merge_threshold=0.25
    # Let's make it 0.4 away
    test_emb_2 = (np.array(test_emb_1) + 0.05).tolist() # roughly 0.5 distance? let's be precise
    # dist = sqrt(sum((0.05)^2 * 128)) = sqrt(0.0025 * 128) = sqrt(0.32) ≈ 0.56
    # Let's use smaller offset to be sure it's within match_threshold (0.5) but outside merge (0.25)
    offset = 0.03
    test_emb_2 = (np.array(test_emb_1) + offset).tolist()
    # dist = sqrt(0.0009 * 128) = sqrt(0.1152) ≈ 0.34 (Matched variant)
    
    res2 = improve_client_embedding('TEST-001', test_emb_2)
    print(f"Action 2 (New Variant): {res2}")
    
    cache = get_face_cache()
    test_items = [item for item in cache if item['client_id'] == 'TEST-001']
    print(f"TEST-001 variants in cache: {len(test_items)}")
    
    if len(test_items) != 2:
        print(f"FAIL: Expected 2 variants in cache, found {len(test_items)}")
        # return
        
    # 5. Merge existing (very close)
    test_emb_3 = (np.array(test_emb_1) + 0.001).tolist()
    # dist ≈ 0.01 (Merge)
    
    # Capture old embedding value
    old_emb = test_items[0]['embedding'].copy()
    old_id = test_items[0]['id']
    
    res3 = improve_client_embedding('TEST-001', test_emb_3)
    print(f"Action 3 (Merge): {res3}")
    
    cache = get_face_cache()
    new_item = next(item for item in cache if item['id'] == old_id)
    
    if np.array_equal(new_item['embedding'], old_emb):
        print("FAIL: Cache embedding did not change after merge")
    else:
        print("SUCCESS: Cache embedding updated after merge")
        
    # 6. Verify Match
    match_id, match_dist = find_best_match(test_emb_1)
    print(f"Match verify: ID={match_id}, Dist={match_dist}")
    
    if match_id == 'TEST-001':
        print("VERIFICATION COMPLETE: Learning and Caching are working together.")
    else:
        print(f"FAIL: find_best_match returned {match_id}")

    # Cleanup
    delete_embeddings_by_client_id('TEST-001')
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM clients WHERE client_id = 'TEST-001'")

if __name__ == "__main__":
    verify_learning_cache()

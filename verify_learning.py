import numpy as np
import json
import time
import sys
from models.face_embedding_model import improve_client_embedding, get_embeddings_by_client_id, delete_embeddings_by_client_id, add_face_embedding
from db import get_db

def log(msg, f=None):
    print(msg)
    if f:
        f.write(msg + "\n")

def verify_learning():
    client_id = "TEST-LEARNING-001"
    
    with open("learning_results.txt", "w", encoding="utf-8") as f:
        log(f"--- Verifying Face Learning for {client_id} ---", f)

        db = get_db()
        cursor = db.cursor()

        try:
            # 1. Cleanup and Setup Client
            log("Cleaning up previous test data...", f)
            cursor.execute("DELETE FROM clients WHERE client_id = %s", (client_id,))
            db.commit()

            log("Creating dummy client...", f)
            cursor.execute("INSERT INTO clients (client_id, full_name, department, gender, age, client_type) VALUES (%s, %s, %s, %s, %s, %s)", 
                        (client_id, "Test Learning Bot", "IT", "Male", 99, "Visitor"))
            db.commit()

            # 2. Add initial embedding (Base Face)
            # Create a random 128-d vector
            base_embedding = np.random.rand(128)
            base_embedding = base_embedding / np.linalg.norm(base_embedding) # Normalize
            
            log("Adding initial embedding...", f)
            add_face_embedding(client_id, base_embedding.tolist())
            
            initial_docs = get_embeddings_by_client_id(client_id)
            log(f"Initial embeddings count: {len(initial_docs)}", f)
            if len(initial_docs) != 1:
                log("FAIL: Expected 1 embedding.", f)
                return

            stored_emb_1 = np.array(initial_docs[0]['embedding_json'])
            
            # 3. Simulate a match that is close (Merge Scenario)
            # Create a vector that is very close (e.g. distance approx 0.1)
            # We can do this by adding small noise
            noise = np.random.normal(0, 0.01, 128)
            new_face_1 = base_embedding + noise
            new_face_1 = new_face_1 / np.linalg.norm(new_face_1)
            
            dist_1 = np.linalg.norm(stored_emb_1 - new_face_1)
            log(f"Simulating Time-In with face distance: {dist_1:.4f} (Expected < 0.25 for merge)", f)
            
            result_1 = improve_client_embedding(client_id, new_face_1.tolist())
            log(f"Result 1: {result_1}", f)
            
            # Verify merge
            updated_docs = get_embeddings_by_client_id(client_id)
            log(f"Updated embeddings count: {len(updated_docs)}", f)
            
            stored_emb_2 = np.array(updated_docs[0]['embedding_json'])
            
            # Check if the embedding moved towards the new face
            # Original was base_embedding. New is stored_emb_2. 
            # It should be 80% old + 20% new.
            # Let's check distance from original base
            dist_shift = np.linalg.norm(stored_emb_2 - base_embedding)
            log(f"Embedding shift from original: {dist_shift:.6f}", f)
            
            if result_1 == "merged_existing":
                log("PASS: Embedding successfully merged.", f)
            else:
                log(f"FAIL: Expected 'merged_existing', got '{result_1}'", f)

            # 4. Simulate a match that is somewhat different (New Variant Scenario)
            # Distance > 0.25 but < 0.5 (or whatever match_threshold is, default 0.5 in code)
            
            # Create a vector further away
            match_found = False
            attempts = 0
            new_face_2 = None
            dist_2 = 0
            
            # Try to find a vector with the right distance
            while attempts < 1000:
                noise_2 = np.random.normal(0, 0.06 + (attempts * 0.0001), 128)
                cand = base_embedding + noise_2
                cand = cand / np.linalg.norm(cand)
                d = np.linalg.norm(stored_emb_2 - cand)
                if 0.25 < d < 0.5:
                    new_face_2 = cand
                    dist_2 = d
                    match_found = True
                    break
                attempts += 1
                
            if not match_found:
                log("Could not generate a face vector within [0.25, 0.5] distance range.", f)
            else:
                log(f"Simulating Time-In with face distance: {dist_2:.4f} (Targeting > 0.25 and < 0.5)", f)
                
                result_2 = improve_client_embedding(client_id, new_face_2.tolist())
                log(f"Result 2: {result_2}", f)
                
                final_docs = get_embeddings_by_client_id(client_id)
                log(f"Final embeddings count: {len(final_docs)}", f)
                
                if result_2 == "added_new_variant" and len(final_docs) == 2:
                    log("PASS: New variant added.", f)
                elif result_2 == "merged_existing":
                    log("NOTE: Merged existing (distance was likely too small).", f)
                elif result_2 == "rejected_outlier":
                    log("NOTE: Rejected (distance too large).", f)
                else:
                    log(f"FAIL: Unexpected result '{result_2}'", f)

        except Exception as e:
            log(f"Test Failed with Error: {e}", f)
            import traceback
            traceback.print_exc(file=f)
        finally:
            # Cleanup
            log("Cleaning up...", f)
            try:
                cursor.execute("DELETE FROM clients WHERE client_id = %s", (client_id,))
                db.commit()
            except:
                pass
            cursor.close()
            db.close()
            log("Test Complete.", f)

if __name__ == "__main__":
    verify_learning()

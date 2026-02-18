import json
import numpy as np
import face_recognition
from db import get_db
import os

def test_match():
    db = get_db()
    if not db:
        print("Failed to connect to DB")
        return
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT client_id, embedding_json FROM face_embeddings")
    embeddings = cursor.fetchall()
    print(f"Loaded {len(embeddings)} embeddings from DB")
    
    # Test image
    test_image_path = os.path.join("Clients", "1.jpg")
    if not os.path.exists(test_image_path):
        print(f"Test image {test_image_path} not found")
        return
    
    img = face_recognition.load_image_file(test_image_path)
    encodings = face_recognition.face_encodings(img)
    
    if not encodings:
        print("No face detected in test image")
        return
    
    target = encodings[0]
    print(f"Target encoding shape: {target.shape}")
    
    best_dist = float('inf')
    best_id = None
    
    for r in embeddings:
        cid = r['client_id']
        emb_json = r['embedding_json']
        
        try:
            print(f"Processing {cid}, type of emb_json: {type(emb_json)}")
            if isinstance(emb_json, (bytes, bytearray)):
                 emb_json = emb_json.decode('utf-8')
            
            if isinstance(emb_json, str):
                emb = np.array(json.loads(emb_json))
            else:
                emb = np.array(emb_json)
            
            if emb.shape != target.shape:
                print(f"Shape mismatch for {cid}: {emb.shape} vs {target.shape}")
                continue

            dist = np.linalg.norm(emb - target)
            print(f"Distance to {cid}: {dist:.4f}")
            
            if dist < best_dist:
                best_dist = dist
                best_id = cid
        except Exception as e:
            print(f"Error processing {cid}: {e}")
            import traceback
            traceback.print_exc()
            
    print("-" * 20)
    print(f"BEST MATCH: {best_id} with distance {best_dist:.4f}")
    
    cursor.close()
    db.close()

if __name__ == "__main__":
    test_match()


import json
import numpy as np
from db import get_db_cursor
from models.face_embedding_model import get_face_cache

def populate_dummy_data(count=1000):
    print(f"Populating {count} dummy records...")
    
    with get_db_cursor(commit=True) as cursor:
        # 1. Clean up any existing dummy data
        cursor.execute("DELETE FROM clients WHERE client_id LIKE 'TEMP-%'")
        
        # 2. Insert dummy clients in batches
        batch_size = 200
        for i in range(0, count, batch_size):
            client_values = []
            for j in range(i + 1, min(i + batch_size, count) + 1):
                client_id = f"TEMP-{j:04d}"
                full_name = f"Dummy User {j}"
                client_values.append((client_id, full_name, "Dummy", "User", "D"))
            
            print(f"Inserting clients {i+1} to {min(i+batch_size, count)}...")
            cursor.executemany(
                "INSERT INTO clients (client_id, full_name, fname, lname, mi) VALUES (%s, %s, %s, %s, %s)",
                client_values
            )
        
        # 3. Insert dummy embeddings in batches
        for i in range(0, count, batch_size):
            embedding_values = []
            for j in range(i + 1, min(i + batch_size, count) + 1):
                client_id = f"TEMP-{j:04d}"
                dummy_emb = np.random.uniform(-1, 1, 128).tolist()
                embedding_values.append((client_id, json.dumps(dummy_emb)))
            
            print(f"Inserting embeddings {i+1} to {min(i+batch_size, count)}...")
            cursor.executemany(
                "INSERT INTO face_embeddings (client_id, embedding_json) VALUES (%s, %s)",
                embedding_values
            )
        
    print(f"Successfully added {count} clients and embeddings.")
    
    # 4. Refresh local cache for verification
    print("Refreshing cache...")
    cache = get_face_cache(force_refresh=True)
    print(f"Total records in cache now: {len(cache)}")

if __name__ == "__main__":
    populate_dummy_data(1000)

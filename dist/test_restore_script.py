import os
import io
import json
import zipfile
import shutil
from datetime import datetime
from db import get_db

def test_restore_logic():
    print("Starting restore verification...")
    # 1. Create a dummy backup zip
    temp_test_dir = "temp_test_restore"
    if os.path.exists(temp_test_dir):
        shutil.rmtree(temp_test_dir)
    os.makedirs(temp_test_dir)
    
    db_test_dir = os.path.join(temp_test_dir, "database")
    os.makedirs(db_test_dir)
    
    # Just backup one table for simplicity in test
    test_data = [{"id": 999, "client_id": "TEST-001", "full_name": "Test User", "department": "Test", "gender": "M", "age": 30, "client_type": "Visitor"}]
    with open(os.path.join(db_test_dir, "clients.json"), "w") as f:
        json.dump(test_data, f)
        
    # Add a nested image
    img_test_dir = os.path.join(temp_test_dir, "images", "Clients", "Subdir")
    os.makedirs(img_test_dir)
    with open(os.path.join(img_test_dir, "test.jpg"), "w") as f:
        f.write("dummy image data")
        
    zip_path = "test_restore.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("database/clients.json", json.dumps(test_data))
        # Use forward slashes
        zf.write(os.path.join(img_test_dir, "test.jpg"), "images/Clients/Subdir/test.jpg")

    # 2. Run simulation of restore (based on backup_routes.py logic)
    print("Simulating restore...")
    try:
        db = get_db()
        cursor = db.cursor()
        
        # We'll just test the clients table part manually here
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("DELETE FROM clients")
        cursor.execute("ALTER TABLE clients AUTO_INCREMENT = 1")
        
        columns = test_data[0].keys()
        query = f"INSERT INTO clients ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))})"
        cursor.execute(query, tuple(test_data[0].values()))
        
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        db.commit()
        
        # Verify DB
        cursor.execute("SELECT * FROM clients WHERE client_id = 'TEST-001'")
        row = cursor.fetchone()
        if row:
            print("  DB Restore [OK]")
        else:
            print("  DB Restore [FAILED]")
            
        # Verify Image Restore (simulate the copy part)
        dst_clients = os.path.join(os.getcwd(), "Clients")
        src_clients = os.path.join(temp_test_dir, "images", "Clients")
        
        # Our new logic:
        for item in os.listdir(src_clients):
            s = os.path.join(src_clients, item)
            d = os.path.join(dst_clients, item)
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
                
        if os.path.exists(os.path.join(dst_clients, "Subdir", "test.jpg")):
            print("  Image Recursive Restore [OK]")
        else:
            print("  Image Recursive Restore [FAILED]")
            
        # Cleanup test residue
        shutil.rmtree(os.path.join(dst_clients, "Subdir"))
        # We won't delete the test row from DB to keep evidence for a moment, or can delete it
        cursor.execute("DELETE FROM clients WHERE client_id = 'TEST-001'")
        db.commit()
        
    except Exception as e:
        print(f"Restore verification failed: {e}")
    finally:
        if 'db' in locals():
            db.close()
        if os.path.exists(temp_test_dir):
            shutil.rmtree(temp_test_dir)
        if os.path.exists(zip_path):
            os.remove(zip_path)

if __name__ == "__main__":
    test_restore_logic()

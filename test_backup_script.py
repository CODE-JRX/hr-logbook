import os
import io
import json
import zipfile
from datetime import datetime, date
from db import get_db

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

TABLES = ['admins', 'clients', 'csm_form', 'face_embeddings', 'logs']

def test_backup():
    print("Starting backup simulation...")
    try:
        db = get_db()
        if not db:
            print("Failed to connect to database.")
            return
        
        cursor = db.cursor(dictionary=True)
        
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for table in TABLES:
                print(f"Processing table: {table}")
                cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                data = cursor.fetchall()
                if data:
                    print(f"  Sample row from {table}:")
                    for k, v in data[0].items():
                        print(f"    {k}: {type(v)} -> {v}")
                
                cursor.execute(f"SELECT * FROM {table}")
                data = cursor.fetchall()
                print(f"  Found {len(data)} rows.")
                
                # Check for potential JSON serialization issues
                try:
                    json_data = json.dumps(data, indent=2, cls=DateTimeEncoder)
                    zf.writestr(f"database/{table}.json", json_data)
                except Exception as json_err:
                    print(f"  JSON error in table {table}: {json_err}")
                    # Print first row to see what's in it
                    if data:
                        print(f"  First row: {data[0]}")
                    raise json_err
                
            # Clients images
            clients_dir = os.path.join(os.getcwd(), 'Clients')
            if os.path.exists(clients_dir):
                count = 0
                for root, dirs, files in os.walk(clients_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.join('images/Clients', os.path.relpath(file_path, clients_dir))
                        zf.write(file_path, arcname)
                        count += 1
                print(f"Added {count} images from Clients.")
            else:
                print("Clients directory not found.")

            # Admins images
            admins_dir = os.path.join(os.getcwd(), 'Admins')
            if os.path.exists(admins_dir):
                count = 0
                for root, dirs, files in os.walk(admins_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.join('images/Admins', os.path.relpath(file_path, admins_dir))
                        zf.write(file_path, arcname)
                        count += 1
                print(f"Added {count} images from Admins.")
            else:
                print("Admins directory not found.")

        cursor.close()
        db.close()
        print("Backup simulation successful.")
        
        with open("test_backup.zip", "wb") as f:
            f.write(memory_file.getvalue())
        print("Backup saved to test_backup.zip")

    except Exception as e:
        print(f"Backup simulation failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_backup()

import os
import io
import json
import zipfile
import traceback
from datetime import datetime, date
from db import get_db

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

TABLES = ['admins', 'clients', 'csm_form', 'face_embeddings', 'logs']

def run_diagnostics():
    log = []
    def log_print(msg):
        print(msg)
        log.append(str(msg))

    log_print("--- Backup Diagnostics ---")
    try:
        db = get_db()
        if not db:
            log_print("ERROR: get_db() returned None. Check DB connection.")
            return
        
        log_print("Successfully connected to DB.")
        cursor = db.cursor(dictionary=True)
        
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for table in TABLES:
                log_print(f"Table: {table}")
                try:
                    cursor.execute(f"SELECT * FROM {table}")
                    data = cursor.fetchall()
                    log_print(f"  Rows: {len(data)}")
                    
                    if data:
                        # Check sample row for types
                        log_print(f"  Sample row types:")
                        for k, v in data[0].items():
                            log_print(f"    {k}: {type(v)}")
                    
                    # Try serialize
                    json_data = json.dumps(data, indent=2, cls=DateTimeEncoder)
                    zf.writestr(f"database/{table}.json", json_data)
                    log_print(f"  Successfully serialized.")
                except Exception as table_err:
                    log_print(f"  FAILED Table {table}: {table_err}")
                    log_print(traceback.format_exc())

            # Images
            for folder in ['Clients', 'Admins']:
                dir_path = os.path.join(os.getcwd(), folder)
                if os.path.exists(dir_path):
                    count = 0
                    for root, dirs, files in os.walk(dir_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Use forward slashes for zip internal paths
                            rel_path = os.path.relpath(file_path, dir_path)
                            arcname = f"images/{folder}/{rel_path}".replace('\\', '/')
                            zf.write(file_path, arcname)
                            count += 1
                    log_print(f"Added {count} files from {folder}")
                else:
                    log_print(f"Directory {folder} NOT FOUND.")

        cursor.close()
        db.close()
        log_print("Backup zip created in memory.")
        
        zip_size = memory_file.getbuffer().nbytes
        log_print(f"Zip size: {zip_size} bytes")

    except Exception as e:
        log_print(f"CRITICAL FAILURE: {e}")
        log_print(traceback.format_exc())

    with open("diagnostics_output.txt", "w", encoding='utf-8') as f:
        f.write("\n".join(log))
    print("Diagnostics saved to diagnostics_output.txt")

if __name__ == "__main__":
    run_diagnostics()

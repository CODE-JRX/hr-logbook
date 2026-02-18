import os
import zipfile
import io
import json
from datetime import datetime, date
from flask import Blueprint, send_file, flash, redirect, url_for, current_app, session, request
from db import get_db
from functools import wraps
import mysql.connector

# Custom JSON encoder to handle datetime and date
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

# Define local admin_required to avoid circular/complex imports with all_routes
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_id'):
            flash('Please sign in to access that page')
            return redirect(url_for('client.admin_login'))
        return f(*args, **kwargs)
    return wrapper

backup_bp = Blueprint('backup', __name__)

TABLES = ['admins', 'clients', 'csm_form', 'face_embeddings', 'logs']

@backup_bp.route('/admin/backup/download')
@admin_required
def download_backup():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # Create in-memory zip file
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            
            # 1. Dump MySQL Tables
            for table in TABLES:
                cursor.execute(f"SELECT * FROM {table}")
                data = cursor.fetchall()
                # Serialize to JSON
                json_data = json.dumps(data, indent=2, cls=DateTimeEncoder)
                zf.writestr(f"database/{table}.json", json_data)
                
            # 2. Add Clients images
            clients_dir = os.path.join(os.getcwd(), 'Clients')
            if os.path.exists(clients_dir):
                for root, dirs, files in os.walk(clients_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Ensure forward slashes for internal zip paths
                        rel_path = os.path.relpath(file_path, clients_dir)
                        arcname = os.path.join('images/Clients', rel_path).replace('\\', '/')
                        zf.write(file_path, arcname)
                        
            # 3. Add Admins images
            admins_dir = os.path.join(os.getcwd(), 'Admins')
            if os.path.exists(admins_dir):
                for root, dirs, files in os.walk(admins_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Ensure forward slashes for internal zip paths
                        rel_path = os.path.relpath(file_path, admins_dir)
                        arcname = os.path.join('images/Admins', rel_path).replace('\\', '/')
                        zf.write(file_path, arcname)

        cursor.close()
        db.close()
        memory_file.seek(0)
        
        filename = f"backup_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.zip"
        
        return send_file(
            memory_file,
            download_name=filename,
            as_attachment=True,
            mimetype='application/zip'
        )
        
    except Exception as e:
        flash(f"Backup failed: {str(e)}")
        return redirect(url_for('client.admin_dashboard'))


@backup_bp.route('/admin/backup/restore', methods=['POST'])
@admin_required
def restore_backup():
    import shutil
    
    if 'backup_file' not in request.files:
        flash('No file part')
        return redirect(url_for('client.admin_dashboard'))
        
    file = request.files['backup_file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('client.admin_dashboard'))
        
    if file and file.filename.endswith('.zip'):
        try:
            db = get_db()
            cursor = db.cursor()
            
            # Save upload temporarily
            temp_dir = os.path.join(os.getcwd(), 'temp_restore')
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            
            zip_path = os.path.join(temp_dir, 'params.zip')
            file.save(zip_path)
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(temp_dir)
                
            # Restore Database
            db_dir = os.path.join(temp_dir, 'database')
            if os.path.exists(db_dir):
                # We should restore in an order that respects foreign keys
                # clients -> face_embeddings/logs
                # admins/csm_form (independent)
                
                # Preferred order
                RESTORE_ORDER = ['admins', 'clients', 'csm_form', 'face_embeddings', 'logs']
                
                # Disable FK checks temporarily for easier restore
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                
                for table in RESTORE_ORDER:
                    json_file = f"{table}.json"
                    file_path = os.path.join(db_dir, json_file)
                    
                    if os.path.exists(file_path):
                        with open(file_path, 'r') as f:
                            data = json.loads(f.read())
                        
                        # Clear table - using DELETE instead of TRUNCATE for better consistency with FK checks and compatibility
                        cursor.execute(f"DELETE FROM {table}")
                        cursor.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")
                        
                        if data:
                            # Insert rows
                            columns = data[0].keys()
                            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))})"
                            
                            rows_to_insert = []
                            for row in data:
                                # JSON doesn't distinguish between None and missing, 
                                # but our dump has all keys.
                                values = []
                                for col in columns:
                                    val = row.get(col)
                                    # Convert ISO strings back to datetime if necessary?
                                    # mysql-connector usually handles ISO strings for DATETIME if format is correct,
                                    # but let's see. 
                                    values.append(val)
                                rows_to_insert.append(tuple(values))
                                
                            cursor.executemany(query, rows_to_insert)
                
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
                db.commit()

            # Restore Images (Admins/Clients)
            for folder in ['Clients', 'Admins']:
                src_folder = os.path.join(temp_dir, 'images', folder)
                dst_folder = os.path.join(os.getcwd(), folder)
                if os.path.exists(src_folder):
                    # Recursive copy to handle subdirectories like Clients/Employees
                    for item in os.listdir(src_folder):
                        s = os.path.join(src_folder, item)
                        d = os.path.join(dst_folder, item)
                        if os.path.isdir(s):
                            if os.path.exists(d):
                                shutil.rmtree(d)
                            shutil.copytree(s, d)
                        else:
                            os.makedirs(dst_folder, exist_ok=True)
                            shutil.copy2(s, d)

            # Cleanup
            shutil.rmtree(temp_dir)
            cursor.close()
            db.close()
            
            flash('System restored successfully')
            
        except Exception as e:
            flash(f"Restore failed: {str(e)}")
            if 'db' in locals():
                db.rollback()
            
    else:
        flash('Invalid file format. Please upload a ZIP file.')
        
    return redirect(url_for('client.admin_dashboard'))

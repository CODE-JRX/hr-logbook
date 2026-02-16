import os
import zipfile
import io
import json
from datetime import datetime
from flask import Blueprint, send_file, flash, redirect, url_for, current_app, session
from bson import json_util
from db import get_db
from functools import wraps

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

@backup_bp.route('/admin/backup/download')
@admin_required
def download_backup():
    try:
        db = get_db()
        
        # Create in-memory zip file
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            
            # 1. Dump MongoDB Collections
            collections = db.list_collection_names()
            for col_name in collections:
                # Fetch all documents
                data = list(db[col_name].find())
                # Serialize to JSON using bson.json_util (handles ObjectIds, Dates, etc.)
                json_data = json_util.dumps(data, indent=2)
                zf.writestr(f"database/{col_name}.json", json_data)
                
            # 2. Add Clients images
            clients_dir = os.path.join(os.getcwd(), 'Clients')
            if os.path.exists(clients_dir):
                for root, dirs, files in os.walk(clients_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Archive name: images/Clients/filename.jpg
                        arcname = os.path.join('images/Clients', os.path.relpath(file_path, clients_dir))
                        zf.write(file_path, arcname)
                        
            # 3. Add Admins images
            admins_dir = os.path.join(os.getcwd(), 'Admins')
            if os.path.exists(admins_dir):
                for root, dirs, files in os.walk(admins_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Archive name: images/Admins/filename.jpg
                        arcname = os.path.join('images/Admins', os.path.relpath(file_path, admins_dir))
                        zf.write(file_path, arcname)

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
    from flask import request
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
                for json_file in os.listdir(db_dir):
                    if json_file.endswith('.json'):
                        col_name = json_file.replace('.json', '')
                        file_path = os.path.join(db_dir, json_file)
                        
                        with open(file_path, 'r') as f:
                            data = json_util.loads(f.read())
                            
                        # Drop and Re-insert
                        db[col_name].drop()
                        if data:
                            db[col_name].insert_many(data)

            # Restore Images
            # Clients
            clients_src = os.path.join(temp_dir, 'images', 'Clients')
            clients_dst = os.path.join(os.getcwd(), 'Clients')
            if os.path.exists(clients_src):
                if not os.path.exists(clients_dst):
                    os.makedirs(clients_dst)
                for file_name in os.listdir(clients_src):
                     src_file = os.path.join(clients_src, file_name)
                     dst_file = os.path.join(clients_dst, file_name)
                     shutil.copy2(src_file, dst_file)

            # Admins
            admins_src = os.path.join(temp_dir, 'images', 'Admins')
            admins_dst = os.path.join(os.getcwd(), 'Admins')
            if os.path.exists(admins_src):
                if not os.path.exists(admins_dst):
                    os.makedirs(admins_dst)
                for file_name in os.listdir(admins_src):
                     src_file = os.path.join(admins_src, file_name)
                     dst_file = os.path.join(admins_dst, file_name)
                     shutil.copy2(src_file, dst_file)

            # Cleanup
            shutil.rmtree(temp_dir)
            
            flash('System restored successfully')
            
        except Exception as e:
            flash(f"Restore failed: {str(e)}")
            
    else:
        flash('Invalid file format. Please upload a ZIP file.')
        
    return redirect(url_for('client.admin_dashboard'))

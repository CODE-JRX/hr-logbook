import os
import zipfile
import io
import json
import logging
import shutil
from datetime import datetime, date
from flask import Blueprint, send_file, flash, redirect, url_for, current_app, session, request, jsonify
from db import get_db, get_db_cursor
from functools import wraps
import mysql.connector

logger = logging.getLogger(__name__)

# Custom JSON encoder to handle datetime and date
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, bytes):
            # Attempt to decode bytes to utf-8 string
            try:
                return obj.decode('utf-8')
            except UnicodeDecodeError:
                # Fallback to base64 if not valid utf-8 (though unlikely for our use case)
                import base64
                return base64.b64encode(obj).decode('ascii')
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

def _validate_zip_paths(zipfile_obj):
    """
    Validate that ZIP file doesn't contain path traversal attempts.
    
    Args:
        zipfile_obj: zipfile.ZipFile object
    
    Returns:
        Tuple of (is_valid: bool, error_msg: str)
    """
    try:
        for name in zipfile_obj.namelist():
            # Normalize path
            normalized = os.path.normpath(name)
            # Check for path traversal
            if normalized.startswith('..') or os.path.isabs(normalized):
                return False, f"Invalid path in ZIP: {name}"
        return True, ""
    except Exception as e:
        return False, f"Error validating ZIP: {e}"

def _verify_backup_integrity(zip_path):
    """
    Verify backup ZIP file integrity and structure.
    
    Args:
        zip_path: Path to ZIP file
    
    Returns:
        Tuple of (is_valid: bool, missing_tables: list, error_msg: str)
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Check CRC integrity
            bad_file = zf.testzip()
            if bad_file:
                return False, [], f"ZIP corruption detected in file: {bad_file}"
            
            # Validate paths
            valid, error = _validate_zip_paths(zf)
            if not valid:
                return False, [], error
            
            # Check for required table files
            missing = []
            for table in TABLES:
                if f"database/{table}.json" not in zf.namelist():
                    missing.append(table)
            
            if missing:
                return False, missing, f"Missing database exports: {', '.join(missing)}"
            
            return True, [], ""
    
    except zipfile.BadZipFile as e:
        return False, [], f"Invalid ZIP file: {e}"
    except Exception as e:
        logger.error(f"Error verifying backup: {e}")
        return False, [], f"Backup verification failed: {e}"

@backup_bp.route('/admin/backup/download')
@admin_required
def download_backup():
    """Download complete system backup as ZIP file."""
    try:
        logger.info(f"Starting backup download for admin {session.get('admin_id')}")
        with get_db_cursor() as cursor:
            # Create in-memory zip file
            memory_file = io.BytesIO()
            with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                
                # 1. Dump MySQL Tables
                for table in TABLES:
                    try:
                        cursor.execute(f"SELECT * FROM {table}")
                        data = cursor.fetchall()
                        # Serialize to JSON
                        json_data = json.dumps(data, indent=2, cls=DateTimeEncoder)
                        zf.writestr(f"database/{table}.json", json_data)
                        logger.debug(f"Backed up table {table}: {len(data)} rows")
                    except Exception as e:
                        logger.error(f"Error backing up table {table}: {e}")
                        raise
                    
                # 2. Add Clients images
                clients_dir = os.path.join(os.getcwd(), 'Clients')
                if os.path.exists(clients_dir):
                    try:
                        for root, dirs, files in os.walk(clients_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                rel_path = os.path.relpath(file_path, clients_dir)
                                arcname = os.path.join('images/Clients', rel_path).replace('\\', '/')
                                zf.write(file_path, arcname)
                        logger.debug(f"Backed up client images")
                    except Exception as e:
                        logger.warning(f"Error backing up client images: {e}")
                        # Continue backup without images
                            
                # 3. Add Admins images
                admins_dir = os.path.join(os.getcwd(), 'Admins')
                if os.path.exists(admins_dir):
                    try:
                        for root, dirs, files in os.walk(admins_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                rel_path = os.path.relpath(file_path, admins_dir)
                                arcname = os.path.join('images/Admins', rel_path).replace('\\', '/')
                                zf.write(file_path, arcname)
                        logger.debug(f"Backed up admin images")
                    except Exception as e:
                        logger.warning(f"Error backing up admin images: {e}")
                        # Continue backup without images

            memory_file.seek(0)
            
            filename = f"backup_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.zip"
            logger.info(f"Backup completed: {filename}")
            
            return send_file(
                memory_file,
                download_name=filename,
                as_attachment=True,
                mimetype='application/zip'
            )
        
    except Exception as e:
        logger.error(f"Backup failed: {e}", exc_info=True)
        flash(f"Backup failed: {str(e)}", "danger")
        return redirect(url_for('client.admin_dashboard'))


@backup_bp.route('/admin/backup/restore', methods=['POST'])
@admin_required
def restore_backup():
    """Restore system from backup ZIP file with full transaction support."""
    
    # Check if this is an AJAX request by checking Accept header
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.accept_mimetypes
    
    if 'backup_file' not in request.files:
        msg = 'No file part'
        if is_ajax:
            return jsonify({'success': False, 'message': msg}), 400
        flash(msg)
        return redirect(url_for('client.admin_dashboard'))
        
    file = request.files['backup_file']
    if file.filename == '':
        msg = 'No selected file'
        if is_ajax:
            return jsonify({'success': False, 'message': msg}), 400
        flash(msg)
        return redirect(url_for('client.admin_dashboard'))
        
    if not file.filename.endswith('.zip'):
        msg = 'Only ZIP files are accepted'
        if is_ajax:
            return jsonify({'success': False, 'message': msg}), 400
        flash(msg)
        return redirect(url_for('client.admin_dashboard'))
    
    temp_dir = None
    try:
        logger.info(f"Starting backup restore from {file.filename}")
        
        # Save and validate backup file
        temp_dir = os.path.join(os.getcwd(), 'temp_restore_' + str(int(datetime.now().timestamp())))
        os.makedirs(temp_dir, exist_ok=True)
        
        zip_path = os.path.join(temp_dir, 'backup.zip')
        file.save(zip_path)
        
        # Verify backup integrity first (before touching database)
        logger.info("Verifying backup integrity...")
        is_valid, missing, error = _verify_backup_integrity(zip_path)
        if not is_valid:
            logger.error(f"Backup validation failed: {error}")
            msg = f"Backup file is invalid: {error}"
            if is_ajax:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, "danger")
            return redirect(url_for('client.admin_dashboard'))
        
        logger.info("Backup validation passed")
        
        # Extract backup
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(temp_dir)
        
        # Begin database restoration with explicit transaction control
        with get_db_cursor(commit=False) as cursor:  # commit=False so we control it
            try:
                db_dir = os.path.join(temp_dir, 'database')
                
                logger.info("Starting database restore...")
                
                # Foreign key checks disabled during restore
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                
                # Preferred restore order (respects FK constraints when re-enabled)
                RESTORE_ORDER = ['admins', 'clients', 'csm_form', 'face_embeddings', 'logs']
                
                restored_tables = []
                for table in RESTORE_ORDER:
                    json_file = f"{table}.json"
                    file_path = os.path.join(db_dir, json_file)
                    
                    if not os.path.exists(file_path):
                        logger.warning(f"Skipping table {table}: file not found")
                        continue
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Clear table
                        cursor.execute(f"DELETE FROM {table}")
                        cursor.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")
                        
                        if data:
                            columns = list(data[0].keys())
                            placeholders = ', '.join(['%s'] * len(columns))
                            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
                            
                            rows_inserted = 0
                            for row in data:
                                try:
                                    values = [row.get(col) for col in columns]
                                    cursor.execute(query, values)
                                    rows_inserted += 1
                                except mysql.connector.errors.IntegrityError as e:
                                    logger.warning(f"Skipped row in {table} due to integrity constraint: {e}")
                                    continue
                            
                            logger.info(f"Restored table {table}: {rows_inserted} rows")
                            restored_tables.append(table)
                        else:
                            logger.info(f"Restored table {table}: 0 rows")
                            restored_tables.append(table)
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Corrupt JSON in {table}.json: {e}")
                        raise Exception(f"Table {table} has invalid data format")
                    except Exception as table_err:
                        logger.error(f"Error restoring table {table}: {table_err}")
                        raise
                
                # Re-enable foreign key checks
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
                
                # If we got here, commit the transaction
                logger.info(f"Committing database changes...")
                # The context manager will handle commit since commit=True in outer function
                
            except Exception as db_err:
                logger.error(f"Database restore failed: {db_err}")
                # Rollback is handled by context manager
                msg = f"Database restore failed: {str(db_err)}"
                if is_ajax:
                    return jsonify({'success': False, 'message': msg}), 500
                flash(msg, "danger")
                return redirect(url_for('client.admin_dashboard'))
        
        # Now restore images (after DB restore succeeds)
        logger.info("Restoring images...")
        for folder in ['Clients', 'Admins']:
            src_folder = os.path.join(temp_dir, 'images', folder)
            dst_folder = os.path.join(os.getcwd(), folder)
            
            if os.path.exists(src_folder):
                try:
                    # Verify paths don't escape workspace
                    os.path.normpath(src_folder)
                    os.path.normpath(dst_folder)
                    
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
                    
                    logger.info(f"Restored {folder} images")
                except Exception as img_err:
                    logger.warning(f"Error restoring {folder} images: {img_err}")
                    # Non-fatal: continue if image restore fails
        
        logger.info("Restore completed successfully")
        
        msg = "Backup restored successfully!"
        if is_ajax:
            return jsonify({'success': True, 'message': msg}), 200
        flash(msg, "success")
        return redirect(url_for('client.admin_dashboard'))
        
    except Exception as e:
        logger.error(f"Restore failed: {e}", exc_info=True)
        msg = f"Restore failed: {str(e)}"
        if is_ajax:
            return jsonify({'success': False, 'message': msg}), 500
        flash(msg, "danger")
        return redirect(url_for('client.admin_dashboard'))
    
    finally:
        # Always cleanup temp directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as cleanup_err:
                logger.warning(f"Failed to cleanup temp directory: {cleanup_err}")

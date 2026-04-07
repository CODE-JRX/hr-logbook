from db import get_db_cursor
import logging

logger = logging.getLogger(__name__)

def get_employee_count():
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM pds_personal_information")
            result = cursor.fetchone()
            return result['count'] if result else 0
    except Exception as e:
        logger.error(f"Error getting employee count: {e}")
        return 0

def get_employees_filtered(search=None, limit=25):
    try:
        with get_db_cursor() as cursor:
            query = "SELECT id, surname, first_name, middle_name, sex, date_of_birth, mobile_no, email, agency_employee_no FROM pds_personal_information"
            params = []
            if search:
                query += " WHERE surname LIKE %s OR first_name LIKE %s OR email LIKE %s OR agency_employee_no LIKE %s"
                search_param = f"%{search}%"
                params = [search_param, search_param, search_param, search_param]
            
            query += " ORDER BY id DESC LIMIT %s"
            params.append(int(limit))
            
            cursor.execute(query, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching employees: {e}")
        return []

def delete_employee(id):
    try:
        import os
        with get_db_cursor(commit=True) as cursor:
            # 1. Fetch file paths before deletion
            cursor.execute("SELECT pds_excel_path, signature_path FROM pds_personal_information WHERE id = %s", (id,))
            emp = cursor.fetchone()
            
            # 3. Delete from main table
            cursor.execute("DELETE FROM pds_personal_information WHERE id = %s", (id,))
            
            # 4. Clean up filesystem
            if emp:
                file_fields = ['pds_excel_path', 'signature_path', 'photo', 'thumbmark', 'signature']
                for file_field in file_fields:
                    path = emp.get(file_field)
                    if path:
                        # Convert web path to absolute disk path if it's relative to static
                        if path.startswith('/static/') or path.startswith('static/'):
                            # remove leading slash for joining
                            rel_path = path if not path.startswith('/') else path[1:]
                            abs_path = os.path.join(os.getcwd(), rel_path)
                        else:
                            abs_path = path # assume absolute or direct relative
                            
                        try:
                            if os.path.exists(abs_path) and os.path.isfile(abs_path):
                                os.remove(abs_path)
                                logger.info(f"Deleted file: {abs_path}")
                        except Exception as fe:
                            logger.error(f"Failed to delete file {abs_path}: {fe}")

            return True
    except Exception as e:
        logger.error(f"Error deleting employee {id}: {e}")
        return False

def get_employee_full_pds(id):
    """Fetches all related PDS records for a specific employee ID."""
    try:
        with get_db_cursor() as cursor:
            data = {}
            # 1. Personal Information
            cursor.execute("SELECT * FROM pds_personal_information WHERE id = %s", (id,))
            data['personal_info'] = cursor.fetchone()
            if not data['personal_info']:
                return None
            return data
    except Exception as e:
        logger.error(f"Error fetching full PDS for {id}: {e}")
        return None

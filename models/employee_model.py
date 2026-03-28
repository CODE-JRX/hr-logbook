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
            
            # 2. Delete from dependent tables first due to foreign key constraints
            tables = [
                'pds_spouse', 'pds_parents', 'pds_children', 'pds_education',
                'pds_work_experience', 'pds_civil_service_eligibility', 'pds_voluntary_work',
                'pds_training', 'pds_other_information', 'pds_declarations', 'pds_references', 'pds_oath'
            ]
            for table in tables:
                cursor.execute(f"DELETE FROM {table} WHERE personal_info_id = %s", (id,))
            
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
                
            # 2. Family & Dependents
            cursor.execute("SELECT * FROM pds_spouse WHERE personal_info_id = %s", (id,))
            data['spouse'] = cursor.fetchone()
            
            cursor.execute("SELECT * FROM pds_parents WHERE personal_info_id = %s", (id,))
            data['parents'] = cursor.fetchone()
            
            cursor.execute("SELECT * FROM pds_children WHERE personal_info_id = %s", (id,))
            data['children'] = cursor.fetchall()
            
            # 3. Education
            cursor.execute("SELECT * FROM pds_education WHERE personal_info_id = %s", (id,))
            data['education'] = cursor.fetchall()
            
            # 4. Eligibility & Work
            cursor.execute("SELECT * FROM pds_civil_service_eligibility WHERE personal_info_id = %s", (id,))
            data['eligibility'] = cursor.fetchall()
            
            cursor.execute("SELECT * FROM pds_work_experience WHERE personal_info_id = %s", (id,))
            data['work_experience'] = cursor.fetchall()
            
            # 5. Voluntary & Training
            cursor.execute("SELECT * FROM pds_voluntary_work WHERE personal_info_id = %s", (id,))
            data['voluntary'] = cursor.fetchall()
            
            cursor.execute("SELECT * FROM pds_training WHERE personal_info_id = %s", (id,))
            data['training'] = cursor.fetchall()
            
            # 6. Others
            cursor.execute("SELECT * FROM pds_other_information WHERE personal_info_id = %s", (id,))
            data['other_info'] = cursor.fetchone()
            
            cursor.execute("SELECT * FROM pds_declarations WHERE personal_info_id = %s", (id,))
            data['declarations'] = cursor.fetchone()
            
            cursor.execute("SELECT * FROM pds_references WHERE personal_info_id = %s", (id,))
            data['references'] = cursor.fetchall()
            
            cursor.execute("SELECT * FROM pds_oath WHERE personal_info_id = %s", (id,))
            data['oath'] = cursor.fetchone()
            
            # Debug: Count declarations for verification
            cursor.execute("SELECT COUNT(*) as decl_count FROM pds_declarations WHERE personal_info_id = %s", (id,))
            decl_count = cursor.fetchone()
            logger.info(f"Employee {id} has {decl_count['decl_count'] if decl_count else 0} declarations records")
            
            return data
    except Exception as e:
        logger.error(f"Error fetching full PDS for {id}: {e}")
        return None

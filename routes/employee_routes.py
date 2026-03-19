import logging
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from db import get_db_cursor
from utils.excel_parser import parse_pds_excel
import traceback
import os
import time
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

employee_bp = Blueprint('employee_bp', __name__)

@employee_bp.route('/admin/manage-employees')
def manage_employees():
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, surname, first_name, middle_name, sex, date_of_birth, mobile_no, email, agency_employee_no FROM pds_personal_information ORDER BY id DESC")
            employees = cursor.fetchall()
            return render_template('admin/admin_manage_employees.html', employees=employees)
    except Exception as e:
        logger.error(f"Error fetching employees: {e}")
        return f"Database error: {e}", 500

@employee_bp.route('/admin/pds-test')
def pds_test():
    """Standalone page to test PDS Excel parsing — shows extracted JSON."""
    return render_template('admin/pds_test.html')

@employee_bp.route('/employee/pds/1', methods=['GET', 'POST'])
def pds_p1():
    if request.method == 'POST':
        session['pds_p1'] = request.form.to_dict(flat=False)
        return redirect(url_for('employee_bp.pds_p2'))
    prefill = session.get('pds_excel_prefill', {})
    return render_template('employees/pds-p1.html', prefill=prefill)

@employee_bp.route('/employee/pds/2', methods=['GET', 'POST'])
def pds_p2():
    if request.method == 'POST':
        session['pds_p2'] = request.form.to_dict(flat=False)
        return redirect(url_for('employee_bp.pds_p3'))
    prefill = session.get('pds_excel_prefill', {})
    return render_template('employees/pds-p2.html', prefill=prefill)

@employee_bp.route('/employee/pds/3', methods=['GET', 'POST'])
def pds_p3():
    if request.method == 'POST':
        session['pds_p3'] = request.form.to_dict(flat=False)
        return redirect(url_for('employee_bp.pds_p4'))
    prefill = session.get('pds_excel_prefill', {})
    return render_template('employees/pds-p3.html', prefill=prefill)

@employee_bp.route('/employee/pds/4', methods=['GET', 'POST'])
def pds_p4():
    if request.method == 'POST':
        form_data = request.form.to_dict(flat=False)
        
        # Handle signature upload
        if 'signature_image' in request.files:
            file = request.files['signature_image']
            if file and file.filename != '':
                upload_dir = 'static/uploads/signatures'
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
                filename = f"sig_{int(time.time())}_{secure_filename(file.filename)}"
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)
                # Store path in form data so it's picked up by submit logic
                form_data['signature_path'] = [f"/static/uploads/signatures/{filename}"]

        session['pds_p4'] = form_data
        return redirect(url_for('employee_bp.pds_submit'))
    prefill = session.get('pds_excel_prefill', {})
    return render_template('employees/pds-p4.html', prefill=prefill)

def match_data_to_schema(cursor, table_name, data):
    cursor.execute(f"DESCRIBE {table_name}")
    columns = [row['Field'] for row in cursor.fetchall() if row['Field'] not in ('id', 'personal_info_id')]
    
    insert_data = {}
    for col in columns:
        # try exact
        val = data.get(col)
        # try matching substrings since labels might not match perfectly
        if val is None:
            # find first matching key in data
            matches = [k for k in data.keys() if col in k or k in col]
            if matches:
                val = data[matches[0]]
        
        if val:
            if isinstance(val, list):
                insert_data[col] = val[0]
            else:
                insert_data[col] = val
        else:
            insert_data[col] = None
            
    return insert_data

def match_data_to_schema_list(cursor, table_name, data):
    """Matches form data arrays to table columns, returning a list of dictionaries."""
    cursor.execute(f"DESCRIBE {table_name}")
    columns = [row['Field'] for row in cursor.fetchall() if row['Field'] not in ('id', 'personal_info_id')]
    
    max_len = 1
    matched_cols = {}
    for col in columns:
        val = data.get(col)
        if val is None:
            matches = [k for k in data.keys() if col in k or k in col]
            if matches:
                val = data[matches[0]]
        matched_cols[col] = val
        if val and isinstance(val, list):
            max_len = max(max_len, len(val))
            
    rows = []
    for i in range(max_len):
        row_data = {}
        has_val = False
        for col in columns:
            val = matched_cols[col]
            if val and isinstance(val, list):
                if i < len(val):
                    row_data[col] = val[i]
                    if val[i] and str(val[i]).strip():
                        has_val = True
                else:
                    row_data[col] = None
            else:
                row_data[col] = val if i == 0 else None
                if row_data[col] and str(row_data[col]).strip() and i == 0:
                    has_val = True
        
        # Only add the row if it contains at least one non-empty value
        if has_val:
            rows.append(row_data)
            
    return rows if rows else [{}] # Ensure at least one empty dict is returned if nothing matches

def insert_rows_with_mapping(cursor, table_name, data, col_map, personal_info_id):
    """
    Inserts rows into table_name using col_map to translate form field names to DB columns.
    col_map: dict of {db_column: form_field_name}
    Handles list (array) form fields for multi-row tables.
    """
    max_len = 0
    for form_name in col_map.values():
        val = data.get(form_name)
        if val and isinstance(val, list):
            max_len = max(max_len, len(val))
    
    if max_len == 0:
        max_len = 1
    
    for i in range(max_len):
        row = {'personal_info_id': personal_info_id}
        has_val = False
        for db_col, form_name in col_map.items():
            val = data.get(form_name)
            if val and isinstance(val, list):
                cell = val[i] if i < len(val) else None
            elif val and i == 0:
                cell = val
            else:
                cell = None
            row[db_col] = cell
            if cell and str(cell).strip():
                has_val = True
        if has_val:
            cols = list(row.keys())
            vals = list(row.values())
            placeholders = ', '.join(['%s'] * len(cols))
            cursor.execute(f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({placeholders})", vals)


from models.employee_model import get_employee_count, delete_employee, get_employee_full_pds

def db_to_pds_prefill(data):
    """Transforms DB records into the structure expected by PDS templates."""
    if not data: return {}
    pi = data.get('personal_info') or {}
    
    # Clean up dates and list formats for template consumption
    def clean_date(val):
        if not val: return ''
        if hasattr(val, 'strftime'): return val.strftime('%Y-%m-%d')
        return str(val)

    # 1. Map Education
    education = []
    for edu in (data.get('education') or []):
        education.append({
            'level': edu.get('level'),
            'school': edu.get('school_name'),
            'degree': edu.get('degree_course'),
            'from': edu.get('from_year'),
            'to': edu.get('to_year'),
            'units': edu.get('highest_level_units'),
            'graduated': edu.get('year_graduated'),
            'honors': edu.get('scholarship_honors')
        })

    # 2. Map Eligibility
    eligibility = []
    for elig in (data.get('eligibility') or []):
        eligibility.append({
            'eligibility': elig.get('eligibility'),
            'rating': elig.get('rating'),
            'exam_date': clean_date(elig.get('date_of_exam')),
            'exam_place': elig.get('place_of_exam'),
            'license_number': elig.get('license_number'),
            'license_date': clean_date(elig.get('valid_until'))
        })

    # 3. Map Work Experience
    work_exp = []
    for work in (data.get('work_experience') or []):
        work_exp.append({
            'from': clean_date(work.get('date_from')),
            'to': clean_date(work.get('date_to')),
            'position': work.get('position_title'),
            'department': work.get('department_agency_company'),
            'appointment_status': work.get('status_of_appointment'),
            'govt_service': work.get('gov_service')
        })

    # 4. Map Voluntary Work
    voluntary = []
    for vol in (data.get('voluntary') or []):
        voluntary.append({
            'organization': vol.get('organization'),
            'from': clean_date(vol.get('date_from')),
            'to': clean_date(vol.get('date_to')),
            'hours': vol.get('hours'),
            'position': vol.get('position')
        })

    # 5. Map Training
    training = []
    for tr in (data.get('training') or []):
        training.append({
            'title': tr.get('title'),
            'from': clean_date(tr.get('date_from')),
            'to': clean_date(tr.get('date_to')),
            'hours': tr.get('hours'),
            'type': tr.get('type'),
            'conducted_by': tr.get('conducted_by')
        })

    # 6. Map References
    references = []
    for ref in (data.get('references') or []):
        references.append({
            'name': ref.get('full_name'),
            'address': ref.get('address'),
            'contact': ref.get('contact')
        })

    processed = {
        'personal_info': {
            **pi,
            'surname': pi.get('surname'),
            'first_name': pi.get('first_name'),
            'middle_name': pi.get('middle_name'),
            'name_extension': pi.get('name_extension'),
            'date_of_birth': clean_date(pi.get('date_of_birth')),
            'place_of_birth': pi.get('place_of_birth'),
            'sex_at_birth': pi.get('sex'), # Excel compatibility
            'email_address': pi.get('email'),
            'citizenship': pi.get('country_citizenship'),
            'mobile_no': pi.get('mobile_no'),
            'agency_employee_no': pi.get('agency_employee_no'),
            'gsis_no': pi.get('gsis_no'),
            'pagibig_no': pi.get('pagibig_no'),
            'philhealth_no': pi.get('philhealth_no'),
            'sss_no': pi.get('sss_no'),
            'tin_no': pi.get('tin_no'),
            'height': pi.get('height'),
            'weight': pi.get('weight'),
            'blood_type': pi.get('blood_type'),
            'residential_address': {
                'house_no': pi.get('res_house_no'),
                'street': pi.get('res_street'),
                'subdivision': pi.get('res_subdivision'),
                'barangay': pi.get('res_barangay'),
                'city': pi.get('res_city'),
                'province': pi.get('res_province'),
                'zip_code': pi.get('res_zip_code')
            },
            'permanent_address': {
                'house_no': pi.get('perm_house_no'),
                'street': pi.get('perm_street'),
                'subdivision': pi.get('perm_subdivision'),
                'barangay': pi.get('perm_barangay'),
                'city': pi.get('perm_city'),
                'province': pi.get('perm_province'),
                'zip_code': pi.get('perm_zip_code')
            }
        },
        'family_background': {
            'spouse': {
                'surname': data['spouse'].get('surname') if data.get('spouse') else '',
                'first_name': data['spouse'].get('first_name') if data.get('spouse') else '',
                'middle_name': data['spouse'].get('middle_name') if data.get('spouse') else '',
                'name_extension': data['spouse'].get('name_extension') if data.get('spouse') else '',
                'occupation': data['spouse'].get('occupation') if data.get('spouse') else '',
                'employer': data['spouse'].get('employer') if data.get('spouse') else '',
                'biz_address': data['spouse'].get('business_address') if data.get('spouse') else '',
                'tel_no': data['spouse'].get('telephone_no') if data.get('spouse') else ''
            },
            'father': { 
                'surname': data['parents'].get('father_surname') if data.get('parents') else '',
                'first_name': data['parents'].get('father_first_name') if data.get('parents') else '',
                'middle_name': data['parents'].get('father_middle_name') if data.get('parents') else '',
                'name_extension': data['parents'].get('father_name_extension') if data.get('parents') else ''
            },
            'mother': {
                'maiden_surname': data['parents'].get('mother_maiden_surname') if data.get('parents') else '',
                'first_name': data['parents'].get('mother_first_name') if data.get('parents') else '',
                'middle_name': data['parents'].get('mother_middle_name') if data.get('parents') else ''
            },
            'children': [
                {'name': c.get('full_name'), 'dob': clean_date(c.get('date_of_birth'))} 
                for c in (data.get('children') or [])
            ]
        },
        'educational_background': education,
        'civil_service_eligibility': eligibility,
        'work_experience': work_exp,
        'voluntary_work': voluntary,
        'training_programs': training,
        'other_information': {
            'skills': (data['other_info'].get('special_skills_hobbies') or '').split(', ') if data.get('other_info') else [],
            'distinctions': (data['other_info'].get('non_academic_distinctions') or '').split(', ') if data.get('other_info') else [],
            'memberships': (data['other_info'].get('membership_associations') or '').split(', ') if data.get('other_info') else []
        },
        'references': references,
        'government_id': {
             'type': pi.get('gov_issued_id'),
             'number': pi.get('id_no'),
             'date_place_of_issuance': pi.get('date_place_issuance')
        }
    }
    return processed

@employee_bp.route('/admin/employee/add')
def add_employee_start():
    """Initializes a fresh PDS flow for a new employee."""
    # Clear editing and prefill state
    session.pop('editing_employee_id', None)
    session.pop('pds_excel_prefill', None)
    # Clear any partially filled form pages in session
    for p in ['pds_p1', 'pds_p2', 'pds_p3', 'pds_p4']:
        session.pop(p, None)
    return redirect(url_for('employee_bp.pds_p1'))

@employee_bp.route('/admin/employee/edit/<int:id>')
def edit_employee_start(id):
    """Initial entry point for editing an employee. Loads data into session."""
    raw_data = get_employee_full_pds(id)
    if not raw_data:
        flash(f"Employee ID {id} not found.", "danger")
        return redirect(url_for('employee_bp.manage_employees'))
    
    # Store in session as 'pds_excel_prefill' to trick existing pds routes into loading it
    session['pds_excel_prefill'] = db_to_pds_prefill(raw_data)
    session['editing_employee_id'] = id
    
    # Clear any previous form-step session data to avoid mixed states
    for k in ('pds_p1', 'pds_p2', 'pds_p3', 'pds_p4'):
        session.pop(k, None)
        
    return redirect(url_for('employee_bp.pds_p1', is_edit=1))

@employee_bp.route('/admin/employee/delete/<id>')
def admin_delete_employee(id):
    if delete_employee(id):
        flash("Employee and all related PDS records deleted successfully.")
    else:
        flash("Failed to delete employee records.")
    return redirect(url_for('employee_bp.manage_employees'))

@employee_bp.route('/employee/pds/submit', methods=['GET', 'POST'])
def pds_submit():
    data = {}
    if 'pds_p1' in session: data.update(session['pds_p1'])
    if 'pds_p2' in session: data.update(session['pds_p2'])
    if 'pds_p3' in session: data.update(session['pds_p3'])
    if 'pds_p4' in session: data.update(session['pds_p4'])
    if request.method == 'POST':
        data.update(request.form.to_dict(flat=False))
        
    if not data:
        return "No data submitted", 400

    try:
        with get_db_cursor(commit=True) as cursor:
            # Check if we are in Edit Mode
            personal_info_id = session.get('editing_employee_id')
            is_edit = personal_info_id is not None
            
            # 1. pds_personal_information
            pinfo_data = match_data_to_schema(cursor, 'pds_personal_information', data)
            # fallback for required fields
            pinfo_data['surname'] = data.get('surname', [''])[0] if isinstance(data.get('surname'), list) else data.get('surname', '')
            pinfo_data['first_name'] = data.get('first_name', [''])[0] if isinstance(data.get('first_name'), list) else data.get('first_name', '')
            
            cols = list(pinfo_data.keys())
            vals = list(pinfo_data.values())
            
            if is_edit:
                # Update core personal info
                sets = ", ".join([f"{c} = %s" for c in cols])
                cursor.execute(f"UPDATE pds_personal_information SET {sets} WHERE id = %s", vals + [personal_info_id])
                
                # Clear all related tables to re-insert fresh data (Delete & Re-insert strategy)
                tables_to_clear = [
                    'pds_spouse', 'pds_parents', 'pds_children', 'pds_education',
                    'pds_work_experience', 'pds_civil_service_eligibility', 'pds_voluntary_work',
                    'pds_training', 'pds_other_information', 'pds_declarations', 'pds_references', 'pds_oath'
                ]
                for t in tables_to_clear:
                    cursor.execute(f"DELETE FROM {t} WHERE personal_info_id = %s", (personal_info_id,))
            else:
                # Insert new record
                placeholders = ', '.join(['%s'] * len(cols))
                cursor.execute(f"INSERT INTO pds_personal_information ({', '.join(cols)}) VALUES ({placeholders})", vals)
                personal_info_id = cursor.lastrowid
            # 2. Insert single-row tables (schema-matched automatically)
            single_row_tables = [
                'pds_spouse', 'pds_parents', 'pds_other_information', 'pds_declarations', 'pds_oath'
            ]
            for table in single_row_tables:
                table_data = match_data_to_schema(cursor, table, data)
                if any((v is not None and str(v).strip() != '') for v in table_data.values()):
                    table_data['personal_info_id'] = personal_info_id
                    t_cols = list(table_data.keys())
                    t_vals = list(table_data.values())
                    t_placeholders = ', '.join(['%s'] * len(t_cols))
                    cursor.execute(f"INSERT INTO {table} ({', '.join(t_cols)}) VALUES ({t_placeholders})", t_vals)

            # 3. Insert multi-row tables — explicit form-field→DB-column mappings
            insert_rows_with_mapping(cursor, 'pds_children', data, {
                'full_name': 'child_fullname[]',
                'date_of_birth': 'child_dob[]'
            }, personal_info_id)

            insert_rows_with_mapping(cursor, 'pds_education', data, {
                'level': 'level[]',
                'school_name': 'name_of_school[]',
                'degree_course': 'basic_education_degree_course[]',
                'from_year': 'period_from[]',
                'to_year': 'period_to[]',
                'highest_level_units': 'highest_level_units_earned[]',
                'year_graduated': 'year_graduated[]',
                'scholarship_honors': 'scholarship_academic_honors[]'
            }, personal_info_id)

            insert_rows_with_mapping(cursor, 'pds_civil_service_eligibility', data, {
                'eligibility': 'eligibility[]',
                'rating': 'elig_rating[]',
                'date_of_exam': 'elig_date[]',
                'place_of_exam': 'elig_place[]',
                'license_number': 'elig_license_no[]',
                'valid_until': 'elig_validity[]'
            }, personal_info_id)

            insert_rows_with_mapping(cursor, 'pds_work_experience', data, {
                'date_from': 'work_from[]',
                'date_to': 'work_to[]',
                'position_title': 'work_position[]',
                'department_agency_company': 'work_company[]',
                'status_of_appointment': 'work_status[]',
                'gov_service': 'work_govt_service[]'
            }, personal_info_id)

            insert_rows_with_mapping(cursor, 'pds_voluntary_work', data, {
                'organization': 'voluntary_organization[]',
                'date_from': 'voluntary_period_from[]',
                'date_to': 'voluntary_period_to[]',
                'hours': 'voluntary_hours[]',
                'position': 'voluntary_position[]'
            }, personal_info_id)

            insert_rows_with_mapping(cursor, 'pds_training', data, {
                'title': 'training_title[]',
                'date_from': 'training_period_from[]',
                'date_to': 'training_period_to[]',
                'hours': 'training_hours[]',
                'type': 'training_type[]',
                'conducted_by': 'training_sponsor[]'
            }, personal_info_id)

            insert_rows_with_mapping(cursor, 'pds_references', data, {
                'full_name': 'ref_name[]',
                'address': 'ref_address[]',
                'contact': 'ref_contact[]'
            }, personal_info_id)
                
            session.pop('pds_p1', None)
            session.pop('pds_p2', None)
            session.pop('pds_p3', None)
            session.pop('pds_p4', None)
            session.pop('editing_employee_id', None)
            
            # Move temp Excel file to permanent location if it exists
            temp_path = session.pop('pds_excel_temp_path', None)
            if temp_path and os.path.exists(temp_path):
                permanent_dir = 'static/uploads/employee_pds'
                if not os.path.exists(permanent_dir):
                    os.makedirs(permanent_dir)
                ext = temp_path.rsplit('.', 1)[1].lower() if '.' in temp_path else 'xlsx'
                final_filename = f"pds_{personal_info_id}_{int(time.time())}.{ext}"
                final_path = os.path.join(permanent_dir, final_filename)
                os.rename(temp_path, final_path)
                
                # Update DB with final path
                db_path = f"/static/uploads/employee_pds/{final_filename}"
                cursor.execute("UPDATE pds_personal_information SET pds_excel_path = %s WHERE id = %s", (db_path, personal_info_id))
            
            session.pop('pds_excel_prefill', None)
            
            msg = "PDS record updated successfully!" if is_edit else "PDS successfully submitted!"
            flash(msg)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'success': True, 'message': msg})

            return redirect(url_for('employee_bp.manage_employees', success=1))
            
    except Exception as e:
        logger.error(f"Error submitting PDS: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        return f"Database error during submission: {e}", 500

@employee_bp.route('/api/employees/upload-pds-excel', methods=['POST'])
def upload_pds_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        file_content = file.read()
        parsed_data = None
        warning = None
        try:
            parsed_data = parse_pds_excel(file_content)
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Excel parse error: {str(e)}\n{tb}")
            warning = str(e)

        if parsed_data is not None:
            # Save the file to tempoary storage
            temp_dir = 'static/uploads/temp_pds'
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            temp_filename = f"temp_{int(time.time())}_{secure_filename(file.filename)}"
            temp_path = os.path.join(temp_dir, temp_filename)
            with open(temp_path, 'wb') as f:
                f.write(file_content)
            
            session['pds_excel_temp_path'] = temp_path
            
            # Store in session so PDS pages can pre-fill themselves
            session['pds_excel_prefill'] = parsed_data
            for k in ('pds_p1', 'pds_p2', 'pds_p3', 'pds_p4'):
                session.pop(k, None)
            response = {
                'success': True,
                'data': parsed_data,
                'redirect': url_for('employee_bp.pds_p1')
            }
            if warning:
                response['warning'] = f"Partial parse: {warning}"
            return jsonify(response)
        else:
            return jsonify({
                'success': False,
                'error': f"Could not parse Excel: {warning}. Try Debug Mode to inspect cell layout."
            }), 500

    return jsonify({'error': 'Invalid file type. Use .xlsx or .xls'}), 400


@employee_bp.route('/api/employees/debug-excel', methods=['POST'])
def debug_excel():
    """Dumps the raw cell values from all sheets so we can identify layout."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        import openpyxl, io
        file_content = file.read()
        wb = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)
        dump = {}
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            sheet_dump = {}
            max_r = min(ws.max_row, 75)
            max_c = min(ws.max_column, 20)
            for r in range(1, max_r + 1):
                row_data = {}
                for c in range(1, max_c + 1):
                    val = ws.cell(row=r, column=c).value
                    if val is not None and str(val).strip() not in ('', 'N/A'):
                        col_letter = openpyxl.utils.get_column_letter(c)
                        row_data[f"{col_letter}{r}"] = str(val).strip()
                if row_data:
                    sheet_dump[f"row_{r}"] = row_data
            dump[sheet_name] = sheet_dump
        return jsonify({'success': True, 'sheets': wb.sheetnames, 'dump': dump})
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Debug Excel error: {e}\n{tb}")
        return jsonify({'error': str(e)}), 500




@employee_bp.route('/api/employees/pds', methods=['POST'])
def api_submit_pds_json():
    """
    Accepts the parsed JSON structure from the Excel import and inserts
    it into the database tables.
    """
    payload = request.get_json()
    if not payload or 'pdsData' not in payload:
        return jsonify({'error': 'No pdsData in request body'}), 400

    pds = payload['pdsData']

    try:
        with get_db_cursor(commit=True) as cursor:

            # ── 1. personal_information ──────────────────────────────────
            pi = pds.get('personal_info', {})
            res = pi.get('residential_address', {})
            perm = pi.get('permanent_address', {})
            cursor.execute("""
                INSERT INTO pds_personal_information
                (surname, first_name, middle_name, name_extension, date_of_birth,
                 place_of_birth, civil_status, height, weight, blood_type,
                 gsis_no, pagibig_no, philhealth_no, sss_no, tin_no, agency_employee_no,
                 mobile_no, email,
                 res_house_no, res_street, res_barangay, res_city, res_province, res_zip_code,
                 perm_house_no, perm_street, perm_barangay, perm_city, perm_province, perm_zip_code)
                VALUES (%s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s,%s, %s,%s, %s,%s,%s,%s,%s,%s, %s,%s,%s,%s,%s,%s)
            """, (
                pi.get('surname'), pi.get('first_name'), pi.get('middle_name'), pi.get('name_extension'),
                pi.get('date_of_birth') or None, pi.get('place_of_birth'), pi.get('civil_status'),
                pi.get('height'), pi.get('weight'), pi.get('blood_type'),
                pi.get('gsis_no'), pi.get('pagibig_no'), pi.get('philhealth_no'),
                pi.get('sss_no'), pi.get('tin_no'), pi.get('agency_employee_no'),
                pi.get('mobile_no'), pi.get('email_address'),
                res.get('house_no'), res.get('street'), res.get('barangay'), res.get('city'), res.get('province'), res.get('zip_code'),
                perm.get('house_no'), perm.get('street'), perm.get('barangay'), perm.get('city'), perm.get('province'), perm.get('zip_code'),
            ))
            personal_info_id = cursor.lastrowid

            # ── 2. spouse ────────────────────────────────────────────────
            fb = pds.get('family_background', {})
            spouse = fb.get('spouse', {})
            if any(spouse.values()):
                cursor.execute("""
                    INSERT INTO pds_spouse (personal_info_id, surname, first_name, middle_name,
                        occupation, employer_name, business_address, telephone_no)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (personal_info_id, spouse.get('surname'), spouse.get('first_name'),
                      spouse.get('middle_name'), spouse.get('occupation'),
                      spouse.get('employer_name'), spouse.get('business_address'), spouse.get('telephone_no')))

            # ── 3. parents ───────────────────────────────────────────────
            father = fb.get('father', {})
            mother = fb.get('mother', {})
            if any(father.values()) or any(mother.values()):
                cursor.execute("""
                    INSERT INTO pds_parents (personal_info_id,
                        father_surname, father_first_name, father_middle_name,
                        mother_surname, mother_first_name, mother_middle_name)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (personal_info_id,
                      father.get('surname'), father.get('first_name'), father.get('middle_name'),
                      mother.get('maiden_surname'), mother.get('first_name'), mother.get('middle_name')))

            # ── 4. children ──────────────────────────────────────────────
            for child in fb.get('children', []):
                cursor.execute("""
                    INSERT INTO pds_children (personal_info_id, full_name, date_of_birth)
                    VALUES (%s,%s,%s)
                """, (personal_info_id, child.get('name'), child.get('date_of_birth') or None))

            # ── 5. education ─────────────────────────────────────────────
            for edu in pds.get('educational_background', []):
                cursor.execute("""
                    INSERT INTO pds_education (personal_info_id, level, school_name, degree_course,
                        period_from, period_to, highest_level_units, year_graduated, scholarship_honors)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (personal_info_id, edu.get('level'), edu.get('school_name'), edu.get('degree'),
                      edu.get('from'), edu.get('to'), edu.get('highest_level'),
                      edu.get('year_graduated'), edu.get('scholarships')))

            # ── 6. civil service eligibility ─────────────────────────────
            for elig in pds.get('civil_service_eligibility', []):
                cursor.execute("""
                    INSERT INTO pds_civil_service_eligibility
                    (personal_info_id, eligibility, rating, exam_date, exam_place, license_number, license_date)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (personal_info_id, elig.get('eligibility'), elig.get('rating'),
                      elig.get('exam_date') or None, elig.get('exam_place'),
                      elig.get('license_number'), elig.get('license_date') or None))

            # ── 7. work experience ───────────────────────────────────────
            for work in pds.get('work_experience', []):
                cursor.execute("""
                    INSERT INTO pds_work_experience
                    (personal_info_id, date_from, date_to, position_title, department_agency,
                     monthly_salary, salary_grade, appointment_status, govt_service)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (personal_info_id, work.get('from') or None, work.get('to') or None,
                      work.get('position'), work.get('department'), work.get('salary'),
                      work.get('pay_grade'), work.get('appointment_status'), work.get('govt_service')))

            # ── 8. voluntary work ────────────────────────────────────────
            for vol in pds.get('voluntary_work', []):
                cursor.execute("""
                    INSERT INTO pds_voluntary_work
                    (personal_info_id, organization, date_from, date_to, hours, position)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (personal_info_id, vol.get('organization'),
                      vol.get('from') or None, vol.get('to') or None,
                      vol.get('hours'), vol.get('position')))

            # ── 9. training / L&D ────────────────────────────────────────
            for trn in pds.get('training_programs', []):
                cursor.execute("""
                    INSERT INTO pds_training
                    (personal_info_id, training_title, date_from, date_to, hours, type_of_ld, conducted_by)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (personal_info_id, trn.get('title'),
                      trn.get('from') or None, trn.get('to') or None,
                      trn.get('hours'), trn.get('type'), trn.get('conducted_by')))

            # ── 10. other information ─────────────────────────────────────
            oi = pds.get('other_information', {})
            cursor.execute("""
                INSERT INTO pds_other_information
                (personal_info_id, skills_hobbies, distinctions, memberships)
                VALUES (%s,%s,%s,%s)
            """, (personal_info_id,
                  ', '.join(oi.get('skills', [])),
                  ', '.join(oi.get('distinctions', [])),
                  ', '.join(oi.get('memberships', []))))

        return jsonify({'success': True, 'personal_info_id': personal_info_id})

    except Exception as e:
        logger.error(f"Error saving PDS JSON to DB: {e}")
        return jsonify({'error': str(e)}), 500


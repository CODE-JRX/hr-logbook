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

# Map form field names to actual DB column names for personal info table
PERSONAL_INFO_MAP = {
    'surname': 'surname',
    'first_name': 'first_name',
    'middle_name': 'middle_name',
    'name_extension': 'name_extension',
    'civil_status': 'civil_status',
    'country_citizenship': 'citizenship',
    'sex': 'sex',
    'date_of_birth': 'date_of_birth',
    'place_of_birth': 'place_of_birth',
    'res_house_no': 'residential_house',
    'res_street': 'residential_street',
    'res_subdivision': 'residential_subdivision',
    'res_barangay': 'residential_barangay',
    'res_city': 'residential_city',
    'res_province': 'residential_province',
    'res_zip_code': 'residential_zip',
    'perm_house_no': 'permanent_house',
    'perm_street': 'permanent_street',
    'perm_subdivision': 'permanent_subdivision',
    'perm_barangay': 'permanent_barangay',
    'perm_city': 'permanent_city',
    'perm_province': 'permanent_province',
    'perm_zip_code': 'permanent_zip',
    'height': 'height',
    'weight': 'weight',
    'blood_type': 'blood_type',
    'umid_no': 'umid_id',
    'pagibig_no': 'pagibig_id',
    'philhealth_no': 'philhealth_no',
    'sss_no': 'sss_no',
    'philsys_no': 'philsys_no',
    'gsis_no': 'gsis_no',
    'tin_no': 'tin_no',
    'agency_employee_no': 'agency_employee_no',
    'telephone_no': 'telephone_no',
    'mobile_no': 'mobile_no',
    'email': 'email',
}


def build_personal_info_payload(data: dict) -> dict:
    """
    Build a dict aligned with the current DB schema using explicit mappings.
    Only maps known fields and ignores audit columns.
    """
    payload = {}
    for form_key, col in PERSONAL_INFO_MAP.items():
        if form_key in data:
            payload[col] = _coerce_first(data[form_key])
    # Optional: also store citizenship in both columns if country exists
    if 'country_citizenship' in data and 'country' not in payload:
        payload['country'] = _coerce_first(data['country_citizenship'])

    # Signature upload (UI stores as signature_path); map to DB column signature_path
    if 'signature_path' in data:
        payload['signature_path'] = _coerce_first(data['signature_path'])
    return payload

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

@employee_bp.route('/admin/employee/view/<int:id>')
def view_employee(id):
    """Render a read-only view of an employee's PDS."""
    data = get_employee_full_pds(id)
    if not data:
        flash(f"Employee ID {id} not found.", "danger")
        return redirect(url_for('employee_bp.manage_employees'))
    return render_template('admin/admin_view_employee.html', pds=data)

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
    clear_ls = session.pop('clear_local_storage', False)
    return render_template('employees/pds-p1.html', prefill=prefill, clear_ls=clear_ls)

@employee_bp.route('/employee/pds/2', methods=['GET', 'POST'])
def pds_p2():
    if request.method == 'POST':
        session['pds_p2'] = request.form.to_dict(flat=False)
        return redirect(url_for('employee_bp.pds_p3'))
    prefill = session.get('pds_excel_prefill', {})
    clear_ls = session.pop('clear_local_storage', False)
    return render_template('employees/pds-p2.html', prefill=prefill, clear_ls=clear_ls)

@employee_bp.route('/employee/pds/3', methods=['GET', 'POST'])
def pds_p3():
    if request.method == 'POST':
        session['pds_p3'] = request.form.to_dict(flat=False)
        return redirect(url_for('employee_bp.pds_p4'))
    prefill = session.get('pds_excel_prefill', {})
    clear_ls = session.pop('clear_local_storage', False)
    return render_template('employees/pds-p3.html', prefill=prefill, clear_ls=clear_ls)

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
    clear_ls = session.pop('clear_local_storage', False)
    return render_template('employees/pds-p4.html', prefill=prefill, clear_ls=clear_ls)

def _coerce_first(val):
    """Return the first element if list-like, otherwise the value itself."""
    if isinstance(val, list):
        return val[0] if val else None
    return val


def _clean_date(val):
    """
    Normalize many date inputs to YYYY-MM-DD. Returns None if unparsable or 'PRESENT'.
    Accepts YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY.
    """
    if val is None:
        return None
    if isinstance(val, str) and val.strip().upper() == 'PRESENT':
        return None
    from datetime import datetime
    candidates = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%m-%d-%Y",
    ]
    s = str(val).strip()
    for fmt in candidates:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def match_data_to_schema(cursor, table_name, data):
    """
    Map incoming form data to table columns using a simple heuristic.
    Excludes id/personal_info_id/created_at/updated_at to avoid clobbering defaults.
    """
    cursor.execute(f"DESCRIBE {table_name}")
    columns = [
        row["Field"]
        for row in cursor.fetchall()
        if row["Field"] not in ("id", "personal_info_id", "created_at", "updated_at")
    ]

    insert_data = {}
    for col in columns:
        # try exact
        val = data.get(col)
        # try matching substrings since labels might not match perfectly
        if val is None:
            matches = [k for k in data.keys() if col in k or k in col]
            if matches:
                val = data[matches[0]]

        insert_data[col] = _coerce_first(val) if val else None

    return insert_data

def match_data_to_schema_list(cursor, table_name, data):
    """Matches form data arrays to table columns, returning a list of dictionaries."""
    cursor.execute(f"DESCRIBE {table_name}")
    columns = [
        row['Field']
        for row in cursor.fetchall()
        if row['Field'] not in ('id', 'personal_info_id', 'created_at', 'updated_at')
    ]
    
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
    def normalize_cell(val):
        if isinstance(val, str) and val.strip().upper() == 'PRESENT':
            return None
        return val

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
                cell = normalize_cell(val[i] if i < len(val) else None)
            elif val and i == 0:
                cell = normalize_cell(val)
            else:
                cell = None

            # Normalize dates per table/column
            if table_name in ('pds_work_experience', 'pds_voluntary_work', 'pds_training') and db_col in ('date_from', 'date_to'):
                cell = _clean_date(cell)

            row[db_col] = cell
            if cell and str(cell).strip():
                has_val = True
        if has_val:
            cols = list(row.keys())
            vals = list(row.values())
            placeholders = ', '.join(['%s'] * len(cols))
            cursor.execute(f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({placeholders})", vals)


def _fix_work_is_present(cursor, personal_info_id, data):
    """
    After inserting pds_work_experience rows, set is_present=1 for any
    row whose original 'work_to[]' value was 'PRESENT' (which was
    normalized to NULL by _clean_date).
    """
    raw_to_vals = data.get('work_to[]', [])
    if not isinstance(raw_to_vals, list):
        raw_to_vals = [raw_to_vals]
    
    # Fetch the IDs of the just-inserted rows in insertion order
    cursor.execute(
        "SELECT id FROM pds_work_experience WHERE personal_info_id = %s ORDER BY id",
        (personal_info_id,)
    )
    inserted = cursor.fetchall()
    
    for idx, row in enumerate(inserted):
        if idx < len(raw_to_vals):
            raw_val = raw_to_vals[idx]
            if raw_val and str(raw_val).strip().upper() == 'PRESENT':
                cursor.execute(
                    "UPDATE pds_work_experience SET is_present = 1 WHERE id = %s",
                    (row['id'],)
                )


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
            'highest_level': edu.get('highest_level_units'),
            'units': edu.get('highest_level_units'),
            'year_graduated': edu.get('year_graduated'),
            'graduated': edu.get('year_graduated'),
            'scholarships': edu.get('scholarship_honors'),
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
            'to': '' if str(work.get('date_to')).strip().upper() == 'PRESENT' else clean_date(work.get('date_to')),
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
            'citizenship': pi.get('citizenship') or pi.get('country_citizenship'),
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
                'house_no': pi.get('residential_house') or pi.get('res_house_no'),
                'street': pi.get('residential_street') or pi.get('res_street'),
                'subdivision': pi.get('residential_subdivision') or pi.get('res_subdivision'),
                'barangay': pi.get('residential_barangay') or pi.get('res_barangay'),
                'city': pi.get('residential_city') or pi.get('res_city'),
                'province': pi.get('residential_province') or pi.get('res_province'),
                'zip_code': pi.get('residential_zip') or pi.get('res_zip_code')
            },
            'permanent_address': {
                'house_no': pi.get('permanent_house') or pi.get('perm_house_no'),
                'street': pi.get('permanent_street') or pi.get('perm_street'),
                'subdivision': pi.get('permanent_subdivision') or pi.get('perm_subdivision'),
                'barangay': pi.get('permanent_barangay') or pi.get('perm_barangay'),
                'city': pi.get('permanent_city') or pi.get('perm_city'),
                'province': pi.get('permanent_province') or pi.get('perm_province'),
                'zip_code': pi.get('permanent_zip') or pi.get('perm_zip_code')
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
                # DB uses mother_maiden_surname; fall back to mother_surname for older schema
                'maiden_surname': (data['parents'].get('mother_maiden_surname') if data.get('parents') else '') or (data['parents'].get('mother_surname') if data.get('parents') else ''),
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
        'declarations': data.get('declarations') or data.get('decl') or data.get('pds_declarations') or {},
        'references': references,
        'government_id': {
             'type': (data.get('oath') or {}).get('government_id') or pi.get('gov_issued_id'),
             'number': (data.get('oath') or {}).get('id_number') or pi.get('id_no'),
             'date_place_of_issuance': (data.get('oath') or {}).get('issuance_date_place') or pi.get('date_place_issuance')
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
    session['clear_local_storage'] = True
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
        
    session['clear_local_storage'] = True
    return redirect(url_for('employee_bp.pds_p1', is_edit=1))

@employee_bp.route('/admin/employee/delete/<id>')
def admin_delete_employee(id):
    if delete_employee(id):
        flash("Employee and all related PDS records deleted successfully.", "success")
    else:
        flash("Failed to delete employee records.", "danger")
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
            pinfo_data = build_personal_info_payload(data)
            cols = list(pinfo_data.keys())
            vals = list(pinfo_data.values())

            if is_edit:
                if cols:
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
                placeholders = ', '.join(['%s'] * len(cols))
                cursor.execute(f"INSERT INTO pds_personal_information ({', '.join(cols)}) VALUES ({placeholders})", vals)
                personal_info_id = cursor.lastrowid
            # 2. Insert single-row tables (schema-matched automatically)
            single_row_tables = [
                'pds_spouse', 'pds_parents', 'pds_other_information', 'pds_declarations', 'pds_oath'
            ]
            for table in single_row_tables:
                # Custom mapping for spouse/parents because field names differ from DB columns
                if table == 'pds_spouse':
                    spouse_map = {
                        'surname': 'spouse_surname',
                        'first_name': 'spouse_first_name',
                        'middle_name': 'spouse_middle_name',
                        'name_extension': 'spouse_name_extension',
                        'occupation': 'spouse_occupation',
                        'employer': 'spouse_employer',
                        'business_address': 'spouse_biz_address',
                        'telephone_no': 'spouse_tel_no',
                    }
                    table_data = {col: _coerce_first(data.get(src)) for col, src in spouse_map.items()}
                elif table == 'pds_parents':
                    parents_map = {
                        'father_surname': 'father_surname',
                        'father_first_name': 'father_first_name',
                        'father_middle_name': 'father_middle_name',
                        'father_name_extension': 'father_name_extension',
                        'mother_maiden_surname': 'mother_surname',
                        'mother_first_name': 'mother_first_name',
                        'mother_middle_name': 'mother_middle_name',
                    }
                    table_data = {col: _coerce_first(data.get(src)) for col, src in parents_map.items()}
                elif table == 'pds_other_information':
                    other_map = {
                        'special_skills_hobbies': 'skills_hobbies',
                        'non_academic_distinctions': 'distinctions',
                        'membership_associations': 'memberships',
                    }
                    table_data = {col: _coerce_first(data.get(src)) for col, src in other_map.items()}
                elif table == 'pds_declarations':
                    declarations_map = {
                        # Yes/No radio answers (stored for reporting)
                        'q34a_answer': 'q34a',
                        'q34b_answer': 'q34b',
                        'q35a_answer': 'q35a',
                        'q35b_answer': 'q35b',
                        'q36_answer':  'q36',
                        'q37_answer':  'q37',
                        'q38a_answer': 'q38a',
                        'q38b_answer': 'q38b',
                        'q39_answer':  'q39',
                        'q40a_answer': 'q40a',
                        'q40b_answer': 'q40b',
                        'q40c_answer': 'q40c',
                        # Detail text fields
                        'related_appointing_authority_3rd_degree': 'decl_related_3rd',
                        'related_appointing_authority_4th_degree': 'decl_related_4th',
                        'administrative_offense_details': 'decl_admin_offense',
                        'criminal_charge_details': 'decl_criminal_charge',
                        'criminal_charge_date': 'decl_criminal_date',
                        'criminal_charge_status': 'decl_criminal_status',
                        'conviction_details': 'decl_conviction',
                        'separation_details': 'decl_separation',
                        'election_candidacy_details': 'decl_election',
                        'resignation_campaign_details': 'decl_resignation_campaign',
                        'immigrant_status_country': 'decl_immigrant_country',
                        'indigenous_group': 'decl_indigenous_group',
                        'pwd_id': 'decl_pwd_id',
                        'solo_parent_id': 'decl_solo_parent_id',
                    }
                    table_data = {col: _coerce_first(data.get(src)) for col, src in declarations_map.items()}
                    logger.info(f"Inserting declarations for personal_info_id={personal_info_id}: {table_data}")
                elif table == 'pds_oath':

                    oath_map = {
                        'government_id': 'gov_issued_id',
                        'id_number': 'id_no',
                        'issuance_date_place': 'date_place_issuance',
                        'signature': 'signature_path',
                        'date_signed': 'date_signed',
                        'thumbmark': 'thumbmark',
                    }
                    table_data = {col: _coerce_first(data.get(src)) for col, src in oath_map.items()}
                else:
                    table_data = match_data_to_schema(cursor, table, data)
                # Always insert declarations even if sparse (NULLs allowed)
                if table == 'pds_declarations' or any((v is not None and str(v).strip() != '') for v in table_data.values()):
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
                'monthly_salary': 'work_monthly_salary[]',
                'salary_job_pay_grade': 'work_salary_grade[]',
                'status_of_appointment': 'work_status[]',
                'gov_service': 'work_govt_service[]'
            }, personal_info_id)
            # Set is_present flag for work rows where date_to was 'PRESENT'
            _fix_work_is_present(cursor, personal_info_id, data)

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
                'contact': 'ref_tel_no[]'
            }, personal_info_id)
                
            # Session cleanup only on full success
            session.pop('pds_p1', None)
            session.pop('pds_p2', None)
            session.pop('pds_p3', None)
            session.pop('pds_p4', None)
            session.pop('editing_employee_id', None)
            session.pop('pds_excel_prefill', None)
            session.pop('pds_excel_temp_path', None)
            
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
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'success': True, 'message': msg})

            flash(msg, 'success')
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
                        occupation, employer, business_address, telephone_no)
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
                        mother_maiden_surname, mother_first_name, mother_middle_name)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (personal_info_id,
                      father.get('surname'), father.get('first_name'), father.get('middle_name'),
                      mother.get('maiden_surname'), mother.get('first_name'), mother.get('middle_name')))

            # ── 4. declarations ──────────────────────────────────────────
            decl = pds.get('declarations', {}) or {}
            if any(decl.values()):
                cursor.execute("""
                    INSERT INTO pds_declarations
                    (personal_info_id, related_appointing_authority_3rd_degree, related_appointing_authority_4th_degree,
                     administrative_offense_details, criminal_charge_details, criminal_charge_date, criminal_charge_status,
                     conviction_details, separation_details, election_candidacy_details, resignation_campaign_details,
                     immigrant_status_country, indigenous_group, pwd_id, solo_parent_id)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    personal_info_id,
                    decl.get('related_appointing_authority_3rd_degree'),
                    decl.get('related_appointing_authority_4th_degree'),
                    decl.get('administrative_offense_details'),
                    decl.get('criminal_charge_details'),
                    _clean_date(decl.get('criminal_charge_date')),
                    decl.get('criminal_charge_status'),
                    decl.get('conviction_details'),
                    decl.get('separation_details'),
                    decl.get('election_candidacy_details'),
                    decl.get('resignation_campaign_details'),
                    decl.get('immigrant_status_country'),
                    decl.get('indigenous_group'),
                    decl.get('pwd_id'),
                    decl.get('solo_parent_id')
                ))

            # ── 5. children ──────────────────────────────────────────────
            for child in fb.get('children', []):
                cursor.execute("""
                    INSERT INTO pds_children (personal_info_id, full_name, date_of_birth)
                    VALUES (%s,%s,%s)
                """, (personal_info_id, child.get('name'), child.get('date_of_birth') or None))

            # ── 5. education ─────────────────────────────────────────────
            for edu in pds.get('educational_background', []):
                def _year(val):
                    import re
                    if val is None:
                        return None
                    if isinstance(val, (int, float)):
                        try:
                            return int(val)
                        except Exception:
                            return None
                    s = str(val)
                    m = re.search(r"(\\d{4})", s)
                    return m.group(1) if m else None
                cursor.execute("""
                    INSERT INTO pds_education (personal_info_id, level, school_name, degree_course,
                        from_year, to_year, highest_level_units, year_graduated, scholarship_honors)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (personal_info_id, edu.get('level'), edu.get('school_name'), edu.get('degree'),
                      _year(edu.get('from')), _year(edu.get('to')), edu.get('highest_level'),
                      _year(edu.get('year_graduated')), edu.get('scholarships')))

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
                to_val = work.get('to')
                if isinstance(to_val, str) and to_val.strip().upper() == 'PRESENT':
                    to_val = None
                cursor.execute("""
                    INSERT INTO pds_work_experience
                    (personal_info_id, date_from, date_to, position_title, department_agency_company,
                     status_of_appointment, gov_service)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (personal_info_id, work.get('from') or None, to_val,
                      work.get('position'), work.get('department'),
                      work.get('appointment_status'), work.get('govt_service')))

            # ── 8. voluntary work ────────────────────────────────────────
            for vol in pds.get('voluntary_work', []):
                def _d(v): return _clean_date(v)
                cursor.execute("""
                    INSERT INTO pds_voluntary_work
                    (personal_info_id, organization, date_from, date_to, hours, position)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (personal_info_id, vol.get('organization'),
                      _d(vol.get('from')), _d(vol.get('to')),
                      vol.get('hours'), vol.get('position')))

            # ── 9. training / L&D ────────────────────────────────────────
            for trn in pds.get('training_programs', []):
                def _d(v): return _clean_date(v)
                cursor.execute("""
                    INSERT INTO pds_training
                    (personal_info_id, title, date_from, date_to, hours, type, conducted_by)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (personal_info_id, trn.get('title'),
                      _d(trn.get('from')), _d(trn.get('to')),
                      trn.get('hours'), trn.get('type'), trn.get('conducted_by')))

            # ── 10. other information ─────────────────────────────────────
            oi = pds.get('other_information', {})
            cursor.execute("""
                INSERT INTO pds_other_information
                (personal_info_id, special_skills_hobbies, non_academic_distinctions, membership_associations)
                VALUES (%s,%s,%s,%s)
            """, (personal_info_id,
                  ', '.join(oi.get('skills', [])),
                  ', '.join(oi.get('distinctions', [])),
                  ', '.join(oi.get('memberships', []))))

            # 11. references
            for ref in pds.get('references', []):
                cursor.execute("""
                    INSERT INTO pds_references (personal_info_id, full_name, address, contact)
                    VALUES (%s,%s,%s,%s)
                """, (personal_info_id, ref.get('name'), ref.get('address'), ref.get('contact')))

            # 12. government ID / oath block
            gid = pds.get('government_id', {}) or {}
            if any(gid.values()):
                cursor.execute("""
                    INSERT INTO pds_oath (personal_info_id, government_id, id_number, issuance_date_place)
                    VALUES (%s,%s,%s,%s)
                """, (personal_info_id, gid.get('type'), gid.get('number'), gid.get('date_place_of_issuance')))

        return jsonify({'success': True, 'personal_info_id': personal_info_id})

    except Exception as e:
        logger.error(f"Error saving PDS JSON to DB: {e}")
        return jsonify({'error': str(e)}), 500

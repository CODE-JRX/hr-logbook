import logging
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from db import get_db_cursor
from utils.excel_parser import parse_pds_excel

logger = logging.getLogger(__name__)

employee_bp = Blueprint('employee_bp', __name__)

@employee_bp.route('/admin/manage-employees')
def manage_employees():
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, surname, first_name, middle_name, sex, date_of_birth, mobile_no, email, agency_employee_no FROM pds_personal_information ORDER BY surname ASC")
            employees = cursor.fetchall()
            return render_template('admin/admin_manage_employees.html', employees=employees)
    except Exception as e:
        logger.error(f"Error fetching employees: {e}")
        return f"Database error: {e}", 500

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
        session['pds_p4'] = request.form.to_dict(flat=False)
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

from models.employee_model import get_employee_count, delete_employee

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
            # 1. pds_personal_information
            pinfo_data = match_data_to_schema(cursor, 'pds_personal_information', data)
            
            # fallback for required fields
            pinfo_data['surname'] = data.get('surname', [''])[0] if isinstance(data.get('surname'), list) else data.get('surname', '')
            pinfo_data['first_name'] = data.get('first_name', [''])[0] if isinstance(data.get('first_name'), list) else data.get('first_name', '')
            
            cols = list(pinfo_data.keys())
            vals = list(pinfo_data.values())
            
            if cols:
                placeholders = ', '.join(['%s'] * len(cols))
                cursor.execute(
                    f"INSERT INTO pds_personal_information ({', '.join(cols)}) VALUES ({placeholders})",
                    vals
                )
                personal_info_id = cursor.lastrowid
                
                # Insert dynamically into other tables
                tables = [
                    'pds_spouse', 'pds_parents', 'pds_children', 'pds_education',
                    'pds_work_experience', 'pds_civil_service_eligibility', 'pds_voluntary_work',
                    'pds_training', 'pds_other_information', 'pds_declarations', 'pds_references', 'pds_oath'
                ]
                
                for table in tables:
                    table_data = match_data_to_schema(cursor, table, data)
                    # Filter out purely None tables to avoid empty rows
                    if any(v is not None for v in table_data.values()):
                        table_data['personal_info_id'] = personal_info_id
                        t_cols = list(table_data.keys())
                        t_vals = list(table_data.values())
                        t_placeholders = ', '.join(['%s'] * len(t_cols))
                        cursor.execute(
                            f"INSERT INTO {table} ({', '.join(t_cols)}) VALUES ({t_placeholders})",
                            t_vals
                        )
                
            session.pop('pds_p1', None)
            session.pop('pds_p2', None)
            session.pop('pds_p3', None)
            session.pop('pds_p4', None)
            session.pop('pds_excel_prefill', None)
            
            flash("PDS successfully submitted!")
            return redirect(url_for('client.admin_dashboard'))
            
    except Exception as e:
        logger.error(f"Error submitting PDS: {e}")
        return f"Database error during submission: {e}", 500

@employee_bp.route('/api/employees/upload-pds-excel', methods=['POST'])
def upload_pds_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        try:
            file_content = file.read()
            parsed_data = parse_pds_excel(file_content)
            # Store in session so PDS pages can pre-fill themselves
            session['pds_excel_prefill'] = parsed_data
            # Clear any previous partial PDS session data
            for k in ('pds_p1', 'pds_p2', 'pds_p3', 'pds_p4'):
                session.pop(k, None)
            return jsonify({
                'success': True,
                'data': parsed_data,
                'redirect': url_for('employee_bp.pds_p1')
            })
        except Exception as e:
            logger.error(f"Error parsing Excel: {str(e)}")
            return jsonify({'error': f"Failed to parse Excel file: {str(e)}"}), 500
    return jsonify({'error': 'Invalid file type'}), 400


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


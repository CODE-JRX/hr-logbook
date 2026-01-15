from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, get_flashed_messages
from functools import wraps
from models.admin_model import add_admin, get_admin_by_email, verify_admin_credentials
from models.employee_model import *
from models.employee_model import search_employees
from models.face_embedding_model import add_face_embedding, find_best_match
from models.log_model import add_time_in, add_time_out, get_logs
from models.csm_form_model import insert_csm_form, get_csm_forms_filtered
from models.employee_model import get_departments
from models.log_model import get_logs_by_day, get_department_counts, get_purpose_counts, get_total_logs
from models.employee_model import get_employee_count
import os
import base64
import re
import face_recognition
import numpy as np
from datetime import datetime

employee_bp = Blueprint("employee", __name__)


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_id'):
            flash('Please sign in to access that page')
            return redirect(url_for('employee.admin_login'))
        return f(*args, **kwargs)
    return wrapper

@employee_bp.route("/employees")
@employee_bp.route("/employees")
@admin_required
def employee_data():
    employees = get_all_employees()
    return render_template("employees/employee_data.html", employees=employees)


@employee_bp.route("/")
def home():
    return render_template("index.html", year=datetime.now().year)


@employee_bp.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        employee_id = request.form.get("employee_id")
        full_name = request.form.get("full_name")
        department = request.form.get("department")
        gender = request.form.get("gender")
        age = request.form.get("age")

        # create employee row
        # ensure age is stored as integer when present
        try:
            age_val = int(age) if age not in (None, '') else None
        except Exception:
            age_val = None
        add_employee(employee_id, full_name, department, gender, age_val)

        # handle captured photo (data URL)
        photo_data = request.form.get("photo_data")
        if photo_data and employee_id:
            try:
                # extract base64 payload
                m = re.match(r"data:(image/\w+);base64,(.*)", photo_data)
                if m:
                    img_b64 = m.group(2)
                else:
                    # fallback if data URL prefix missing
                    img_b64 = photo_data.split(",", 1)[1] if "," in photo_data else photo_data

                image_bytes = base64.b64decode(img_b64)

                employees_dir = os.path.join(os.getcwd(), "Employees")
                os.makedirs(employees_dir, exist_ok=True)
                file_path = os.path.join(employees_dir, f"{employee_id}.jpg")
                with open(file_path, "wb") as f:
                    f.write(image_bytes)

                # compute face encoding
                img = face_recognition.load_image_file(file_path)
                encodings = face_recognition.face_encodings(img)
                if encodings:
                    embedding = list(encodings[0])
                    add_face_embedding(employee_id, embedding)
                else:
                    # no face found; optional: remove file or keep for debug
                    flash("No face detected in the uploaded photo; embedding not saved.")
            except Exception as e:
                # don't block adding employee if embedding fails
                flash(f"Failed to process photo: {e}")

        # If an admin performed the registration, keep the admin workflow.
        if session.get('admin_id'):
            flash('Client registered successfully')
            return redirect(url_for('employee.employee_data'))
        else:
            # Regular user self-registration — show a short confirmation page that
            # redirects to Client Log after a brief delay so the user can read it.
            message = 'Registration successful. You may now use the Client Log.'
            return render_template('registration_success.html', message=message, redirect_url=url_for('employee.employee_log'), delay=3500)
    # Consume any existing flashed messages so previous system messages (login/logout)
    # do not unexpectedly appear on the registration form page.
    get_flashed_messages()
    return render_template("employees/add.html")


@employee_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit(id):
    if request.method == "POST":
        update_employee(
            id,
            employee_id=request.form.get("employee_id"),
            full_name=request.form.get("full_name"),
            department=request.form.get("department"),
            gender=request.form.get("gender"),
            age=(int(request.form.get("age")) if request.form.get("age") not in (None, '') else None)
        )
        return redirect(url_for("employee.employee_data"))

    employee = get_employee_by_id(id)
    return render_template("employees/edit.html", employee=employee)


@employee_bp.route("/delete/<int:id>")
@admin_required
def delete(id):
    delete_employee(id)
    return redirect(url_for("employee.employee_data"))


@employee_bp.route('/employee-log')
def employee_log():
    return render_template('employee_log.html')



@employee_bp.route('/CSM-form', methods=['GET', 'POST'])
def csm_form():
    # Render and process the Customer Satisfaction Monitoring form
    if request.method == 'POST':
        try:
            # Basic fields
            control_no = request.form.get('control_no')
            date_val = request.form.get('date')  # expected YYYY-MM-DD
            agency_visited = request.form.get('agency_visited')
            client_type = request.form.get('client_type')
            sex = request.form.get('sex')
            region_of_residence = request.form.get('region_of_residence')
            email = request.form.get('email')
            # collect all checked services (multiple checkboxes named service_availed)
            services = request.form.getlist('service_availed') or []
            other_service = request.form.get('other_service')
            # if 'Others' was checked and an other_service text provided, include it
            if other_service and any(s.lower() == 'others' or s.lower() == 'other' for s in services):
                services = [s for s in services if s.lower() not in ('others', 'other')]
                services.append(other_service)
            service_availed = ', '.join(services) if services else None

            # numeric/ratings fields - convert where present
            def to_int(v):
                try:
                    return int(v) if v not in (None, '') else None
                except Exception:
                    return None

            age = to_int(request.form.get('age'))
            awareness_of_cc = to_int(request.form.get('awareness_of_cc'))
            cc_of_this_office_was = to_int(request.form.get('cc_of_this_office_was'))
            cc_help_you = to_int(request.form.get('cc_help_you'))

            sdq_vals = []
            for i in range(9):
                sdq_vals.append(to_int(request.form.get(f'sdq{i}')))

            suggestion = request.form.get('suggestion')

            new_id = insert_csm_form(
                control_no, date_val, agency_visited, client_type, sex, age, region_of_residence,
                email, service_availed, awareness_of_cc, cc_of_this_office_was, cc_help_you,
                sdq_vals, suggestion
            )

            if new_id:
                flash('CSM form submitted successfully')
                return redirect(url_for('employee.csm_form', submitted=1))
            else:
                flash('Failed to save CSM form (no id returned)')
                return redirect(url_for('employee.csm_form'))
        except Exception as e:
            flash('Failed to submit form: ' + str(e))
            return redirect(url_for('employee.csm_form'))

    # GET: render template
    return render_template('CSM-form.html')


@employee_bp.route('/search_employee')
def search_employee():
    # AJAX endpoint for live search (q=...)
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    try:
        rows = search_employees(q, limit=10)
        # return minimal fields for client
        results = [{'id': r['id'], 'employee_id': r['employee_id'], 'full_name': r.get('full_name')} for r in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@employee_bp.route('/today_logs')
def today_logs():
    # return all logs for the current day
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        rows = get_logs(start_date=today, end_date=today)
        # keep only needed fields
        results = []
        for r in rows:
            ti = r.get('time_in')
            to = r.get('time_out')
            results.append({
                'id': r.get('id'),
                'employee_id': r.get('employee_id'),
                'full_name': r.get('full_name'),
                'time_in': str(ti) if ti is not None else None,
                'time_out': str(to) if to is not None else None,
                'purpose': r.get('purpose')
            })
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@employee_bp.route('/employee-log-report')
@admin_required
def employee_log_report():
    # read filters from query string
    purpose = request.args.get('purpose')
    department = request.args.get('department')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    logs = get_logs(purpose=purpose, department=department, start_date=start_date, end_date=end_date)
    departments = get_departments()
    return render_template('employee_log_report.html', logs=logs, filters={'purpose': purpose, 'department': department, 'start_date': start_date, 'end_date': end_date}, departments=departments)


@employee_bp.route('/csm-report')
@admin_required
def csm_report():
    # Handle CSM form filtering and reporting
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    gender = request.args.get('gender')
    region = request.args.get('region')
    age_min = request.args.get('age_min')
    age_max = request.args.get('age_max')
    service = request.args.get('service')
    
    # Convert age_min/max to int if provided
    try:
        age_min = int(age_min) if age_min else None
        age_max = int(age_max) if age_max else None
    except (ValueError, TypeError):
        age_min = age_max = None
    
    # Get filtered CSM forms
    csm_forms = get_csm_forms_filtered(
        start_date=start_date,
        end_date=end_date,
        gender=gender,
        region=region,
        age_min=age_min,
        age_max=age_max,
        service=service
    )
    
    # Prepare filters dict for template
    filters = {
        'start_date': start_date,
        'end_date': end_date,
        'gender': gender,
        'region': region,
        'age_min': age_min,
        'age_max': age_max,
        'service': service
    }
    
    # Get list of unique services for dropdown (parse from all records)
    all_forms = get_csm_forms_filtered()
    services_set = set()
    for form in all_forms:
        if form.get('service_availed'):
            # service_availed is comma-separated; split and add each
            for svc in form['service_availed'].split(','):
                services_set.add(svc.strip())
    services_list = sorted(list(services_set))
    
    return render_template('csm_report.html', csm_forms=csm_forms, filters=filters, services=services_list)


@employee_bp.route('/admin/dashboard')
def admin_dashboard():
    # Protect dashboard - require admin login
    if not session.get('admin_id'):
        flash('Please sign in to access the admin dashboard')
        return redirect(url_for('employee.admin_login'))

    # Serve dashboard page (stats/empty) - chart data comes from /admin/chart_data
    total_employees = get_employee_count()
    total_logs = get_total_logs()
    return render_template('admin/admin_dashboard.html', stats={'total_employees': total_employees, 'total_logs': total_logs})


@employee_bp.route('/admin/chart_data')
def admin_chart_data():
    # Require admin session to access chart data
    if not session.get('admin_id'):
        return jsonify({'error': 'unauthorized'}), 401

    # return JSON for charts
    days = int(request.args.get('days', 14))
    by_day = get_logs_by_day(days)
    dept = get_department_counts()
    purpose = get_purpose_counts()
    return jsonify({'by_day': by_day, 'department': dept, 'purpose': purpose})


@employee_bp.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password') or request.form.get('confirm')

        if not (first_name and last_name and email and password):
            flash('All fields are required')
            return redirect(url_for('employee.admin_signup'))

        if password != confirm:
            flash('Passwords do not match')
            return redirect(url_for('employee.admin_signup'))

        if get_admin_by_email(email):
            flash('An account with that email already exists')
            return redirect(url_for('employee.admin_signup'))

        try:
            add_admin(first_name, last_name, email, password)
            flash('Account created. Please sign in.')
            return redirect(url_for('employee.admin_login'))
        except Exception as e:
            flash('Failed to create account: ' + str(e))
            return redirect(url_for('employee.admin_signup'))

    return render_template('admin/admin_signup.html')


@employee_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        admin = verify_admin_credentials(email, password)
        if admin:
            session['admin_id'] = admin['id']
            session['admin_email'] = admin['email']
            flash('Signed in successfully')
            return redirect(url_for('employee.admin_dashboard'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('employee.admin_login'))

    return render_template('admin/login.html')


@employee_bp.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_email', None)
    flash('Signed out')
    return render_template('admin/logout.html')


@employee_bp.route('/identify', methods=['POST'])
def identify():
    # Expects form field 'photo_data' (data URL)
    photo_data = request.form.get('photo_data')
    if not photo_data:
        return jsonify({'ok': False, 'error': 'No photo_data provided'}), 400

    try:
        # Extract base64
        import base64, re, io
        m = re.match(r"data:(image/\w+);base64,(.*)", photo_data)
        if m:
            img_b64 = m.group(2)
        else:
            img_b64 = photo_data.split(',', 1)[1] if ',' in photo_data else photo_data
        image_bytes = base64.b64decode(img_b64)

        # Load image into face_recognition
        from PIL import Image
        img = face_recognition.load_image_file(io.BytesIO(image_bytes))
        encodings = face_recognition.face_encodings(img)
        if not encodings:
            return jsonify({'ok': False, 'error': 'No face detected'}), 200

        encoding = list(encodings[0])
        emp_id, distance = find_best_match(encoding)
        if emp_id:
            emp = get_employee_by_employee_id(emp_id)
            return jsonify({'ok': True, 'employee_id': emp_id, 'full_name': emp.get('full_name') if emp else None, 'gender': emp.get('gender') if emp else None, 'age': emp.get('age') if emp else None, 'distance': distance}), 200
        else:
            return jsonify({'ok': False, 'error': 'No matching employee found'}), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@employee_bp.route('/generate_control_no')
def generate_control_no():
    """Generate a new control number in the format HR-S<YY>-<NextID>"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Get the highest ID from csm_form table
        cursor.execute("SELECT MAX(id) FROM csm_form")
        result = cursor.fetchone()
        max_id = result[0] if result[0] else 0
        next_id = max_id + 1
        conn.close()
        
        # Get last 2 digits of current year
        year = datetime.now().year
        yy = str(year)[-2:]
        
        # Format: HR-S<YY>-<NextID> with leading zeros (3 digits)
        control_no = f"HR-S{yy}-{next_id:03d}"
        
        return jsonify({'control_no': control_no}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@employee_bp.route('/log_action', methods=['POST'])
def log_action():
    data = request.json or {}
    employee_id = data.get('employee_id')
    action = data.get('action')  # 'time_in' or 'time_out'
    purpose = data.get('purpose')
    if not employee_id or action not in ('time_in', 'time_out'):
        return jsonify({'ok': False, 'error': 'Missing or invalid parameters'}), 400

    try:
        if action == 'time_in':
            add_time_in(employee_id, purpose)
        else:
            # Do not update purpose on time_out; purpose should come from the original time_in
            add_time_out(employee_id)
        return jsonify({'ok': True}), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500
    
@employee_bp.route('/terms-of-use', methods=['GET', 'POST'])
def term_of_use():
    if request.method == 'POST':
        accepted = request.form.get('accept_terms')
        if accepted == 'on':
            session['accepted_terms'] = True
            flash('Terms of Use accepted. You may now proceed.')
            return redirect(url_for('employee.add'))
        else:
            flash('You must accept the Terms of Use to proceed.')
    return render_template('terms_of_use.html')

@employee_bp.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy-policy.html')

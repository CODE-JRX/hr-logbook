from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models.admin_model import add_admin, get_admin_by_email, verify_admin_credentials
from models.employee_model import *
from models.face_embedding_model import add_face_embedding, find_best_match
from models.log_model import add_time_in, add_time_out, get_logs
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

@employee_bp.route("/employees")
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

        # create employee row
        add_employee(employee_id, full_name, department)

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

        return redirect(url_for("employee.employee_data"))
    return render_template("employees/add.html")


@employee_bp.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if request.method == "POST":
        update_employee(
            id,
            employee_id=request.form.get("employee_id"),
            full_name=request.form.get("full_name"),
            department=request.form.get("department")
        )
        return redirect(url_for("employee.employee_data"))

    employee = get_employee_by_id(id)
    return render_template("employees/edit.html", employee=employee)


@employee_bp.route("/delete/<int:id>")
def delete(id):
    delete_employee(id)
    return redirect(url_for("employee.employee_data"))


@employee_bp.route('/employee-log')
def employee_log():
    return render_template('employee_log.html')


@employee_bp.route('/employee-log-report')
def employee_log_report():
    # read filters from query string
    purpose = request.args.get('purpose')
    department = request.args.get('department')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    logs = get_logs(purpose=purpose, department=department, start_date=start_date, end_date=end_date)
    departments = get_departments()
    return render_template('employee_log_report.html', logs=logs, filters={'purpose': purpose, 'department': department, 'start_date': start_date, 'end_date': end_date}, departments=departments)


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
            return jsonify({'ok': True, 'employee_id': emp_id, 'full_name': emp.get('full_name') if emp else None, 'distance': distance}), 200
        else:
            return jsonify({'ok': False, 'error': 'No matching employee found'}), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


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

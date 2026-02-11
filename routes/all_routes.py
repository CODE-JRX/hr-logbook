from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, get_flashed_messages
from db import get_db
from functools import wraps
from models.admin_model import add_admin, get_admin_by_email, verify_admin_credentials
from models.client_model import *
from models.client_model import search_clients
from models.face_embedding_model import add_face_embedding, find_best_match
from models.admin_model import find_best_admin_match
from models.log_model import add_time_in, add_time_out, get_logs
from models.csm_form_model import insert_csm_form, get_csm_forms_filtered
from models.client_model import get_departments
from models.log_model import get_logs_by_day, get_department_counts, get_purpose_counts, get_total_logs
from models.client_model import get_client_count
import os
import base64
import re
import io
import face_recognition
import numpy as np
from datetime import datetime
from bson.objectid import ObjectId

client_bp = Blueprint("client", __name__)


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_id'):
            flash('Please sign in to access that page')
            return redirect(url_for('client.admin_login'))
        return f(*args, **kwargs)
    return wrapper

@client_bp.route("/clients")
@admin_required
def client_data():
    search = request.args.get('search', '')
    limit = request.args.get('limit', '25')
    clients = get_clients_filtered(search=search, limit=limit)
    return render_template("clients/client_data.html", clients=clients, search=search, limit=limit)

@client_bp.route("/clients_ajax")
@admin_required
def client_data_ajax():
    search = request.args.get('search', '')
    limit = request.args.get('limit', '25')
    clients = get_clients_filtered(search=search, limit=limit)
    # Return only the table rows as HTML
    return render_template("clients/client_data_rows.html", clients=clients)


@client_bp.route("/")
def home():
    return render_template("index.html", year=datetime.now().year)


@client_bp.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        client_id = get_next_client_id()
        full_name = request.form.get("full_name")
        department = request.form.get("department")
        gender = request.form.get("gender")
        age = request.form.get("age")
        client_type = request.form.get("client_type")

        # create client row
        # ensure age is stored as integer when present
        try:
            age_val = int(age) if age not in (None, '') else None
        except Exception:
            age_val = None
        add_client(client_id, full_name, department, gender, age_val, client_type)

        # handle captured photo (data URL)
        photo_data = request.form.get("photo_data")
        if photo_data and client_id:
            try:
                # extract base64 payload
                m = re.match(r"data:(image/\w+);base64,(.*)", photo_data)
                if m:
                    img_b64 = m.group(2)
                else:
                    # fallback if data URL prefix missing
                    img_b64 = photo_data.split(",", 1)[1] if "," in photo_data else photo_data

                image_bytes = base64.b64decode(img_b64)

                clients_dir = os.path.join(os.getcwd(), "Clients")
                os.makedirs(clients_dir, exist_ok=True)
                file_path = os.path.join(clients_dir, f"{client_id}.jpg")
                with open(file_path, "wb") as f:
                    f.write(image_bytes)

                # compute face encoding
                img = face_recognition.load_image_file(file_path)
                encodings = face_recognition.face_encodings(img)
                if encodings:
                    embedding = list(encodings[0])
                    add_face_embedding(client_id, embedding)
                else:
                    # no face found; optional: remove file or keep for debug
                    flash("No face detected in the uploaded photo; embedding not saved.")
            except Exception as e:
                # don't block adding client if embedding fails
                flash(f"Failed to process photo: {e}")

        # If an admin performed the registration, keep the admin workflow.
        if session.get('admin_id'):
            flash('Client registered successfully')
            return redirect(url_for('client.client_data'))
        else:
            # Regular user self-registration — show a short confirmation page that
            # redirects to Client Log after a brief delay so the user can read it.
            message = f'Registration successful. Your Client ID is {client_id}. You may now use the Client Log.'
            return render_template('registration_success.html', message=message, redirect_url=url_for('client.client_log'), delay=3500)
    # Consume any existing flashed messages so previous system messages (login/logout)
    # do not unexpectedly appear on the registration form page.
    get_flashed_messages()
    return render_template("clients/add.html")


@client_bp.route("/edit/<id>", methods=["GET", "POST"])
@admin_required
def edit(id):
    if request.method == "POST":
        update_client(
            id,
            client_id=request.form.get("client_id"),
            full_name=request.form.get("full_name"),
            department=request.form.get("department"),
            client_type=request.form.get("client_type"),
            gender=request.form.get("gender"),
            age=(int(request.form.get("age")) if request.form.get("age") not in (None, '') else None)
        )
        return redirect(url_for("client.client_data"))

    client = get_client_by_id(id)
    return render_template("clients/edit.html", client=client)


@client_bp.route("/delete/<id>")
@admin_required
def delete(id):
    delete_client(id)
    return redirect(url_for("client.client_data"))


@client_bp.route('/client-log')
def client_log():
    return render_template('client_log.html')



@client_bp.route('/CSM-form', methods=['GET', 'POST'])
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
                return redirect(url_for('client.csm_form', submitted=1))
            else:
                flash('Failed to save CSM form (no id returned)')
                return redirect(url_for('client.csm_form'))
        except Exception as e:
            flash('Failed to submit form: ' + str(e))
            return redirect(url_for('client.csm_form'))

    # GET: render template
    return render_template('CSM-form.html')


@client_bp.route('/search_client')
def search_client():
    # AJAX endpoint for live search (q=...)
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    try:
        rows = search_clients(q, limit=10)
        # return minimal fields for client
        results = [{'id': r['id'], 'client_id': r['client_id'], 'full_name': r.get('full_name')} for r in rows]
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@client_bp.route('/today_logs')
def today_logs():
    # return only logs for the current day where clients are still logged in (time_out IS NULL)
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        rows = get_logs(start_date=today, end_date=today)
        # keep only needed fields and filter out logged-out clients
        results = []
        for r in rows:
            ti = r.get('time_in')
            to = r.get('time_out')
            # Only include logs where time_out is NULL (still logged in)
            if to is None:
                results.append({
                    'id': r.get('id'),
                    'client_id': r.get('client_id'),
                    'full_name': r.get('full_name'),
                    'time_in': str(ti) if ti is not None else None,
                    'time_out': str(to) if to is not None else None,
                    'purpose': r.get('purpose'),
                    'department': r.get('department')
                })
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@client_bp.route('/client-log-report')
@admin_required
def client_log_report():
    # read filters from query string
    purpose = request.args.get('purpose')
    department = request.args.get('department')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = request.args.get('limit', '25')

    logs = get_logs(purpose=purpose, department=department, start_date=start_date, end_date=end_date, limit=limit)
    departments = get_departments()
    purposes = ["Receive Document/s Requested", "Submit Document/s", "Request Form/s", "Process Appointment", "Inquire", "OTHERS"]
    return render_template('client_log_report.html', logs=logs, filters={'purpose': purpose, 'department': department, 'start_date': start_date, 'end_date': end_date, 'limit': limit}, departments=departments, purposes=purposes)


@client_bp.route('/csm-report', methods=['GET', 'POST'])
@admin_required
def csm_report():
    # Handle POST requests for AJAX filtering
    if request.method == 'POST':
        try:
            data = request.get_json() or {}
            # Extract filters from JSON payload
            limit = data.get('limit', '25')
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            gender = data.get('gender')
            region = data.get('region')
            age_min = data.get('age_min')
            age_max = data.get('age_max')
            service = data.get('service')
            q = data.get('q', '')  # search query

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
                service=service,
                limit=limit
            )

            # If search query, filter further
            if q:
                q_lower = q.lower()
                csm_forms = [f for f in csm_forms if any(q_lower in str(f.get(field, '')).lower() for field in ['control_no', 'date', 'client_type', 'sex', 'age', 'region_of_residence', 'email', 'service_availed'])]

            # Render only the table rows
            from flask import render_template_string
            html = render_template_string('''
            {% for form in csm_forms %}
            <tr>
                <td><strong>{{ form.control_no }}</strong></td>
                <td>{{ form.date }}</td>
                <td>{{ form.client_type or '—' }}</td>
                <td>{{ form.sex or '—' }}</td>
                <td>{{ form.age or '—' }}</td>
                <td>{{ form.region_of_residence or '—' }}</td>
                <td>{{ form.email or '—' }}</td>
                <td style="font-size: 12px;">{{ form.service_availed or '—' }}</td>
            </tr>
            {% endfor %}
            ''', csm_forms=csm_forms)

            return jsonify({'html': html})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Handle CSV export
    if request.args.get('export') == 'csv':
        import csv
        from io import StringIO
        from flask import Response

        # Get all CSM forms (no filters for export)
        all_forms = get_csm_forms_filtered()

        # Generate CSV with all columns
        output = StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)

        # Write header
        header = [
            'ID', 'Control #', 'Date', 'Agency Visited', 'Client Type', 'Sex', 'Age',
            'Region of Residence', 'Email', 'Service Availed', 'Awareness of CC',
            'CC of This Office Was', 'CC Help You', 'SDQ0', 'SDQ1', 'SDQ2', 'SDQ3',
            'SDQ4', 'SDQ5', 'SDQ6', 'SDQ7', 'SDQ8', 'Suggestion', 'Created At'
        ]
        writer.writerow(header)

        # Write data rows
        for form in all_forms:
            row = [
                form.get('id', ''),
                form.get('control_no', ''),
                form.get('date', ''),
                form.get('agency_visited', ''),
                form.get('client_type', ''),
                form.get('sex', ''),
                form.get('age', ''),
                form.get('region_of_residence', ''),
                form.get('email', ''),
                form.get('service_availed', ''),
                form.get('awareness_of_cc', ''),
                form.get('cc_of_this_office_was', ''),
                form.get('cc_help_you', ''),
                form.get('sdq0', ''),
                form.get('sdq1', ''),
                form.get('sdq2', ''),
                form.get('sdq3', ''),
                form.get('sdq4', ''),
                form.get('sdq5', ''),
                form.get('sdq6', ''),
                form.get('sdq7', ''),
                form.get('sdq8', ''),
                form.get('suggestion', ''),
                form.get('created_at', '')
            ]
            writer.writerow(row)

        csv_content = output.getvalue()
        output.close()

        return Response(
            csv_content,
            mimetype='text/csv; charset=utf-8',
            headers={'Content-Disposition': 'attachment; filename=csm_report_all.csv'}
        )

    # Handle CSM form filtering and reporting
    limit = request.args.get('limit', '25')
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
        service=service,
        limit=limit
    )

    # Prepare filters dict for template
    filters = {
        'start_date': start_date,
        'end_date': end_date,
        'gender': gender,
        'region': region,
        'age_min': age_min,
        'age_max': age_max,
        'service': service,
        'limit': limit
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


@client_bp.route('/admin/dashboard')
def admin_dashboard():
    # Protect dashboard - require admin login
    if not session.get('admin_id'):
        flash('Please sign in to access the admin dashboard')
        return redirect(url_for('client.admin_login'))

    # Serve dashboard page (stats/empty) - chart data comes from /admin/chart_data
    total_clients = get_client_count()
    total_logs = get_total_logs()
    return render_template('admin/admin_dashboard.html', stats={'total_clients': total_clients, 'total_logs': total_logs})


@client_bp.route('/admin/chart_data')
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


@client_bp.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password') or request.form.get('confirm')
        photo_data = request.form.get('photo_data')

        if not (first_name and last_name and email and password and photo_data):
            flash('All fields are required, including photo')
            return redirect(url_for('client.admin_signup'))

        if password != confirm:
            flash('Passwords do not match')
            return redirect(url_for('client.admin_signup'))

        if get_admin_by_email(email):
            flash('An account with that email already exists')
            return redirect(url_for('client.admin_signup'))

        # Process photo and compute embedding
        embedding = None
        try:
            # Extract base64 payload
            m = re.match(r"data:(image/\w+);base64,(.*)", photo_data)
            if m:
                img_b64 = m.group(2)
            else:
                # fallback if data URL prefix missing
                img_b64 = photo_data.split(",", 1)[1] if "," in photo_data else photo_data

            image_bytes = base64.b64decode(img_b64)

            # Create admin first to get ID for file name
            admin_id = add_admin(first_name, last_name, email, password)

            # Save image file
            admins_dir = os.path.join(os.getcwd(), "Admins")
            os.makedirs(admins_dir, exist_ok=True)
            file_path = os.path.join(admins_dir, f"{admin_id}.jpg")
            with open(file_path, "wb") as f:
                f.write(image_bytes)

            # Compute face encoding
            img = face_recognition.load_image_file(file_path)
            encodings = face_recognition.face_encodings(img)
            if encodings:
                embedding = list(encodings[0])
                # Update admin with embedding
                db = get_db()
                db.admins.update_one({"_id": ObjectId(admin_id)}, {"$set": {"face_embedding": embedding}})
            else:
                # No face found; optional: remove file or keep for debug
                flash("No face detected in the uploaded photo; embedding not saved.")
        except Exception as e:
            flash(f"Failed to process photo: {e}")

        flash('Account created. Please sign in.')
        return redirect(url_for('client.admin_login'))

    return render_template('admin/admin_signup.html')


@client_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        admin = verify_admin_credentials(email, password)
        if admin:
            session['admin_id'] = admin['id']
            session['admin_email'] = admin['email']
            flash('Signed in successfully')
            return redirect(url_for('client.admin_dashboard'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('client.admin_login', type='password'))

    # If login type is password, show the regular login form
    if request.args.get('type') == 'password':
        return render_template('admin/login.html')
    
    # Default to face login
    return render_template('admin/face_login.html')


@client_bp.route('/admin/face_login', methods=['POST'])
def admin_face_login():
    photo_data = request.form.get('photo_data')
    if not photo_data:
        return jsonify({'ok': False, 'error': 'No photo_data provided'}), 400

    try:
        # Extract base64
        m = re.match(r"data:(image/\w+);base64,(.*)", photo_data)
        if m:
            img_b64 = m.group(2)
        else:
            img_b64 = photo_data.split(',', 1)[1] if ',' in photo_data else photo_data
        image_bytes = base64.b64decode(img_b64)

        # Load image into face_recognition
        img = face_recognition.load_image_file(io.BytesIO(image_bytes))
        encodings = face_recognition.face_encodings(img)
        if not encodings:
            return jsonify({'ok': False, 'error': 'No face detected'}), 200

        encoding = list(encodings[0])
        admin_id, distance = find_best_admin_match(encoding)
        if admin_id:
            # Get admin details
            db = get_db()
            admin = db.admins.find_one({"_id": ObjectId(admin_id)})
            if admin:
                session['admin_id'] = admin_id
                session['admin_email'] = admin.get('email')
                return jsonify({'ok': True}), 200
        return jsonify({'ok': False, 'error': 'Face not recognized'}), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@client_bp.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_email', None)
    flash('Signed out')
    return render_template('admin/logout.html')


@client_bp.route('/identify', methods=['POST'])
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
        client_id, distance = find_best_match(encoding)
        if client_id:
            cli = get_client_by_client_id(client_id)
            return jsonify({'ok': True, 'client_id': client_id, 'full_name': cli.get('full_name') if cli else None, 'gender': cli.get('gender') if cli else None, 'age': cli.get('age') if cli else None, 'distance': distance}), 200
        else:
            return jsonify({'ok': False, 'error': 'No matching client found'}), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@client_bp.route('/verify_face', methods=['POST'])
def verify_face():
    # Expects form field 'photo_data' (data URL)
    photo_data = request.form.get('photo_data')
    if not photo_data:
        return jsonify({'ok': False, 'message': 'No photo_data provided'}), 400

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
            return jsonify({'ok': False, 'message': 'No identifiable face detected. Please ensure your face is clear and well-lit.'}), 200

        # Check if face is clear (we can add more checks here if needed, e.g., face size, quality)
        # For now, just check if at least one face is detected
        return jsonify({'ok': True, 'message': 'Face detected successfully.'}), 200
    except Exception as e:
        return jsonify({'ok': False, 'message': f'Error verifying face: {str(e)}'}), 500


@client_bp.route('/generate_control_no')
def generate_control_no():
    """Generate a new control number in the format HR-S<YY>-<NextID>"""
    try:
        db = get_db()
        # Find the latest control_no to increment
        # Format: HR-S<YY>-<NNN>
        year = datetime.now().year
        yy = str(year)[-2:]
        prefix = f"HR-S{yy}-"
        
        # We can find the last created document that starts with this prefix
        # or simplified: just count + 1 (risk of collision if deletion happens, but adhering to requested logic of "NextID")
        # Let's try to find max from matching documents.
        
        latest_form = db.csm_form.find(
            {"control_no": {"$regex": f"^{prefix}"}}
        ).sort("control_no", -1).limit(1)
        
        next_id = 1
        try:
            doc = list(latest_form)
            if doc:
                last_no = doc[0].get('control_no')
                # extract last 3 digits
                parts = last_no.split('-')
                if len(parts) >= 3:
                     next_id = int(parts[-1]) + 1
        except:
            pass
            
        control_no = f"{prefix}{next_id:03d}"
        
        return jsonify({'control_no': control_no}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@client_bp.route('/log_action', methods=['POST'])
def log_action():
    data = request.json or {}
    client_id = data.get('client_id')
    action = data.get('action')  # 'time_in' or 'time_out'
    purposes = data.get('purposes', [])
    additional_info = data.get('additional_info')
    if not client_id or action not in ('time_in', 'time_out'):
        return jsonify({'ok': False, 'error': 'Missing or invalid parameters'}), 400

    try:
        if action == 'time_in':
            # Convert list of purposes to comma-separated string
            purpose_str = ', '.join(purposes) if purposes else None
            add_time_in(client_id, purpose_str, additional_info)
        else:
            # Do not update purpose on time_out; purpose should come from the original time_in
            add_time_out(client_id)
        return jsonify({'ok': True}), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@client_bp.route('/logout_client/<client_id>', methods=['POST'])
def logout_client(client_id):
    # Logout a specific client by setting time_out on their latest active log
    if not client_id:
        return jsonify({'ok': False, 'error': 'Missing client_id'}), 400

    try:
        add_time_out(client_id)
        return jsonify({'ok': True}), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500
    
@client_bp.route('/terms-of-use', methods=['GET', 'POST'])
def term_of_use():
    if request.method == 'POST':
        accepted = request.form.get('accept_terms')
        if accepted == 'on':
            session['accepted_terms'] = True
            flash('Terms of Use accepted. You may now proceed.')
            return redirect(url_for('client.add'))
        else:
            flash('You must accept the Terms of Use to proceed.')
    return render_template('terms_of_use.html')

@client_bp.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy-policy.html')

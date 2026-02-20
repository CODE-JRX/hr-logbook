# AI Agent Guide: HRMO E-Logbook V2

This document provides a high-level overview of the HRMO E-Logbook V2 system to help AI assistants understand the project's structure, architecture, and data flow.

## 🚀 Project Overview
**HRMO E-Logbook V2** is a biometric-based attendance and visitor log system. It uses face recognition for both clients (logging in/out) and administrators (secure dashboard access).

- **Backend**: Flask (Python)
- **Frontend**: HTML, Vanilla CSS (Modern/Interactive UI)
- **Database**: MySQL
- **Biometrics**: `face_recognition` library (dlib-based)

---

## 📂 Project Structure

```text
d:/hrmo-e-logbook-v2/
├── app.py                  # Entry point, blueprint registration
├── db.py                   # MySQL connection pooling logic
├── schema.sql              # Database schema definitions
├── routes/
│   ├── all_routes.py       # Main application logic (Clients, Identification, Forms)
│   └── backup_routes.py    # Database backup and restore operations
├── models/
│   ├── admin_model.py      # Admin CRUD and logic
│   ├── client_model.py     # Client CRUD and logic
│   ├── face_embedding_model.py # Face recognition & embedding storage logic
│   ├── log_model.py        # Log entry management
│   └── csm_form_model.py   # Client Satisfaction Measurement (CSM) logic
├── templates/              # HTML Templates (Jinja2)
│   ├── admin/              # Admin-specific pages (Face Login, etc.)
│   └── ...
├── static/                 # CSS, JS, and captured images
└── scripts/                # Utility scripts (Deployment, diagnostics)
```

---

## 🏛️ Architecture & Data Flow

### 1. Database Schema
- **`clients`**: Stores basic client information (ID, Name, Dept).
- **`face_embeddings`**: Stores 128D face encodings as JSON, linked to `clients`.
- **`logs`**: Daily log entries (time_in, time_out, purpose).
- **`admins`**: Administrator accounts with multi-factor support (Password + Face PIN).
- **`csm_form`**: Feedback data collected from visitors.

### 2. Biometric Data Flow (Identification)
1. **Capture**: Frontend captures frame from webcam -> Base64 string.
2. **Process**: Backend (`identify` route) decodes Base64 -> `face_recognition` processes image.
3. **Match**: `face_embedding_model.find_best_match` compares input embedding against all stored embeddings in the database using Euclidean distance (`np.linalg.norm`).
4. **Action**: If a match is found within the threshold (~0.7), the system creates a log entry or allows access.

### 3. Admin Authentication Flow
- **Standard**: Email + Password.
- **Enhanced (Face Login)**:
    1. Admin navigates to `/admin/face-login`.
    2. System identifies the face.
    3. Admin enters a 4-digit PIN for verification.
    4. Successful PIN match grants session access.

---

## 🛠️ Instructions for AI Agents

When modifying this project, follow these guidelines:

1. **Database Access**: Always use `db.get_db()` and ensure connections/cursors are closed properly to avoid leaks.
2. **Face Recognition**: Encodings are 128-element lists. When editing clients, handle multiple face angles (Center, Left, Right) to improve matching accuracy.
3. **UI Consistency**: Maintain the "Premium" look. Use Glassmorphism, CSS gradients, and smooth transitions defined in the templates.
4. **Error Handling**: Use `flash()` for user-facing errors and `server.log` or console prints for backend debugging.
5. **Routes**: Most logic resides in `routes/all_routes.py`. New features should generally be added there or in a new blueprint.

---

## 🧪 Verification & Debugging
- **Logs**: Check `server.log` for runtime errors.
- **Database**: Use `init_mysql.py` to reset/re-initialize the database if needed.
- **Diagnostics**: Run `diagnostics_backup.py` to check environment health.

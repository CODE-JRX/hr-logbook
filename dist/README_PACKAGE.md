Packaging & Quick restore (non-Docker)
====================================

Use these steps to package this project for transfer to another Windows machine and restore it there.

What to include in the package
- Project folder (all files in the repo)
- requirements.txt (created at repo root)
- `.env.example` (copy and edit to `.env` on target machine)
- `Employees/` (folder with saved photos) and `resources/` (static images)
- `hr_logbook_db.sql` (SQL dump of the MySQL database) — see below for how to export it

Exporting the database (on the source machine)
1. Ensure `mysqldump` is available (MySQL client tools installed).
2. Run in PowerShell from the repository root:

   .\scripts\export_db.ps1 -OutFile hr_logbook_db.sql

Creating the transfer ZIP (on source machine)
1. Run the helper script to create a packaged ZIP (includes SQL dump):

   .\scripts\package_project.ps1 -Out zip

   This produces `hr-logbook-package.zip` in the repo root.

Restoring on the target machine
1. Copy the ZIP and extract into a folder.
2. Create a Python venv and install requirements (PowerShell example):

   .\scripts\setup_windows.ps1

3. Create the database and import the dump (PowerShell / MySQL client):

   mysql -u root -p -e "CREATE DATABASE hr_logbook_db;"
   mysql -u root -p hr_logbook_db < hr_logbook_db.sql

4. Copy `.env.example` to `.env` and set credentials (DB_PASS etc.).
5. Start the app:

   .venv\Scripts\Activate.ps1; python app.py

Notes & prerequisites
- face_recognition requires native libraries (dlib). On Windows you will need Visual C++ Build Tools and CMake. On Linux, install: build-essential, cmake, libopenblas-dev, liblapack-dev.
- If installing `face_recognition` on Windows proves difficult, consider using Docker instead (recommended for reproducibility).

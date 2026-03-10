@echo off
echo ==========================================
echo Running HRMO E-Logbook V2 Automated Tests
echo Environment: Conda 'tf'
echo ==========================================

echo [1/4] Running Admin 2FA Flow (Signup, PIN, Face Matching)...
conda run -n tf python test_admin_2fa_flow.py
if %errorlevel% neq 0 (
    echo [ERROR] Admin 2FA Flow failed.
)

echo.
echo [2/4] Running Multi-Angle Face Recognition...
conda run -n tf python test_multi_angle_flow.py
if %errorlevel% neq 0 (
    echo [ERROR] Multi-Angle Flow failed.
)

echo.
echo [3/4] Running Backup Script...
conda run -n tf python test_backup_script.py
if %errorlevel% neq 0 (
    echo [ERROR] Backup Script failed.
)

echo.
echo [4/4] Running Restore Script...
conda run -n tf python test_restore_script.py
if %errorlevel% neq 0 (
    echo [WARNING] Restore Script finished with errors (check permission errors on Win).
)

echo ==========================================
echo Testing Complete!
echo Review logs above for details.
echo ==========================================
pause

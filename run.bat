@echo off
echo ===================================
echo   Starting HRMO Logbook Services...
echo ===================================

REM --- Set paths ---
set XAMPP_MYSQL=D:\xampp\
set PYAPP_DIR=D:\fr-hr-logbook

REM --- Start MySQL ---
echo Starting MySQL service...
start "" "%XAMPP_MYSQL%\mysql_start.bat"

REM --- Start Apache ---
echo Starting Apache service...
start "" "%XAMPP_MYSQL%\apache_start.bat"

REM --- Activate Conda env ---
echo Activating conda environment "tf"...
call conda activate tf

REM --- Run the python app ---
echo Running app.py...
cd /d "%PYAPP_DIR%"
python app.py

pause

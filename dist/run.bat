@echo off
echo ===================================
echo   Starting HRMO Logbook Services...
echo ===================================

REM --- Set paths ---
set PYAPP_DIR=D:\hrmo-e-logbook-v2



REM --- Activate Conda env ---
echo Activating conda environment "tf"...
call conda activate tf

REM --- Run the python app ---
echo Running app.py...
cd /d "%PYAPP_DIR%"
start "" python app.py
start http://127.0.0.1:5000
pause

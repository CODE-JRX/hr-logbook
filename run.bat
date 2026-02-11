@echo off
echo ===================================
echo   Starting HRMO Logbook Services...
echo ===================================


REM --- Activate Conda env ---
echo Activating conda environment "tf"...
call conda activate tf

REM --- Run the python app ---
echo Running app.py...
python app.py
start http://127.0.0.1:5000
pause

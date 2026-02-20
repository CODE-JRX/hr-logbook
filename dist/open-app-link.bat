@echo off
set URL=http://127.0.0.1:5000/

:: Try to open in default browser
start "" "%URL%"

if errorlevel 1 (
    echo Failed to open URL in default browser
    pause
    exit /b 1
)

echo URL opened successfully
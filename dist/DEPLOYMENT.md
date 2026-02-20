# Deployment Guide for Flask App with Nginx

This guide explains how to deploy the Flask application using Nginx as a reverse proxy and Waitress as the WSGI server.

## Prerequisites

- Python 3.x installed
- Nginx downloaded and extracted (nginx-1.24.0 folder in the project root)
- All dependencies installed via `pip install -r requirements.txt`

## Steps to Deploy

1. **Install Dependencies:**
   ```
   pip install -r requirements.txt
   ```

2. **Start Waitress Server:**
   - Run the `run_waitress.bat` file to start the Waitress server on port 8000.
   - Alternatively, run: `python -m waitress --host 127.0.0.1 --port 8000 wsgi:app`

3. **Start Nginx:**
   - Run the `start_nginx.bat` file to start Nginx on port 8080.
   - Alternatively, navigate to `nginx-1.24.0` and run: `nginx.exe`

4. **Access the Application:**
   - Open your browser and go to `http://localhost:8080`
   - The Flask app will be served through Nginx.

## Configuration Details

- **Gunicorn:** Runs the Flask app on `127.0.0.1:8000`
- **Nginx:** Listens on port 80 and proxies requests to Gunicorn.
- **Static Files:** Served directly by Nginx from the `css/`, `js/`, `resources/`, and `webfonts/` directories.

## Stopping the Servers

- To stop Nginx: Run `nginx-1.24.0/nginx.exe -s stop`
- To stop Gunicorn: Close the command prompt or use Ctrl+C in the terminal running Gunicorn.

## Notes

- Ensure no other services are running on ports 80 and 8000.
- For production, consider using a process manager like systemd or NSSM for Windows services.
- Update the secret key in `app.py` for security.

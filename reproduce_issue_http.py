import requests
import sys

def reproduce():
    session = requests.Session()
    
    # 1. Login
    print("Logging in...")
    login_url = "http://127.0.0.1:5000/admin/login"
    login_payload = {'email': 'test@test.com', 'password': 'password'}
    try:
        response = session.post(login_url, data=login_payload)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure it is running on http://127.0.0.1:5000")
        sys.exit(1)

    if "/admin/dashboard" not in response.url:
        print(f"Login failed? URL is {response.url}")
        sys.exit(1)
    
    print("Login successful.")

    # 2. Trigger Backup
    print("Triggering backup...")
    backup_url = "http://127.0.0.1:5000/admin/backup/download"
    response = session.get(backup_url)
    
    print(f"Response Status Code: {response.status_code}")
    print(f"Response URL: {response.url}")
    print(f"Content Type: {response.headers.get('Content-Type', '')}")
    
    if "application/zip" in response.headers.get("Content-Type", ""):
        print("Success: Backup file received.")
    else:
        print("Failure: Backup file not received.")
        print("Response text preview:")
        print(response.text[:500])

if __name__ == "__main__":
    reproduce()

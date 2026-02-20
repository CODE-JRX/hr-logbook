import sys
import os

# Add the project root to the python path so we can import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.admin_model import add_admin
from db import get_db

def main():
    print("Adding admin user...")
    try:
        # User requested: username: admin, pass: admin1001
        # accepted args: first_name, last_name, email, password
        admin_id = add_admin("Admin", "User", "admin@me", "admin1001")
        print(f"Successfully added admin user with ID: {admin_id}")
        print("Username (Email): admin@me")
        print("Password: admin1001")
    except Exception as e:
        print(f"Error adding admin user: {e}")

if __name__ == "__main__":
    main()

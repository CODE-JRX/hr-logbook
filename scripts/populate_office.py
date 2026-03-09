import sys
import os

# Add the project root to sys.path to allow importing from the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_cursor

def populate_office_column():
    """
    Populates the 'office' column in the 'logs' table with 'HRMO' 
    wherever the current value is NULL or an empty string.
    """
    print("--- Office Column Population Script ---")
    print("Targeting: 'logs' table")
    print("Action: Setting office = 'HRMO' for empty records")
    
    try:
        with get_db_cursor(commit=True) as cursor:
            # SQL query to update empty or null office entries
            # Using office IS NULL OR office = '' to catch all empty states
            query = "UPDATE logs SET office = 'HRMO' WHERE office IS NULL OR office = ''"
            
            cursor.execute(query)
            affected_rows = cursor.rowcount
            
            print(f"Done! Updated {affected_rows} rows.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure your database is running and the .env file is correctly configured.")

if __name__ == "__main__":
    populate_office_column()

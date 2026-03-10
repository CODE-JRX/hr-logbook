import mysql.connector
import os
import re
from dotenv import load_dotenv

load_dotenv()

def init_mysql():
    host = os.getenv("MYSQL_HOST", "localhost")
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "")
    database = os.getenv("MYSQL_DATABASE", "hrmo_elog_db")

    try:
        # Connect without database first to create it
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        print(f"Database '{database}' ready.")
        cursor.close()
        conn.close()

        # Connect with database to create/update tables
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor(dictionary=True)

        # Read and execute schema.sql (should be in root)
        schema_path = 'schema.sql'
        if not os.path.exists(schema_path):
            schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schema.sql')
        
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                sql_script = f.read()
                
                commands = sql_script.split(';')
                for command in commands:
                    cmd = command.strip()
                    if cmd and not cmd.startswith('USE') and not cmd.startswith('CREATE DATABASE'):
                        try:
                            # Remove comments
                            cmd_clean = re.sub(r'--.*', '', cmd)
                            if cmd_clean.strip():
                                cursor.execute(cmd_clean)
                                print(f"Executed: {cmd_clean.strip()[:60]}...")
                        except mysql.connector.Error as err:
                            if "already exists" not in str(err).lower() and "Duplicate entry" not in str(err).lower():
                                print(f"Warning/Error executing command: {err}")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("MySQL schema initialization complete.")

    except mysql.connector.Error as err:
        print(f"MySQL connection error: {err}")

if __name__ == "__main__":
    init_mysql()

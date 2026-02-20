import mysql.connector
import os
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

        # Connect with database to create tables
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()

        with open('schema.sql', 'r') as f:
            sql_script = f.read()
            # Split script into individual commands - simple split by semicolon
            # (Works for our current simple DDL)
            commands = sql_script.split(';')
            for command in commands:
                cmd = command.strip()
                if cmd and not cmd.startswith('USE') and not cmd.startswith('CREATE DATABASE'):
                    try:
                        cursor.execute(cmd)
                        print(f"Executed: {cmd[:50]}...")
                    except mysql.connector.Error as err:
                        print(f"Error executing command: {err}")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("MySQL schema initialization complete.")

    except mysql.connector.Error as err:
        print(f"MySQL connection error: {err}")

if __name__ == "__main__":
    init_mysql()

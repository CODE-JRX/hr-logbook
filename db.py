import mysql.connector
from mysql.connector import pooling
import os
import time
import logging
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MySQL Configuration
db_config = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "hrmo_elog_db")
}

# Connection pool — created at startup if MySQL is available,
# otherwise lazily created on first successful get_db() call.
connection_pool = None
_pool_creation_attempts = 0
_last_pool_error = None

# Expected database tables for schema validation
REQUIRED_TABLES = [
    'admins', 'clients', 'csm_form', 'face_embeddings', 'logs', 'offices',
    'pds_personal_information', 'pds_spouse', 'pds_parents', 'pds_children',
    'pds_education', 'pds_work_experience', 'pds_civil_service_eligibility',
    'pds_voluntary_work', 'pds_training', 'pds_other_information',
    'pds_declarations', 'pds_references', 'pds_oath'
]

def _create_pool(retry_count=0, max_retries=3):
    """
    Attempt to create the connection pool with retry logic.
    
    Args:
        retry_count: Current retry attempt
        max_retries: Maximum number of retries
    
    Returns:
        Connection pool or None if creation fails
    """
    global _pool_creation_attempts, _last_pool_error
    _pool_creation_attempts += 1
    
    try:
        pool = pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=10,
            **db_config
        )
        logger.info("Connection pool created successfully.")
        return pool
    except mysql.connector.errors.DatabaseError as err:
        _last_pool_error = str(err)
        logger.error(f"Database error creating connection pool: {err}")
        
        # Retry with exponential backoff for connection errors
        if retry_count < max_retries:
            wait_time = 2 ** retry_count  # 1, 2, 4 seconds
            logger.info(f"Retrying pool creation in {wait_time}s (attempt {retry_count + 1}/{max_retries})...")
            time.sleep(wait_time)
            return _create_pool(retry_count + 1, max_retries)
        return None
    except mysql.connector.Error as err:
        _last_pool_error = str(err)
        logger.error(f"Error creating connection pool: {err}")
        return None
    except Exception as err:
        _last_pool_error = str(err)
        logger.error(f"Unexpected error creating connection pool: {err}")
        return None

def validate_schema():
    """
    Validate that all required tables exist in the database.
    
    Returns:
        Tuple of (success: bool, missing_tables: list, error_msg: str)
    """
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        existing_tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        missing = [t for t in REQUIRED_TABLES if t not in existing_tables]
        if missing:
            error_msg = f"Missing database tables: {', '.join(missing)}"
            logger.error(error_msg)
            return False, missing, error_msg
        
        logger.info("Database schema validation passed.")
        return True, [], ""
    except mysql.connector.Error as err:
        error_msg = f"Schema validation failed: {err}"
        logger.error(error_msg)
        return False, [], error_msg
    except Exception as err:
        error_msg = f"Unexpected error during schema validation: {err}"
        logger.error(error_msg)
        return False, [], error_msg

# Try to create pool at import time
connection_pool = _create_pool()

def check_db_availability():
    """Helper to check if the database is actually reachable."""
    try:
        conn = mysql.connector.connect(**db_config)
        conn.close()
        return True
    except mysql.connector.Error as err:
        logger.warning(f"Database availability check failed: {err}")
        return False

def get_db():
    """
    Return a connection from the pool. If pool is None (MySQL was down
    at startup), try to create the pool first so the app auto-recovers
    after MySQL is fixed without needing a restart.
    
    Raises:
        Exception: If connection cannot be obtained
    """
    global connection_pool
    
    # Attempt to create pool if not initialized
    if connection_pool is None:
        logger.warning("Connection pool not initialized. Attempting to create...")
        connection_pool = _create_pool(retry_count=0, max_retries=2)
        if connection_pool is None:
            raise Exception(
                f"Database connection pool unavailable. MySQL server may be down. "
                f"Last error: {_last_pool_error}"
            )
    
    # Attempt to get connection from pool
    try:
        conn = connection_pool.get_connection()
        if conn is None:
            raise Exception("Connection pool returned None")
        return conn
    except mysql.connector.errors.PoolError as err:
        logger.error(f"Connection pool exhausted: {err}")
        raise Exception(
            "Connection pool exhausted. System is busy. Please try again later."
        )
    except mysql.connector.Error as err:
        logger.error(f"Error getting connection from pool: {err}")
        # Attempt to recover by recreating pool
        logger.info("Attempting to recreate connection pool...")
        connection_pool = _create_pool(retry_count=0, max_retries=1)
        if connection_pool is None:
            raise Exception(f"Failed to recover connection pool: {err}")
        
        # Try once more
        try:
            return connection_pool.get_connection()
        except Exception as retry_err:
            raise Exception(f"Failed to get connection after recovery attempt: {retry_err}")
    except Exception as err:
        logger.error(f"Unexpected error getting connection: {err}")
        raise

@contextmanager
def get_db_cursor(commit=False):
    """
    Context manager to get a database connection and cursor.
    Ensures that the connection is closed (returned to pool) even if an exception occurs.
    Handles transaction rollback on errors.
    
    Args:
        commit: If True, commits transaction on success; rolls back on error
    
    Usage:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("INSERT INTO table VALUES ...")
            # Auto-commit on success
            
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM table")
            result = cursor.fetchall()
            # Auto-rollback if exception occurs
    
    Raises:
        Exception: Database connection or query errors
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db()
        cursor = connection.cursor(dictionary=True)
        
        yield cursor
        
        if commit:
            try:
                connection.commit()
            except mysql.connector.Error as err:
                logger.error(f"Commit failed: {err}")
                connection.rollback()
                raise
    
    except mysql.connector.errors.ProgrammingError as err:
        logger.error(f"Programming error (SQL syntax): {err}")
        if commit and connection:
            connection.rollback()
        raise
    
    except mysql.connector.errors.DataError as err:
        logger.error(f"Data error (type mismatch): {err}")
        if commit and connection:
            connection.rollback()
        raise
    
    except mysql.connector.errors.IntegrityError as err:
        logger.error(f"Integrity error (constraint violation): {err}")
        if commit and connection:
            connection.rollback()
        raise
    
    except mysql.connector.Error as err:
        logger.error(f"Database error: {err}")
        if commit and connection:
            connection.rollback()
        raise
    
    except Exception as err:
        logger.error(f"Unexpected error in database operation: {err}")
        if commit and connection:
            try:
                connection.rollback()
            except Exception:
                pass
        raise
    
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception as err:
                logger.warning(f"Error closing cursor: {err}")
        
        if connection is not None:
            try:
                connection.close()
            except Exception as err:
                logger.warning(f"Error closing connection: {err}")



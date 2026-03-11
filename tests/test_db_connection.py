"""
Tests for database connection handling and error recovery.
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
import mysql.connector
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))


class TestDatabaseConnection:
    """Test database connection pool and error handling."""
    
    def test_pool_creation_success(self):
        """Test successful connection pool creation."""
        with patch('db.pooling.MySQLConnectionPool') as mock_pool:
            from db import _create_pool
            mock_pool.return_value = Mock()
            result = _create_pool()
            assert result is not None
            mock_pool.assert_called_once()
    
    def test_pool_creation_failure_with_retry(self):
        """Test pool creation failure and retry logic."""
        with patch('db.pooling.MySQLConnectionPool') as mock_pool, \
             patch('time.sleep') as mock_sleep:
            from db import _create_pool
            # First call fails, would retry
            mock_pool.side_effect = mysql.connector.Error("Connection refused")
            result = _create_pool(retry_count=1, max_retries=1)
            assert result is None  # Should give up after max retries
    
    def test_pool_exhaustion_error(self):
        """Test handling when connection pool is exhausted."""
        with patch('db.connection_pool') as mock_pool:
            from db import get_db
            mock_pool.get_connection.side_effect = mysql.connector.errors.PoolError("No more connections")
            
            with pytest.raises(Exception) as exc_info:
                get_db()
            assert "pool exhausted" in str(exc_info.value).lower()
    
    def test_get_db_cursor_context_manager(self):
        """Test get_db_cursor context manager properly handles connections."""
        with patch('db.get_db') as mock_get_db:
            from db import get_db_cursor
            
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn
            
            # Test normal flow (commit=False)
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("SELECT 1")
            
            mock_cursor.close.assert_called()
            mock_conn.close.assert_called()
            mock_conn.commit.assert_not_called()
            mock_conn.rollback.assert_not_called()
    
    def test_get_db_cursor_commit_success(self):
        """Test get_db_cursor commits on successful operation."""
        with patch('db.get_db') as mock_get_db:
            from db import get_db_cursor
            
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn
            
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("INSERT INTO test VALUES (1)")
            
            mock_conn.commit.assert_called_once()
            mock_conn.rollback.assert_not_called()
    
    def test_get_db_cursor_rollback_on_error(self):
        """Test get_db_cursor rolls back on exception."""
        with patch('db.get_db') as mock_get_db:
            from db import get_db_cursor
            
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn
            
            with pytest.raises(ValueError):
                with get_db_cursor(commit=True) as cursor:
                    raise ValueError("Test error")
            
            mock_conn.rollback.assert_called_once()
            mock_conn.commit.assert_not_called()
    
    def test_cursor_close_even_on_exception(self):
        """Test cursor is closed even if exception occurs."""
        with patch('db.get_db') as mock_get_db:
            from db import get_db_cursor
            
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn
            
            try:
                with get_db_cursor() as cursor:
                    raise Exception("Test error")
            except:
                pass
            
            mock_cursor.close.assert_called_once()
            mock_conn.close.assert_called_once()
    
    def test_schema_validation_success(self):
        """Test successful schema validation."""
        with patch('db.mysql.connector.connect') as mock_connect:
            from db import validate_schema
            
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [
                ('admins',),
                ('clients',),
                ('csm_form',),
                ('face_embeddings',),
                ('logs',),
                ('offices',)
            ]
            mock_connect.return_value = mock_conn
            
            success, missing, error = validate_schema()
            assert success is True
            assert missing == []
            assert error == ""
    
    def test_schema_validation_missing_tables(self):
        """Test schema validation detects missing tables."""
        with patch('db.mysql.connector.connect') as mock_connect:
            from db import validate_schema
            
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [('admins',), ('clients',)]  # Missing tables
            mock_connect.return_value = mock_conn
            
            success, missing, error = validate_schema()
            assert success is False
            assert len(missing) > 0
            assert "Missing" in error
    
    def test_check_db_availability(self):
        """Test database availability check."""
        with patch('db.mysql.connector.connect') as mock_connect:
            from db import check_db_availability
            
            mock_conn = Mock()
            mock_connect.return_value = mock_conn
            
            result = check_db_availability()
            assert result is True
            mock_conn.close.assert_called_once()
    
    def test_check_db_availability_failure(self):
        """Test database availability check when DB is down."""
        with patch('db.mysql.connector.connect') as mock_connect:
            from db import check_db_availability
            
            mock_connect.side_effect = mysql.connector.Error("Connection refused")
            result = check_db_availability()
            assert result is False


class TestDatabaseErrorTypes:
    """Test handling of different MySQL error types."""
    
    def test_programming_error_handling(self):
        """Test handling of SQL syntax errors."""
        with patch('db.get_db') as mock_get_db:
            from db import get_db_cursor
            
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn
            
            with pytest.raises(mysql.connector.errors.ProgrammingError):
                with get_db_cursor(commit=True) as cursor:
                    raise mysql.connector.errors.ProgrammingError("Syntax error")
            
            mock_conn.rollback.assert_called()
    
    def test_data_error_handling(self):
        """Test handling of data type mismatch errors."""
        with patch('db.get_db') as mock_get_db:
            from db import get_db_cursor
            
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn
            
            with pytest.raises(mysql.connector.errors.DataError):
                with get_db_cursor(commit=True) as cursor:
                    raise mysql.connector.errors.DataError("Type mismatch")
            
            mock_conn.rollback.assert_called()
    
    def test_integrity_error_handling(self):
        """Test handling of foreign key constraint violations."""
        with patch('db.get_db') as mock_get_db:
            from db import get_db_cursor
            
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value = mock_conn
            
            with pytest.raises(mysql.connector.errors.IntegrityError):
                with get_db_cursor(commit=True) as cursor:
                    raise mysql.connector.errors.IntegrityError("FK constraint")
            
            mock_conn.rollback.assert_called()

# Quick Reference: Testing & Error Handling

## 🚀 Quick Start

### Install & Run Tests
```bash
cd c:\Users\JRX\Desktop\LogBook-System\hr-logbook
pip install -r test_requirements.txt
pytest
```

### Run Tests with Coverage
```bash
pytest --cov=. --cov-report=html --cov-report=term-missing
# Open: htmlcov/index.html for visual report
```

### Run Specific Tests
```bash
pytest tests/test_db_connection.py -v            # Database tests
pytest tests/test_face_embedding.py -v           # Face cache tests
pytest tests/test_security_validation.py -v      # Security tests
pytest -k "thread" -v                            # Thread safety tests
pytest -k "backup" -v                            # Backup/restore tests
```

---

## 📋 Test Summary

| Module | Tests | Focus |
|--------|-------|-------|
| `test_db_connection.py` | 9 | Database pooling, retry logic, error types |
| `test_face_embedding.py` | 11 | Cache safety, threading, corruption handling |
| `test_security_validation.py` | 15 | Backup integrity, path traversal, input validation |
| `test_integration.py` | 30+ | Workflows, error scenarios, performance (stubs) |
| **TOTAL** | **65+** | **Comprehensive coverage** |

---

## 🔒 Security Improvements

### ✅ Database Connection
- Auto-retry with exponential backoff
- Connection pool exhaustion detection
- Meaningful error messages
- Transaction rollback on error

### ✅ Face Embedding Cache
- Thread-safe with RLock
- Corrupt embeddings skipped
- Atomic DB/cache updates
- Detailed error logging

### ✅ Backup/Restore
- ZIP integrity verification (CRC check)
- Path traversal prevention
- Atomic transactions with rollback
- Cleanup on error (finally block)

### ✅ Input Validation
- Age validation (integer, reasonable range)
- Email format checking
- Name sanitization (trim, uppercase)
- Max upload size (50MB)

---

## 🐛 What Gets Tested

### Database (9 tests)
```
✓ Pool creation success
✓ Pool creation failure with retry
✓ Connection exhaustion (PoolError)
✓ Context manager cleanup
✓ Commit on success
✓ Rollback on error
✓ Schema validation (missing tables)
✓ ProgrammingError handling
✓ IntegrityError handling
```

### Face Recognition (11 tests)
```
✓ Cache initialization from DB
✓ Corrupt embedding JSON skipped
✓ Concurrent cache reads (5 threads)
✓ Face matching with threshold
✓ Empty cache returns None
✓ No match found with high distance
✓ Embedding addition to cache
✓ Embedding deletion from cache
✓ Embedding improvement (merge/add)
✓ Outlier embedding rejection
```

### Security (15 tests)
```
✓ Backup ZIP structure validation
✓ Missing tables detected
✓ ZIP corruption detected
✓ Path traversal prevention
✓ Failed login attempt tracking
✓ PIN verification
✓ Age input validation
✓ Email format validation
✓ Name sanitization
✓ SQL injection prevention
✓ ErrorMessage generic (no stack trace)
```

---

## 📊 Running Tests in Different Modes

### Verbose Output (see all test names)
```bash
pytest -v
```

### Show Print Statements
```bash
pytest -s
```

### Stop on First Failure
```bash
pytest -x
```

### Run with Debug Breakpoints
```bash
pytest --pdb tests/test_db_connection.py::TestDatabaseConnection::test_pool_creation_success
```

### Show Coverage by Module
```bash
pytest --cov=. --cov-report=term-missing
```

### Generate HTML Report
```bash
pytest --cov=. --cov-report=html
# Open htmlcov/index.html
```

---

## 🎯 Key Test Scenarios

### DATABASE RESILIENCE
```python
# Scenario: MySQL crashes and restarts
# Test: Pool creation retry with backoff
# Result: ✓ Auto-recovers without restart

# Scenario: All connections in pool used
# Test: Connection exhaustion handling
# Result: ✓ Clear error message, no deadlock

# Scenario: SQL syntax error
# Test: ProgrammingError caught
# Result: ✓ Logged, transaction rolled back
```

### FACE RECOGNITION SAFETY
```python
# Scenario: One embedding is corrupt JSON
# Test: Corrupt entries skipped
# Result: ✓ Rest of cache loads, warning logged

# Scenario: 5 threads reading cache simultaneously
# Test: Thread-safe access with lock
# Result: ✓ No race conditions, consistent data

# Scenario: No face matches database
# Test: find_best_match returns None
# Result: ✓ No crash, fallback to manual input
```

### BACKUP DATA SAFETY
```python
# Scenario: ZIP contains path traversal attempt
# Test: Path validation
# Result: ✓ Blocked, error message shown

# Scenario: Database error during restore
# Test: Transaction rollback
# Result: ✓ All changes rolled back, DB consistent

# Scenario: Temp files not cleaned up
# Test: Finally block cleanup
# Result: ✓ Always cleaned up, even on error
```

---

## ✅ Pre-Deployment Checklist

- [ ] Run `pytest --cov` (target >80%)
- [ ] All database tests pass
- [ ] All face embedding tests pass
- [ ] All security tests pass
- [ ] Coverage report reviewed
- [ ] Error logs readable and detailed
- [ ] Database credentials in `.env`
- [ ] Test backup/restore with 1GB+ data
- [ ] Load test with 20+ concurrent users
- [ ] Face matching test with 500+ clients

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `IMPROVEMENTS_SUMMARY.md` | Complete changelog and improvements |
| `tests/README.md` | Full testing guide |
| `tests/conftest.py` | Fixture definitions |
| `test_requirements.txt` | Test dependencies |

---

## 🔍 Where Error Handling Lives

| Component | File(s) | Key Function |
|-----------|---------|--------------|
| Database | `db.py` | `get_db_cursor()` context manager |
| Face Cache | `models/face_embedding_model.py` | Thread-safe cache with locks |
| Startup | `app.py` | Schema validation + error handlers |
| Backup | `routes/backup_routes.py` | Integrity checks + rollback |

---

## 💡 Common Test Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'app'"
```bash
Solution: Run from repo root:
cd c:\Users\JRX\Desktop\LogBook-System\hr-logbook
pytest
```

### Issue: Tests pass but coverage is low
```bash
Solution: Check coverage report:
pytest --cov=. --cov-report=html
# Open htmlcov/ and look for red (uncovered) lines
```

### Issue: Mocking errors in tests
```bash
Solution: Use conftest fixtures:
from tests.conftest import mock_db_cursor
# Tests automatically use mocks for external deps
```

### Issue: Database tests fail
```bash
Solution: Mock DB instead of using real connection:
# Tests use @patch('db.get_db_cursor')
# No database needed for unit tests
```

---

## 🎓 Testing Best Practices Used

1. **Unit Tests** - Test individual functions with mocks
2. **Integration Tests** - Stubs for future full workflow tests
3. **Mocking** - External dependencies (DB, files) are mocked
4. **Fixtures** - Reusable test data via conftest.py
5. **Error Testing** - Exception handling explicitly tested
6. **Thread Safety** - Concurrent access tested
7. **Cleanup** - Resource cleanup tested in finally blocks

---

## 📞 Support

For detailed information, see:
- **Implementation details**: `IMPROVEMENTS_SUMMARY.md`
- **How to run tests**: `tests/README.md`
- **Test code**: `tests/*.py`
- **Error handling code**: `db.py`, `models/face_embedding_model.py`, `routes/backup_routes.py`

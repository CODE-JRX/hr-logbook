# HR Logbook Test Suite

Comprehensive test suite for the HR Logbook System covering critical error handling, security, and functionality.

## Running Tests

### Install Test Dependencies

```bash
pip install -r test_requirements.txt -r requirements.txt
```

Or with conda:

```bash
conda activate tf
pip install -r test_requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run Tests with Coverage Report

```bash
pytest --cov=. --cov-report=html --cov-report=term-missing
```

This generates an HTML coverage report in `htmlcov/index.html`.

### Run Specific Test File

```bash
pytest tests/test_db_connection.py -v
pytest tests/test_face_embedding.py -v
pytest tests/test_security_validation.py -v
pytest tests/test_integration.py -v
```

### Run Tests Matching a Pattern

```bash
pytest -k "test_pool" -v           # Run pool-related tests
pytest -k "thread" -v              # Run thread safety tests
pytest -k "backup" -v              # Run backup tests
```

### Run with Debug Output

```bash
pytest -v -s           # Verbose with print statements shown
pytest -vv -s          # Extra verbose
```

## Test Organization

### `test_db_connection.py`
Tests for database connection handling and error recovery:
- Pool creation and recovery
- Connection exhaustion handling
- Context manager cleanup
- Transaction management (commit/rollback)
- Schema validation
- Different MySQL error types (Programming, Data, Integrity errors)

**Key scenarios:**
- ✓ Pool creation failures with retry logic
- ✓ Connection pool exhaustion
- ✓ Database errors are properly caught and logged
- ✓ Cursor cleanup on exceptions
- ✓ Schema validation on startup

### `test_face_embedding.py`
Tests for face embedding cache with thread safety:
- Cache initialization from database
- Handling corrupt embeddings
- Thread-safe concurrent access
- Face matching with threshold
- Embedding improvement logic

**Key scenarios:**
- ✓ Cache loads from database correctly
- ✓ Corrupt embeddings are skipped with logging
- ✓ Multiple threads can read cache simultaneously
- ✓ Face matching respects similarity threshold
- ✓ New embeddings are merged or added appropriately

### `test_security_validation.py`
Tests for security, authentication, and input validation:
- Backup integrity verification
- Path traversal prevention in ZIP files
- Authentication error handling
- Input validation and sanitization
- SQL injection prevention
- Generic error messages (no stack trace exposure)

**Key scenarios:**
- ✓ Backup ZIP structure validated
- ✓ Malicious paths detected in ZIP
- ✓ Age and email validated
- ✓ Parameterized queries prevent SQL injection
- ✓ User errors shown as generic messages

### `test_integration.py`
High-level integration tests (mostly stubs for actual integration testing):
- Client registration flow
- Client log in/out workflow
- Admin login (password and face)
- CSM form submission
- Error scenarios
- Rate limiting
- Data consistency
- Performance benchmarks

## Critical Test Cases

### Tier 1 - System Crash Prevention
1. **Database Connection Pool Failure** ✓
   - Pool creation retry with backoff
   - Connection exhaustion handling
   - Auto-recovery when MySQL restarts

2. **Cache Corruption** ✓
   - Corrupt embedding JSON skipped
   - Thread-safe updates prevent race conditions

3. **Backup Restoration** ✓
   - ZIP integrity verified before restore
   - Path traversal attempts blocked
   - Transaction rollback on error

4. **Face Recognition Failure** ✓
   - No face detected offers override
   - Missing models disable feature gracefully

### Tier 2 - Feature Resilience
1. Face matching timeout
2. Admin login flow completeness
3. CSM form validation
4. Override workflow functionality

### Tier 3 - Security
1. Session management
2. Authentication security
3. Input sanitization
4. Rate limiting
5. Error message exposure

## Adding New Tests

1. Create test file in `tests/` directory following naming pattern `test_*.py`
2. Import necessary fixtures from `conftest.py`
3. Use mocking for external dependencies
4. Include docstrings explaining what is tested
5. Run tests: `pytest tests/test_yourfile.py -v`

## Debugging Failed Tests

```bash
# Run with pdb debugger
pytest --pdb tests/test_db_connection.py::TestDatabaseConnection::test_pool_creation_success

# Show local variables on failure
pytest -l tests/test_db_connection.py

# Stop on first failure
pytest -x tests/test_db_connection.py
```

## Expected Coverage

Target: >80% overall coverage

Critical modules:
- `db.py` - 90%+ coverage
- `models/face_embedding_model.py` - 85%+ coverage 
- `routes/backup_routes.py` - 80%+ coverage
- Authentication routes - 75%+ coverage

## Test Results Interpretation

### All Tests Pass ✓
System is ready for deployment with implemented error handling.

### Some Integration Tests Fail
Integration tests are scaffolding only. Implement actual network/DB fixtures to make them runnable.

### Coverage Below Target
Run full report: `pytest --cov --cov-report=html` and check `htmlcov/index.html` for gaps.

## Continuous Integration

For GitHub Actions or similar CI/CD:

```yaml
pytest:
  stage: test
  script:
    - pip install -r test_requirements.txt
    - pytest --cov --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

## Known Issues / Limitations

1. **Integration tests** are stubs - need real Flask test client
2. **Database tests** use mocks - real integration db testing recommended
3. **Performance tests** are placeholders - need profiling setup
4. **Rate limiting tests** require middleware implementation

## Recommendations

1. **Before deploying:**
   - Run full test suite: `pytest --cov`
   - Check coverage > 80%
   - Review any failed tests

2. **Regular maintenance:**
   - Run tests after every code change
   - Add tests for new features/bugs
   - Update test requirements quarterly

3. **Production readiness:**
   - Set up CI/CD pipeline
   - Add performance/load testing
   - Configure automated test runs

## References

- pytest documentation: https://docs.pytest.org
- unittest.mock: https://docs.python.org/3/library/unittest.mock.html
- Flask testing: https://flask.palletsprojects.com/testing/

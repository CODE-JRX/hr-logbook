# Backup & Restore Issues - Analysis & Fixes

## Issues Found

### 🔴 CRITICAL Issue 1: Restore Transaction Not Committed
**Location**: [routes/backup_routes.py](routes/backup_routes.py#L263)  
**Severity**: CRITICAL - Data is restored but never persisted

**Problem**:
```python
with get_db_cursor(commit=False) as cursor:  # commit=False so we control it
```

**Impact**:
- When `commit=False`, the context manager WILL NOT commit changes
- All database restoration operations are performed but never saved
- File system image restoration happens, but database remains unchanged
- User sees "Restore successful" but data is actually lost

**Root Cause**:
- The context manager `get_db_cursor()` only commits when `commit=True`
- The code comment says "we control it" but there is NO manual `connection.commit()` call
- When context exits, transaction is rolled back implicitly

**Fix**:
Change line 263 from:
```python
with get_db_cursor(commit=False) as cursor:
```
To:
```python
with get_db_cursor(commit=True) as cursor:
```

---

### 🟡 Issue 2: Inconsistent Table Lists
**Location**: [routes/backup_routes.py](routes/backup_routes.py#L47) vs [test_backup_script.py](test_backup_script.py#L12)

**Problem**:
- `backup_routes.py` line 47: `TABLES = ['offices', 'admins', 'clients', 'csm_form', 'face_embeddings', 'logs']` (6 tables)
- `test_backup_script.py` line 12: `TABLES = ['admins', 'clients', 'csm_form', 'face_embeddings', 'logs']` (5 tables - missing 'offices')

**Impact**:
- The test script doesn't verify 'offices' table backup
- Inconsistency between test and actual code

**Fix**: 
Update test_backup_script.py line 12 to include 'offices'

---

### 🟡 Issue 3: Potential Image Restore Path Traversal (Minor)
**Location**: [routes/backup_routes.py](routes/backup_routes.py#L357-L375)

**Current Code**:
```python
for item in os.listdir(src_folder):
    s = os.path.join(src_folder, item)
    d = os.path.join(dst_folder, item)
    
    if os.path.isdir(s):
        if os.path.exists(d):
            shutil.rmtree(d)
        shutil.copytree(s, d)
    else:
        os.makedirs(dst_folder, exist_ok=True)
        shutil.copy2(s, d)
```

**Issue**:
- While ZIP paths are validated, the image copy logic doesn't normalize the copied paths
- If somehow a malicious path gets through, it could cause issues

**Fix**:
Add path normalization before copying

---

## Summary

| Issue | Severity | Component | Status |
|-------|----------|-----------|--------|
| No transaction commit on restore | CRITICAL | restore_backup() | NEEDS FIX |
| Missing 'offices' in test TABLES | LOW | test_backup_script.py | NEEDS FIX |
| Image copy path validation | LOW | image restore logic | OPTIONAL FIX |

---

## Testing Recommendations

After fixes:
1. Create test backup
2. Modify a single record in database
3. Restore from backup
4. Verify database matches backup (SELECT * checks)
5. Verify image files restored
6. Check admin logs for successful restore

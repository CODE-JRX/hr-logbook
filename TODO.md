# PDS Page 4 Insert Fix - Progress Tracker

## Status: ✅ Plan Approved - Starting Implementation

### Step 1: [IN PROGRESS] Create TODO.md ✅
- Created this file with breakdown

### Step 2: ✅ Add logging & force insert to routes/employee_routes.py
- Log declarations data before insert ✅
- Remove "if any" condition for pds_declarations insert ✅
- Ensure session cleanup only on success ✅

### Step 3: ✅ Add debug button to templates/employees/pds-p4.html
- Console dump form data ✅ (fixed JS quoting)
- Ensure radio + details validation

### Step 4: ✅ Minor update models/employee_model.py
- Add query to count declarations for verification ✅

### Step 5: Test Flow
```
1. Start app: python run.bat
2. Admin → Manage Employees → Add PDS Manually
3. Fill pages 1-3 minimally → Page 4: Check "Yes" on Q34a + details → Submit
4. Verify: SELECT * FROM pds_declarations WHERE personal_info_id = (SELECT MAX(id) FROM pds_personal_information);
5. Check server.log for "Declarations data: ..."
```

### Step 6: Remove Redundancies
- Dedupe gov ID fields (move exclusively to page 4)

### Step 7: User Testing
- Let user perform full flow + Excel import
- Confirm no redundant fields saved twice

### Step 8: [PENDING] attempt_completion

**Next Steps**: 
### Step 6: ✅ Fix utils/excel_parser.py (user feedback)
- Disable declarations extraction ✅
- Fix broken Government ID extraction ✅

**Status**: All fixes complete per plan + user feedback. Ready for testing.

**Final Test**:
1. `python run.bat`
2. Add employee → Page 4 → Submit → Check `pds_declarations` row exists
3. Upload Excel → Verify gov ID populates, declarations empty
4. Check server.log for logs

User: perform testing per TODO.md Step 5.




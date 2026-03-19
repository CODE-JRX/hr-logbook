# Excel PDS Upload Fix Plan
Current Working Directory: c:/Users/ASUS-X/Desktop/ELOGBOOK/hr-logbook

## Status: ✅ Plan Created | ⏳ Implementation Pending

### Step 1: Check/Install Dependencies ✓
- openpyxl added to requirements.txt
- Install: `conda activate tf && pip install -r requirements.txt`

- Read requirements.txt to confirm openpyxl.
- If missing, add 'openpyxl>=3.0.0'.
- Install: `conda activate tf && pip install -r requirements.txt`

### Step 2: Verify Blueprint Registration [PENDING]
- Read app.py to confirm `app.register_blueprint(employee_bp, url_prefix='/')` or similar.
- Add if missing.

### Step 3: Enhance Route Error Handling ✓
- Added traceback logging
- Data validation after parse
- User-friendly errors
- Edit routes/employee_routes.py:
  - Import traceback.
  - Catch ValueError/openpyxl exceptions specifically.
  - Log full tb: logger.error(traceback.format_exc()).
  - Validate parsed_data non-empty → error if {} or missing keys.

### Step 4: Improve Excel Parser Robustness ✓
- Added logging for sheets
- Fallback sheets if no C1
- Validate surname before return
- Syntax fix applied
- Edit utils/excel_parser.py:
  - In parse_pds_excel: Print/log wb.sheetnames for debug.
  - Fallback if no C1: Try first sheet or detect by content (surname in row7 col4).
  - After parsing, check if personal_info['surname'] etc. → raise if empty.
  - Add optional debug param.

### Step 5: Frontend UX Polish [PENDING]
- Edit templates/admin/admin_manage_employees.html:
  - Add loading spinner disable.
  - Sample Excel link if available.
  - Better error modals vs alerts.

### Step 6: Testing [PENDING]
- Test upload with valid PDS Excel.
- Check server.log.
- Manual verify session prefill in PDS pages.

### Step 7: Completion [PENDING]
- attempt_completion.

**Next: Test (Steps 5-7)** 
- conda activate tf && pip install -r requirements.txt
- Restart app (run.bat or python app.py)
- Upload PDS Excel, check browser/server.log
- Verify prefill in PDS pages

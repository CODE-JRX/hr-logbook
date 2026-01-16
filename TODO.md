# TODO: Modify Employee Data Page

## Tasks
- [x] Update `models/employee_model.py` to modify `get_all_employees` to accept `search` and `limit` parameters for filtering and limiting results.
- [x] Update `routes/all_routes.py` to handle query parameters `search` and `limit` in the `employee_data` route, pass them to `get_all_employees`, and render the template with filtered employees.
- [x] Update `templates/employees/employee_data.html` to add a search input field, a dropdown for row limits (25, 50, 100, all), and ensure the table displays only the limited and filtered rows.
- [x] Test the changes to ensure search filters by employee_id or full_name, and limit dropdown works correctly.

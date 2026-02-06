# TODO: Implement AJAX Search for Client List

## Tasks
- [x] Add new AJAX route `/clients_ajax` in `routes/all_routes.py` to return filtered client table rows as HTML
- [x] Modify `templates/clients/client_data.html` to use AJAX for search and limit changes instead of form submission
- [x] Add jQuery script to handle input changes and AJAX requests
- [x] Test the AJAX functionality

## Information Gathered
- Current search uses GET form submission, reloading the page
- Backend has `get_clients_filtered(search, limit)` function in `models/client_model.py`
- jQuery is available via `scripts/jquery.js`
- Template renders table with client data

## Plan
1. Create AJAX endpoint that renders partial HTML for table rows
2. Update template to prevent form submission and add AJAX handlers
3. Use jQuery to send requests on search input and limit change
4. Update table body with response HTML

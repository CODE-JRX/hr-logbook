import re

row = {
    'school_name': 'Ateneo',
    'from_year': '2010',
    'to_year': '2014',
    'year_graduated': '2014'
}

for yr_field in ('from_year', 'to_year', 'year_graduated'):
    if yr_field in row and isinstance(row[yr_field], str):
        m = re.search(r'(\d{4})', row[yr_field])
        row[yr_field] = m.group(1) if m else None

print(row)

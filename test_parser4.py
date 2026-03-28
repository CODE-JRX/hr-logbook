import openpyxl, os, sys, json
# add local path to import excel_parser
sys.path.append(os.getcwd())
import utils.excel_parser as ep

files = [os.path.join('static/uploads/temp_pds', f) for f in os.listdir('static/uploads/temp_pds') if f.endswith('.xlsx')]
latest_file = max(files, key=os.path.getmtime)

with open(latest_file, 'rb') as f:
    data = ep.parse_pds_excel(f.read())

with open('parser_dump.json', 'w', encoding='utf-8') as f:
    json.dump({
        'references': data.get('references'),
        'government_id': data.get('government_id'),
        'declarations': data.get('declarations')
    }, f, indent=2)

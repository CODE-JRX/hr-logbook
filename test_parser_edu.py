import openpyxl, os, sys, json
sys.path.append(os.getcwd())
import utils.excel_parser as ep

files = [os.path.join('static/uploads/temp_pds', f) for f in os.listdir('static/uploads/temp_pds') if f.endswith('.xlsx')]
latest_file = max(files, key=os.path.getmtime)

with open(latest_file, 'rb') as f:
    data = ep.parse_pds_excel(f.read())

with open('edu_out.json', 'w', encoding='utf-8') as f:
    json.dump(data.get('educational_background'), f, indent=2)

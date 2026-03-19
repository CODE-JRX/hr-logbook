import openpyxl
import re
from datetime import datetime
import io

def is_junk(val):
    if not isinstance(val, str):
        return False
    s = re.sub(r'\s+', ' ', val.strip().upper())
    junk_list = [
        "CONTINUE ON SEPARATE", "SIGNATURE", "WORK EXPERIENCE",
        "LEARNING AND DEVELOPMENT", "OTHER INFORMATION", "DATE OF BIRTH",
        "INCLUSIVE DATES", "DEPARTMENT / AGENCY", "STATUS OF APPOINTMENT", "GOV'T SERVICE",
        "NAME OF CHILDREN", "WRITE FULL", "TYPE OF LD", "MANAGERIAL", "SUPERVISORY",
        "BASIC EDUCATION", "HIGHEST LEVEL", "SCHOLARSHIP", "INCLUDE PRIVATE EMPLOYMENT",
        "START FROM YOUR RECENT", "DESCRIPTION OF DUTIES", "WRITE IN FULL", "DO NOT ABBREVIATE",
        "MEMBERSHIP IN ASSOCIATION", "CS FORM"
    ]
    if re.match(r'^\d{2}\.$', s):
        return True
    if s in ["DATE", "FROM", "TO"]:
        return True
    return any(j in s for j in junk_list)

def get_val(sheet, row, col_idx):
    if not sheet:
        return ""
    if row > sheet.max_row or col_idx > sheet.max_column:
        return ""
    val = sheet.cell(row=row, column=col_idx).value
    if val is None:
        return ""
    if isinstance(val, str):
        val = val.strip()
    if val == "N/A" or val == "":
        return ""
    return val

def parse_date(val):
    if not val or val == "N/A":
        return ""
    if isinstance(val, datetime):
        return val.strftime('%Y-%m-%d')
    # sometimes it's string, sometimes numbers representing serial date
    if isinstance(val, (int, float)):
        # openpyxl handles dates automatically in most cases and returns datetime objects
        # if it's a number and not parsed as date, we might need to convert it (epoch)
        pass
    if isinstance(val, str):
        # Could be '12/12/1990' or similar
        return val
    return str(val)

def find_row(sheet, start_row, end_row, regex_str, col_idx):
    for r in range(start_row, end_row + 1):
        val = get_val(sheet, r, col_idx)
        if isinstance(val, str) and re.search(regex_str, val, re.IGNORECASE):
            return r
    return -1

def parse_table(sheet, start_row, end_row, mappings, required_keys=None):
    if not sheet:
        return []
    result = []
    for r in range(start_row, end_row + 1):
        has_data = False
        obj = {}
        for key, config in mappings.items():
            col = config if isinstance(config, int) else config['col']
            transform = None if isinstance(config, int) else config.get('transform')
            
            val = get_val(sheet, r, col)
            if transform and val:
                val = transform(val)
            
            obj[key] = val
            if val and val != "N/A":
                has_data = True
                
        if has_data:
            # check junk
            if any(is_junk(v) for v in obj.values() if isinstance(v, str)):
                continue
                
            if required_keys:
                if isinstance(required_keys, str):
                    required_keys = [required_keys]
                has_required = any(obj.get(k) and obj.get(k) != "N/A" and obj.get(k) != "" for k in required_keys)
                if not has_required:
                    continue
            
            is_just_na = all(v == "N/A" or v == "" for v in obj.values())
            if not is_just_na:
                result.append(obj)
    return result

def parse_list(sheet, start_row, end_row, col_idx):
    if not sheet:
        return []
    res = []
    for r in range(start_row, end_row + 1):
        val = get_val(sheet, r, col_idx)
        if val and val != "N/A" and not is_junk(val):
            res.append(val)
    return res

def parse_pds_excel(file_content):
    wb = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)
    def find_sheet(names, target):
        # looks for 'C1', 'C1 (2)', 'Sheet1', 'Page 1', etc.
        pattern = re.compile(rf'.*{re.escape(target)}.*', re.IGNORECASE)
        for n in names:
            if pattern.search(n): return wb[n]
        # try simple number? 
        if target.startswith('C'):
            num = target[1:]
            for n in names:
                if num in n: return wb[n]
        return None

    c1 = find_sheet(wb.sheetnames, 'C1')
    c2 = find_sheet(wb.sheetnames, 'C2')
    c3 = find_sheet(wb.sheetnames, 'C3')
    c4 = find_sheet(wb.sheetnames, 'C4')

    if not c1:
        raise ValueError("Could not find Sheet 'C1' or equivalent in the uploaded file.")
    
    # helper mapping columns (A=1, B=2, C=3, D=4, E=5, F=6, G=7, H=8, I=9, J=10, K=11, L=12, M=13, N=14, O=15)
    
    spouse_idx = find_row(c1, 28, 35, r'SPOUSE', 1)  # Assumes label in A or B. Let's check col 1
    # Often labels span columns. Col 1 (A) or 2 (B)?
    # React code '__EMPTY_3' usually means 4th column (D=4) because it's 0-indexed object keys. 
    # Let's adjust col indices according to common PDS. 
    # __EMPTY_3 -> D (4)
    # __EMPTY_11 -> L (12)
    # __EMPTY_15 -> P (16)
    
    spouse_idx = find_row(c1, 28, 35, r'SPOUSE', 1) if find_row(c1, 28, 35, r'SPOUSE', 1) != -1 else find_row(c1, 28, 35, r'SPOUSE', 2)
    father_idx = find_row(c1, 35, 45, r"FATHER'S", 1) if find_row(c1, 35, 45, r"FATHER'S", 1) != -1 else find_row(c1, 35, 45, r"FATHER'S", 2)
    mother_idx = find_row(c1, 38, 55, r"MOTHER'S", 1) if find_row(c1, 38, 55, r"MOTHER'S", 1) != -1 else find_row(c1, 38, 55, r"MOTHER'S", 2)
    
    work_exp_label = find_row(c2, 5, 20, r'WORK EXPERIENCE', 1)
    if work_exp_label == -1: work_exp_label = find_row(c2, 5, 20, r'WORK EXPERIENCE', 2)
    
    civil_end_row = work_exp_label - 1 if work_exp_label > -1 else 8
    work_exp_start_row = work_exp_label + 1 if work_exp_label > -1 else 9
    
    training_label = find_row(c3, 5, 15, r'LEARNING AND DEVELOPMENT', 1)
    if training_label == -1: training_label = find_row(c3, 5, 15, r'LEARNING AND DEVELOPMENT', 2)
    
    other_info_label = find_row(c3, 15, 25, r'OTHER INFORMATION', 1)
    if other_info_label == -1: other_info_label = find_row(c3, 15, 25, r'OTHER INFORMATION', 2)
    
    vol_end_row = training_label - 1 if training_label > -1 else 8
    train_start_row = training_label + 1 if training_label > -1 else 9
    train_end_row = other_info_label - 1 if other_info_label > -1 else 20
    other_info_start = other_info_label + 1 if other_info_label > -1 else 21
    
    data = {
        'personal_info': {
            'surname': get_val(c1, 7, 4),           # __EMPTY_3 is col D (4) after row 6 (0-indexed -> 7 in excel)
            'first_name': get_val(c1, 8, 4),
            'middle_name': get_val(c1, 9, 4),
            'name_extension': re.sub(r'(?i)NAME EXTENSION.*', '', get_val(c1, 8, 12)).strip(),
            'date_of_birth': parse_date(get_val(c1, 10, 4)),
            'place_of_birth': get_val(c1, 11, 4),
            'civil_status': get_val(c1, 8, 16) or get_val(c1, 9, 16) or get_val(c1, 10, 16),
            'height': get_val(c1, 18, 4),
            'weight': get_val(c1, 20, 4),
            'blood_type': get_val(c1, 21, 4),
            'gsis_no': get_val(c1, 23, 4),
            'pagibig_no': get_val(c1, 25, 4),
            'philhealth_no': get_val(c1, 27, 4),
            'sss_no': get_val(c1, 28, 4),
            'tin_no': get_val(c1, 29, 4),
            'agency_employee_no': get_val(c1, 30, 4),
            'mobile_no': get_val(c1, 29, 9),      # __EMPTY_8 is I (9)
            'email_address': get_val(c1, 30, 9),
            'residential_address': {
                'house_no': get_val(c1, 18, 6),   # __EMPTY_5 is F (6)
                'street': get_val(c1, 18, 7),     # __EMPTY_6 is G (7)
                'barangay': get_val(c1, 18, 8),   # __EMPTY_7 is H (8)
                'city': get_val(c1, 18, 9),       # __EMPTY_8 is I (9)
                'province': get_val(c1, 18, 10),  # __EMPTY_9 is J (10)
                'zip_code': get_val(c1, 18, 11)   # __EMPTY_10 is K (11)
            },
            'permanent_address': {
                'house_no': get_val(c1, 19, 6),
                'street': get_val(c1, 19, 7),
                'barangay': get_val(c1, 19, 8),
                'city': get_val(c1, 19, 9),
                'province': get_val(c1, 19, 10),
                'zip_code': get_val(c1, 19, 11)
            }
        },
        'family_background': {
            'spouse': {
                'surname': get_val(c1, spouse_idx + 1, 4) if spouse_idx > -1 else "",
                'first_name': get_val(c1, spouse_idx + 2, 4) if spouse_idx > -1 else "",
                'middle_name': get_val(c1, spouse_idx + 3, 4) if spouse_idx > -1 else "",
                'occupation': get_val(c1, spouse_idx + 4, 4) if spouse_idx > -1 else "",
                'employer_name': get_val(c1, spouse_idx + 5, 4) if spouse_idx > -1 else "",
                'business_address': get_val(c1, spouse_idx + 6, 4) if spouse_idx > -1 else "",
                'telephone_no': get_val(c1, spouse_idx + 7, 4) if spouse_idx > -1 else ""
            },
            'father': {
                'surname': get_val(c1, father_idx + 1, 4) if father_idx > -1 else "",
                'first_name': get_val(c1, father_idx + 2, 4) if father_idx > -1 else "",
                'middle_name': get_val(c1, father_idx + 3, 4) if father_idx > -1 else ""
            },
            'mother': {
                'maiden_surname': get_val(c1, mother_idx + 1, 4) if mother_idx > -1 else "",
                'first_name': get_val(c1, mother_idx + 2, 4) if mother_idx > -1 else "",
                'middle_name': get_val(c1, mother_idx + 3, 4) if mother_idx > -1 else ""
            },
            'children': parse_table(c1, 32, 47, {
                'name': 9, # __EMPTY_8 -> I
                'date_of_birth': {'col': 13, 'transform': parse_date} # __EMPTY_12 -> M
            }, ['name'])
        },
        'educational_background': parse_table(c1, mother_idx + 4 if mother_idx > -1 else 49, 61, {
            'level': {'col': 2, 'transform': lambda v: str(v).split('/')[0].strip()}, # __EMPTY_1 -> B
            'school_name': 4, # __EMPTY_3 -> D
            'degree': 7, # __EMPTY_6 -> G
            'from': 10, # __EMPTY_9 -> J
            'to': 11, # __EMPTY_10 -> K
            'highest_level': 12, # __EMPTY_11 -> L
            'year_graduated': 13, # __EMPTY_12 -> M
            'scholarships': 14 # __EMPTY_13 -> N
        }, ['school_name', 'degree']),
        
        'civil_service_eligibility': parse_table(c2, 4, civil_end_row + 1, {
            'eligibility': 1, # __EMPTY -> A
            'rating': 6, # __EMPTY_5 -> F
            'exam_date': {'col': 7, 'transform': parse_date}, # __EMPTY_6 -> G
            'exam_place': 9, # __EMPTY_8 -> I
            'license_number': 12, # __EMPTY_11 -> L
            'license_date': {'col': 13, 'transform': parse_date} # __EMPTY_12 -> M
        }, ['eligibility', 'license_number']),
        
        'work_experience': parse_table(c2, work_exp_start_row + 1, 46, {
            'from': {'col': 1, 'transform': parse_date}, # __EMPTY -> A
            'to': {'col': 3, 'transform': parse_date}, # __EMPTY_2 -> C
            'position': 4, # __EMPTY_3 -> D
            'department': 7, # __EMPTY_6 -> G
            'salary': 10, # __EMPTY_9 -> J
            'pay_grade': 11, # __EMPTY_10 -> K
            'appointment_status': 12, # __EMPTY_11 -> L
            'govt_service': 13 # __EMPTY_12 -> M
        }, ['position', 'department']),
        
        'voluntary_work': parse_table(c3, 4, vol_end_row + 1, {
            'organization': 1, # __EMPTY -> A
            'from': {'col': 5, 'transform': parse_date}, # __EMPTY_4 -> E
            'to': {'col': 6, 'transform': parse_date}, # __EMPTY_5 -> F
            'hours': 7, # __EMPTY_6 -> G
            'position': 8, # __EMPTY_7 -> H
        }, ['organization']),
        
        'training_programs': parse_table(c3, train_start_row + 1, train_end_row + 1, {
            'title': 1, # __EMPTY -> A
            'from': {'col': 5, 'transform': parse_date}, # __EMPTY_4 -> E
            'to': {'col': 6, 'transform': parse_date}, # __EMPTY_5 -> F
            'hours': 7, # __EMPTY_6 -> G
            'type': 8, # __EMPTY_7 -> H
            'conducted_by': 9 # __EMPTY_8 -> I
        }, ['title']),
        
        'other_information': {
            'skills': parse_list(c3, other_info_start + 1, 36, 1), # __EMPTY -> A
            'distinctions': parse_list(c3, other_info_start + 1, 36, 3), # __EMPTY_2 -> C
            'memberships': parse_list(c3, other_info_start + 1, 36, 10) if parse_list(c3, other_info_start + 1, 36, 10) else parse_list(c3, other_info_start + 1, 36, 9)
        }
    }
    return data

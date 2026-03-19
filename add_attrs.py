import os
from bs4 import BeautifulSoup
import re

html_dir = r"c:\Users\ASUS-X\Desktop\ELOGBOOK\hr-logbook\templates\employees"
files = ["pds-p1.html", "pds-p2.html", "pds-p3.html", "pds-p4.html"]

def clean_label(text):
    text = text.lower()
    text = re.sub(r'[\d\.]+', '', text) # remove numbers
    text = re.sub(r'\(.*?\)', '', text) # remove paren contents
    text = re.sub(r'[^a-z0-9]', '_', text)
    text = re.sub(r'_+', '_', text)
    text = text.strip('_')
    return text

for fname in files:
    path = os.path.join(html_dir, fname)
    if not os.path.exists(path): continue
    
    with open(path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    # Wrap with form if not present
    container = soup.find('div', class_='form-container')
    if container and not container.find('form'):
        form = soup.new_tag('form', method='POST')
        
        # Determine next action
        if 'p1' in fname:
            form['action'] = '/employee/pds/2'
        elif 'p2' in fname:
            form['action'] = '/employee/pds/3'
        elif 'p3' in fname:
            form['action'] = '/employee/pds/4'
        else:
            form['action'] = '/employee/pds/submit'
            
        # Move container contents into form
        for child in list(container.children):
            form.append(child)
        container.append(form)
        
        # Change the button type to submit
        btn = form.find('button', class_='print-style')
        if btn:
            btn['type'] = 'submit'
            btn['onclick'] = '' # remove alert
            btn.string = 'Next Step' if 'p4' not in fname else 'Submit PDS'
    
    # Add names to inputs
    for group in soup.find_all('div', class_='field-group'):
        label = group.find('label')
        if not label: continue
        name_val = clean_label(label.get_text())
        if not name_val: continue
        
        for input_tag in group.find_all(['input', 'select', 'textarea']):
            if not input_tag.has_attr('name'):
                input_tag['name'] = name_val
                
    with open(path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
        
print("Modified files successfully.")

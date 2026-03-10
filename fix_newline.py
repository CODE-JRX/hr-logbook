
import os

filepath = r'c:\Users\JRX\Desktop\LogBook-System\hr-logbook\templates\base.html'

with open(filepath, 'rb') as f:
    content = f.read()

# Replace the broken join with a correct one
# We look for the byte sequence of the newline inside the join
old = b"allMessages.join('\n');" # Wait, if it's an actual newline it would be b"join('\r\n');" or similar
# Based on view_file, it was join(' and then newline and then ');

# Let's try to be more robust
content_str = content.decode('utf-8', errors='ignore')
new_content = content_str.replace("allMessages.join('\n');", "allMessages.join('\\n');")

# If that didn't work, maybe it was an actual newline
if new_content == content_str:
    new_content = content_str.replace("allMessages.join('\r\n');", "allMessages.join('\\n');")
if new_content == content_str:
    new_content = content_str.replace("allMessages.join('\n');", "allMessages.join('\\n');")

# Actually, and probably most reliably:
import re
new_content = re.sub(r"allMessages\.join\('\s+'\);", r"allMessages.join('\\n');", content_str, flags=re.MULTILINE)

# Let's try a very direct replace based on what I see
new_content = content_str.replace("allMessages.join('\n');", "allMessages.join('\\n');")
# Wait, if view_file shows line 746 as ending in ', the newline is at the end of the line.

# TRY THIS:
lines = content_str.splitlines()
for i, line in enumerate(lines):
    if "allMessages.join('" in line and i + 1 < len(lines) and "');" in lines[i+1]:
        print(f"Found at line {i+1}")
        lines[i] = line.replace("join('", "join('\\n');")
        lines[i+1] = "" # Clear the next line
        break

new_content = "\n".join(l for l in lines if l.strip() or l == "") # Keep empty lines but remove the one we cleared

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)
print("SUCCESS")

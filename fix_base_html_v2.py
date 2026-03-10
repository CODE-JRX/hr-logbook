
import os

filepath = r'c:\Users\JRX\Desktop\LogBook-System\hr-logbook\templates\base.html'

with open(filepath, 'rb') as f:
    content = f.read().decode('utf-8', errors='ignore')

# Use a very broad regex to find the flash message block
import re

# Match from "Unified Flash Message Handling" to the next "});"
# capturing the block
pattern = r'(// Unified Flash Message Handling via Modal\s*\{% with messages = get_flashed_messages\(\) %\}\s*\{% if messages %\}.*?\{% endwith %\}\s*\}\);)'
replacement = """// Unified Flash Message Handling via Modal
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          const successModalEl = document.getElementById('successModal');
          const successMsgEl = document.getElementById('successMessage');
          if (successModalEl && successMsgEl) {
            const allMessages = {{ messages | tojson }};
            successMsgEl.textContent = allMessages.join('\\n');
            const successModal = new bootstrap.Modal(successModalEl);
            successModal.show();
          }
        {% endif %}
      {% endwith %}
    });"""

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

if new_content != content:
    with open(filepath, 'wb') as f:
        f.write(new_content.encode('utf-8'))
    print("SUCCESS: File updated with regex.")
else:
    print("FAILURE: Regex did not match.")
    # Debug: print what it DID find
    match = re.search(r'// Unified Flash Message Handling via Modal.*', content, flags=re.DOTALL)
    if match:
        print("FOUND START OF BLOCK:")
        print(match.group(0)[:300])


import os
import re

filepath = r'c:\Users\JRX\Desktop\LogBook-System\hr-logbook\templates\base.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# We look for the script block and replace it completely
# This regex is very broad to catch any variation of the broken state
pattern = r'// Unified Flash Message Handling via Modal.*?{% endwith %}\s*\}\);'
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

if new_content == content:
    print("Pattern not found with dotall, trying simpler pattern")
    pattern2 = r'// Unified Flash Message Handling via Modal.*'
    # Find the line number or just replace everything from there to the end of script
    match = re.search(pattern2, content, flags=re.DOTALL)
    if match:
        # Assuming the rest of the file is just closing tags
        rest_of_file = match.group(0)
        # Find where the script ends
        end_idx = rest_of_file.find("</script>")
        if end_idx != -1:
             block_to_replace = rest_of_file[:end_idx].strip()
             new_content = content.replace(block_to_replace, replacement)

if new_content != content:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("SUCCESS")
else:
    print("FAILED to replace")

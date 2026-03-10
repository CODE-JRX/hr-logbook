
import os

filepath = r'c:\Users\JRX\Desktop\LogBook-System\hr-logbook\templates\base.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

broken_block = """      // Unified Flash Message Handling via Modal
      {% with messages = get_flashed_messages() %}
      {% if messages %}
      const successModalEl = document.getElementById('successModal');
      const successMsgEl = document.getElementById('successMessage');
      if (successModalEl && successMsgEl) {
        const allMessages = {{ messages | tojson
      }
    };
    successMsgEl.textContent = allMessages.join('\n');
    const successModal = new bootstrap.Modal(successModalEl);
    successModal.show();
          }
    {% endif %}
    {% endwith %}"""

fixed_block = """      // Unified Flash Message Handling via Modal
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
      {% endwith %}"""

# We need to be careful with exact whitespace. Let's try to find it more robustly.
import re

# Match the broken block even if spaces vary slightly
# We escape special characters for regex
pattern = re.escape(broken_block).replace(r'\ ', r'\s*').replace(r'\n', r'\s*\n\s*')
new_content = re.sub(pattern, fixed_block, content)

if new_content == content:
    print("Failed to match with robust regex, trying exact match...")
    if broken_block in content:
        new_content = content.replace(broken_block, fixed_block)
        print("Exact match succeeded.")
    else:
        print("Exact match failed too. Printing snippet of content for debugging:")
        idx = content.find("Unified Flash Message Handling")
        if idx != -1:
            print(content[idx:idx+500])
        else:
            print("String not found at all")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)
print("File update attempted.")


import re
import os

target_file = "web/pages/02__Upload_Image.py"

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

# Replace triple double quotes with a placeholder or comments
# Helper to replace with comments
def replace_docstring(match):
    text = match.group(1)
    lines = text.split('\n')
    return '\n'.join([f'# {line.strip()}' for line in lines])

# Regex for triple " strings
# We use DOTALL to match newlines
# This is a naive regex but sufficient for docstrings which are usually well-formed locally
# We capture the content inside
pattern = r'"""(.*?)"""'

# Apply replacement
new_content = re.sub(pattern, replace_docstring, content, flags=re.DOTALL)

# Also check for triple ' strings just in case
pattern_single = r"'''(.*?)'''"
new_content = re.sub(pattern_single, replace_docstring, new_content, flags=re.DOTALL)

with open(target_file, "w", encoding="utf-8") as f:
    f.write(new_content)

print(f"Processed {target_file}")

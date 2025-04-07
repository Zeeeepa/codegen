#!/usr/bin/env python3

with open('projector/backend/code_suggestions.py', 'r') as f:
    content = f.read()

# Replace the problematic pattern with a simpler one that works correctly
old_pattern = r'"pattern": r"def\\s+(\\w+)\\([^)]*\\):\\s*(?!\\s*(?:\\\"\\\"\\\"|\\\'\\\'\\\'\'))"'
new_pattern = r'"pattern": r"def\\s+(\\w+)\\([^)]*\\):\\s*(?!\\s*(?:\\\"\\\"\\\"|\\\'\\\'\\\'))"'

content = content.replace(old_pattern, new_pattern)

with open('projector/backend/code_suggestions.py', 'w') as f:
    f.write(content)

print("Pattern fixed successfully")

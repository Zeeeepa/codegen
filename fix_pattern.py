with open('projector/backend/code_suggestions.py', 'r') as file:
    content = file.read()

# Replace the pattern with a simpler version that works correctly
content = content.replace(
    '"pattern": r"def\\s+(\\w+)\\([^)]*\\):\\s*(?!\\s*(?:\\\"\\\"\\\"|\\\'\\\'\\\'\'))"',
    '"pattern": r"def\\s+(\\w+)\\([^)]*\\):\\s*(?!\\s*(?:\\\"\\\"\\\"|\\\'\\\'\\\''))"'
)

with open('projector/backend/code_suggestions.py', 'w') as file:
    file.write(content)

print("Pattern fixed successfully")

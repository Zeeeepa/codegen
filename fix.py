import re
import sys

def check_syntax(file_path):
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        compile(content, file_path, 'exec')
        return True
    except SyntaxError as e:
        print(f"Syntax error at line {e.lineno}: {e.msg}")
        return False

def fix_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace problematic line
    content = content.replace("if ('\"\"\"' in line or \"'''\" in line) and not (", 
                             "if ('\"\"\"' in line or '\\'\\'\\'' in line) and not (")
    
    with open(file_path, 'w') as f:
        f.write(content)

file_path = 'codegen-on-oss/codegen_on_oss/analysis/analysis.py'
fix_file(file_path)

if check_syntax(file_path):
    print("Fixed the file successfully!")
else:
    print("Failed to fix the file.")

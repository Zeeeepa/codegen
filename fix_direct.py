import re

def fix_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix the first problematic line
    content = content.replace("if ('\"\"\"' in line or \"'''\" in line) and not (", 
                             "if ('\"\"\"' in line or '\\'\\'\\'' in line) and not (")
    
    # Fix the unterminated triple-quoted string
    if "\"\"\"" in content and content.count("\"\"\"") % 2 == 1:
        content += "\n\"\"\""
    elif "'''" in content and content.count("'''") % 2 == 1:
        content += "\n'''"
    
    with open(file_path, 'w') as f:
        f.write(content)

fix_file('codegen-on-oss/codegen_on_oss/analysis/analysis.py')
print("Fixed the file")

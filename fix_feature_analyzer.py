def fix_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace CodegenFunction with Function
    content = content.replace("function: CodegenFunction", "function: Function")
    
    with open(file_path, 'w') as f:
        f.write(content)

fix_file('codegen-on-oss/codegen_on_oss/analysis/feature_analyzer.py')
print("Fixed feature_analyzer.py")

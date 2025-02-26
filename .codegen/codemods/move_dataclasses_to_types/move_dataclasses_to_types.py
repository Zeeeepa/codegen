import codegen
from codegen.sdk.core.codebase import Codebase
import os


@codegen.function('move-dataclasses-to-types')
def run(codebase: Codebase):
    # Only process files in src/codegen
    src_codegen_prefix = "src/codegen"
    
    # For each file in the codebase
    for file in codebase.files:
        # Skip files that are not in src/codegen
        if not file.filepath.startswith(src_codegen_prefix):
            continue
            
        # For each class in the file
        for cls in file.classes:
            # Check if the class is a dataclass (either @dataclass or @dataclass(...))
            if any(d for d in cls.decorators if "@dataclass" in d.source):
                # Skip if the file is already a types.py file
                if file.name == "types.py":
                    continue
                    
                # Determine the target file path for types.py
                dir_path = os.path.dirname(file.filepath)
                types_filepath = os.path.join(dir_path, "types.py")
                
                # Check if types.py file exists, if not, create it
                if not codebase.has_file(types_filepath):
                    types_file = codebase.create_file(types_filepath, "")
                else:
                    types_file = codebase.get_file(types_filepath)
                
                # Move the dataclass to types.py, add a "back edge" import
                cls.move_to_file(types_file, include_dependencies=True, strategy="add_back_edge")
    
    # Commit changes to persist the file modifications
    codebase.commit()


if __name__ == "__main__":
    print('Parsing codebase...')
    codebase = Codebase("./")

    print('Running function...')
    run(codebase)

import codegen
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.dataclasses.usage import UsageKind
import re


@codegen.function('move-dataclasses-to-types')
def run(codebase: Codebase):
    # Only process files in src/codegen
    src_codegen_prefix = "src/codegen"
    
    # Track which directories already have types.py files
    processed_dirs = set()
    
    # First pass: identify all dataclasses
    dataclasses_to_move = []
    
    for file in codebase.files:
        # Skip files outside src/codegen
        if not file.filepath.startswith(src_codegen_prefix):
            continue
            
        # Skip existing types.py files
        if file.name == "types.py":
            # Remember this directory already has a types.py
            dir_path = "/".join(file.filepath.split("/")[:-1])
            processed_dirs.add(dir_path)
            continue
            
        # Find all dataclass definitions in the file
        for cls in file.classes:
            # Check if the class is a dataclass by looking for @dataclass decorator
            # This handles both standalone @dataclass and @dataclass() with parameters
            is_dataclass = False
            for decorator in cls.decorators:
                decorator_text = decorator.source.strip()
                if decorator_text == "@dataclass" or decorator_text.startswith("@dataclass("):
                    is_dataclass = True
                    break
                    
            if is_dataclass:
                dataclasses_to_move.append(cls)
    
    # Second pass: move dataclasses to types.py files
    for cls in dataclasses_to_move:
        file = cls.file
        
        # Determine the target directory path
        dir_path = "/".join(file.filepath.split("/")[:-1])
        types_filepath = f"{dir_path}/types.py"
        
        # Check if types.py file exists, if not, create it
        if dir_path not in processed_dirs:
            if not codebase.has_file(types_filepath):
                # Create a new types.py file with appropriate imports
                types_file = codebase.create_file(types_filepath, "")
            else:
                types_file = codebase.get_file(types_filepath)
            processed_dirs.add(dir_path)
        else:
            types_file = codebase.get_file(types_filepath)
        
        # Move the dataclass to types.py, including dependencies and adding back-edge imports
        print(f"Moving {cls.name} from {file.filepath} to {types_filepath}")
        cls.move_to_file(types_file, include_dependencies=True, strategy="add_back_edge")

    # Commit changes to persist the file modifications
    codebase.commit()


if __name__ == "__main__":
    print('Parsing codebase...')
    codebase = Codebase("./")

    print('Running function...')
    run(codebase)

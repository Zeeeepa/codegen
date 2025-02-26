import codegen
from codegen.sdk.core.codebase import Codebase


@codegen.function("remove-dead-code")
def run(codebase: Codebase):
    # Codemod: Remove dead code in the src/codegen directory

    # Iterate through all files in the src/codegen directory
    for file in codebase.files:
        # Only process files in the src/codegen directory
        if not file.filepath.startswith("src/codegen"):
            continue

        # Iterate over all functions in the file
        for function in file.functions:
            # Skip test functions, decorated functions, and those used as endpoints
            if "test" not in function.file.filepath and not function.decorators and not function.usages:
                # If function has no usages or call sites, remove it
                if not function.usages and not function.call_sites:
                    print(f"Removing unused function: {function.name} in {function.file.filepath}")
                    function.remove()

        # Similarly, check and remove unused classes
        for cls in file.classes:
            # Skip classes with no usage, preserving API endpoints
            if not cls.decorators:
                # Check if any method in the class has a decorator containing "route"
                is_endpoint = False
                for method in cls.methods:
                    if method.decorators and any("route" in d.source for d in method.decorators):
                        is_endpoint = True
                        break

                if not cls.usages and not is_endpoint:
                    print(f"Removing unused class: {cls.name} in {cls.file.filepath}")
                    cls.remove()

    # Commit changes to the codebase
    codebase.commit()


if __name__ == "__main__":
    print("Parsing codebase...")
    codebase = Codebase("./")

    print("Running function...")
    run(codebase)

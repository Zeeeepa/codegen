"""
Example script demonstrating the use of the unified analysis module.

This script shows how to use the CodeAnalyzer and CodeMetrics classes
to perform comprehensive code analysis on a repository.
"""

from codegen_on_oss.analysis.analysis import CodeAnalyzer
from codegen_on_oss.metrics import CodeMetrics

from codegen import Codebase


def main():
    """
    Main function demonstrating the use of the analysis module.
    """
    print("Analyzing a sample repository...")

    # Load a codebase
    repo_name = "fastapi/fastapi"
    codebase = Codebase.from_repo(repo_name)

    print(f"Loaded codebase: {repo_name}")
    print(f"Files: {len(codebase.files)}")
    print(f"Functions: {len(codebase.functions)}")
    print(f"Classes: {len(codebase.classes)}")

    # Create analyzer instance
    analyzer = CodeAnalyzer(codebase)

    # Get codebase summary
    print("\n=== Codebase Summary ===")
    print(analyzer.get_codebase_summary())

    # Analyze complexity
    print("\n=== Complexity Analysis ===")
    complexity_results = analyzer.analyze_complexity()
    print(
        f"Average cyclomatic complexity: {complexity_results['cyclomatic_complexity']['average']:.2f}"
    )
    print(f"Complexity rank: {complexity_results['cyclomatic_complexity']['rank']}")

    # Find complex functions
    complex_functions = [
        f
        for f in complexity_results["cyclomatic_complexity"]["functions"]
        if f["complexity"] > 10
    ][
        :5
    ]  # Show top 5

    if complex_functions:
        print("\nTop complex functions:")
        for func in complex_functions:
            print(
                f"- {func['name']}: Complexity {func['complexity']} (Rank {func['rank']})"
            )

    # Analyze imports
    print("\n=== Import Analysis ===")
    import_analysis = analyzer.analyze_imports()
    print(f"Found {len(import_analysis['import_cycles'])} import cycles")

    # Create metrics instance
    metrics = CodeMetrics(codebase)

    # Get code quality summary
    print("\n=== Code Quality Summary ===")
    quality_summary = metrics.get_code_quality_summary()

    print("Overall metrics:")
    for metric, value in quality_summary["overall_metrics"].items():
        if isinstance(value, float):
            print(f"- {metric}: {value:.2f}")
        else:
            print(f"- {metric}: {value}")

    print("\nProblem areas:")
    for area, count in quality_summary["problem_areas"].items():
        print(f"- {area}: {count}")

    # Find bug-prone functions
    print("\n=== Bug-Prone Functions ===")
    bug_prone = metrics.find_bug_prone_functions()[:5]  # Show top 5

    if bug_prone:
        print("Top bug-prone functions:")
        for func in bug_prone:
            print(f"- {func['name']}: Estimated bugs {func['bugs_delivered']:.2f}")

    # Analyze dependencies
    print("\n=== Dependency Analysis ===")
    dependencies = metrics.analyze_dependencies()

    print(
        f"Dependency graph: {dependencies['dependency_graph']['nodes']} nodes, "
        f"{dependencies['dependency_graph']['edges']} edges"
    )
    print(f"Dependency density: {dependencies['dependency_graph']['density']:.4f}")
    print(f"Number of cycles: {dependencies['cycles']}")

    if dependencies["most_central_files"]:
        print("\nMost central files:")
        for file, score in dependencies["most_central_files"][:5]:  # Show top 5
            print(f"- {file}: Centrality {score:.4f}")

    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()


# Tutorial: Comparing Codebases

This tutorial demonstrates how to compare codebases using the Codebase Analysis Viewer.

## Introduction

Comparing codebases is a powerful way to understand how code evolves over time, how different implementations of similar functionality differ, and how refactoring impacts code quality. This tutorial will guide you through comparing codebases in various scenarios, including:

1. Comparing different versions of the same codebase
2. Comparing different branches of a repository
3. Comparing forks with their original repositories
4. Comparing before and after major refactoring
5. Comparing similar projects with different implementations

## Prerequisites

Before starting this tutorial, make sure you have:

1. Installed the Codebase Analysis Viewer
2. Basic familiarity with the command-line interface
3. Access to the repositories you want to compare

## Comparing Different Versions of the Same Codebase

Comparing different versions of the same codebase helps you understand how the code has evolved over time.

### Step 1: Basic Version Comparison

Start with a basic comparison of two versions:

```bash
codegen-on-oss compare --base-repo-url https://github.com/username/repo --base-branch v1.0 --compare-branch v2.0
```

### Step 2: Focus on Specific Categories

Compare specific aspects of the codebase:

```bash
codegen-on-oss compare --base-repo-url https://github.com/username/repo --base-branch v1.0 --compare-branch v2.0 --categories codebase_structure code_quality
```

### Step 3: Analyze Code Quality Changes

Focus on how code quality has changed between versions:

```bash
# Using the CLI
codegen-on-oss compare --base-repo-url https://github.com/username/repo --base-branch v1.0 --compare-branch v2.0 --categories code_quality

# Using the Python API
from codebase_comparator import CodebaseComparator

comparator = CodebaseComparator(
    base_repo_url="https://github.com/username/repo",
    base_branch="v1.0",
    compare_branch="v2.0"
)
quality_diff = comparator.compare(categories=["code_quality"])
print(f"Cyclomatic complexity change: {quality_diff['categories']['code_quality']['cyclomatic_complexity']['avg_complexity']['difference']}")
```

### Step 4: Visualize Changes

Generate a visual report of the changes:

```bash
codegen-on-oss compare --base-repo-url https://github.com/username/repo --base-branch v1.0 --compare-branch v2.0 --output-format html --output-file version_comparison.html
```

## Comparing Different Branches of a Repository

Comparing different branches helps you understand how feature development or bug fixes impact the codebase.

### Step 1: Basic Branch Comparison

Start with a basic comparison of two branches:

```bash
codegen-on-oss compare --base-repo-url https://github.com/username/repo --base-branch main --compare-branch feature-branch
```

### Step 2: Focus on New Features

Compare branches to identify new features or components:

```bash
# Using the CLI
codegen-on-oss compare --base-repo-url https://github.com/username/repo --base-branch main --compare-branch feature-branch

# Using the Python API
from codebase_comparator import CodebaseComparator

comparator = CodebaseComparator(
    base_repo_url="https://github.com/username/repo",
    base_branch="main",
    compare_branch="feature-branch"
)
results = comparator.compare()

# Check for new files
file_count_diff = results["categories"]["codebase_structure"]["file_count"]
if file_count_diff["difference"] > 0:
    print(f"Feature branch added {file_count_diff['difference']} new files")

# Check for new functions
new_functions = results["categories"]["symbol_level"]["new_functions"]
print(f"Feature branch added {len(new_functions)} new functions:")
for func in new_functions:
    print(f"  {func['name']} in {func['file']}")
```

### Step 3: Analyze Impact on Complexity

Analyze how the feature branch impacts code complexity:

```bash
# Using the CLI
codegen-on-oss compare --base-repo-url https://github.com/username/repo --base-branch main --compare-branch feature-branch --categories code_quality

# Using the Python API
from codebase_comparator import CodebaseComparator

comparator = CodebaseComparator(
    base_repo_url="https://github.com/username/repo",
    base_branch="main",
    compare_branch="feature-branch"
)
quality_diff = comparator.compare(categories=["code_quality"])
complexity_diff = quality_diff["categories"]["code_quality"]["cyclomatic_complexity"]["avg_complexity"]
if complexity_diff["difference"] > 0:
    print(f"Warning: Feature branch increases average complexity by {complexity_diff['difference']} ({complexity_diff['percent_change']}%)")
else:
    print(f"Good: Feature branch decreases average complexity by {abs(complexity_diff['difference'])} ({abs(complexity_diff['percent_change'])}%)")
```

### Step 4: Check for Potential Merge Issues

Analyze potential issues before merging:

```python
from codebase_comparator import CodebaseComparator

comparator = CodebaseComparator(
    base_repo_url="https://github.com/username/repo",
    base_branch="main",
    compare_branch="feature-branch"
)
results = comparator.compare()

# Check for modified files with high complexity
modified_files = results["categories"]["codebase_structure"]["modified_files"]
high_complexity_files = []
for file in modified_files:
    if file["complexity_change"] > 5:
        high_complexity_files.append(file)

if high_complexity_files:
    print("Warning: The following modified files have significant complexity increases:")
    for file in high_complexity_files:
        print(f"  {file['name']}: +{file['complexity_change']}")
```

## Comparing Forks with Their Original Repositories

Comparing forks with their original repositories helps you understand how the fork has diverged.

### Step 1: Basic Fork Comparison

Start with a basic comparison of a fork with its original repository:

```bash
codegen-on-oss compare --base-repo-url https://github.com/original/repo --compare-repo-url https://github.com/fork/repo
```

### Step 2: Identify Major Differences

Identify the major differences between the fork and the original:

```bash
# Using the CLI
codegen-on-oss compare --base-repo-url https://github.com/original/repo --compare-repo-url https://github.com/fork/repo

# Using the Python API
from codebase_comparator import CodebaseComparator

comparator = CodebaseComparator(
    base_repo_url="https://github.com/original/repo",
    compare_repo_url="https://github.com/fork/repo"
)
results = comparator.compare()

# Check for new files
new_files = results["categories"]["codebase_structure"]["new_files"]
print(f"Fork added {len(new_files)} new files")

# Check for removed files
removed_files = results["categories"]["codebase_structure"]["removed_files"]
print(f"Fork removed {len(removed_files)} files")

# Check for modified files
modified_files = results["categories"]["codebase_structure"]["modified_files"]
print(f"Fork modified {len(modified_files)} files")
```

### Step 3: Analyze Feature Additions

Analyze features added in the fork:

```python
from codebase_comparator import CodebaseComparator

comparator = CodebaseComparator(
    base_repo_url="https://github.com/original/repo",
    compare_repo_url="https://github.com/fork/repo"
)
results = comparator.compare()

# Check for new functions
new_functions = results["categories"]["symbol_level"]["new_functions"]
print(f"Fork added {len(new_functions)} new functions")

# Check for new classes
new_classes = results["categories"]["symbol_level"]["new_classes"]
print(f"Fork added {len(new_classes)} new classes")

# Check for new modules
new_modules = results["categories"]["codebase_structure"]["new_modules"]
print(f"Fork added {len(new_modules)} new modules")
```

### Step 4: Evaluate Potential for Upstream Contributions

Evaluate which changes might be good candidates for upstream contributions:

```python
from codebase_comparator import CodebaseComparator

comparator = CodebaseComparator(
    base_repo_url="https://github.com/original/repo",
    compare_repo_url="https://github.com/fork/repo"
)
results = comparator.compare()

# Look for bug fixes (modified functions with improved complexity)
bug_fix_candidates = []
for func in results["categories"]["symbol_level"]["modified_functions"]:
    if func["complexity_change"] < 0 and func["line_count_change"] < 10:
        bug_fix_candidates.append(func)

print(f"Potential bug fixes for upstream contribution: {len(bug_fix_candidates)}")
for func in bug_fix_candidates:
    print(f"  {func['name']} in {func['file']}")

# Look for new features that don't modify core functionality
feature_candidates = []
for func in results["categories"]["symbol_level"]["new_functions"]:
    if not any(core_file in func["file"] for core_file in ["core", "main", "base"]):
        feature_candidates.append(func)

print(f"Potential new features for upstream contribution: {len(feature_candidates)}")
for func in feature_candidates[:5]:  # Show top 5
    print(f"  {func['name']} in {func['file']}")
```

## Comparing Before and After Major Refactoring

Comparing before and after a major refactoring helps you assess the impact of the refactoring.

### Step 1: Basic Refactoring Comparison

Start with a basic comparison of before and after the refactoring:

```bash
codegen-on-oss compare --base-repo-url https://github.com/username/repo --base-branch before-refactor --compare-branch after-refactor
```

### Step 2: Analyze Code Quality Improvements

Analyze how the refactoring has improved code quality:

```bash
# Using the CLI
codegen-on-oss compare --base-repo-url https://github.com/username/repo --base-branch before-refactor --compare-branch after-refactor --categories code_quality

# Using the Python API
from codebase_comparator import CodebaseComparator

comparator = CodebaseComparator(
    base_repo_url="https://github.com/username/repo",
    base_branch="before-refactor",
    compare_branch="after-refactor"
)
quality_diff = comparator.compare(categories=["code_quality"])

# Check complexity changes
complexity_diff = quality_diff["categories"]["code_quality"]["cyclomatic_complexity"]["avg_complexity"]
print(f"Complexity change: {complexity_diff['difference']} ({complexity_diff['percent_change']}%)")

# Check for removed unused functions
removed_unused = quality_diff["categories"]["code_quality"]["removed_unused_functions"]
print(f"Removed unused functions: {len(removed_unused)}")

# Check for reduced nesting depth
nesting_diff = quality_diff["categories"]["code_quality"]["nesting_depth_analysis"]["avg_max_nesting"]
print(f"Nesting depth change: {nesting_diff['difference']} ({nesting_diff['percent_change']}%)")
```

### Step 3: Analyze Structural Changes

Analyze how the refactoring has changed the structure of the codebase:

```python
from codebase_comparator import CodebaseComparator

comparator = CodebaseComparator(
    base_repo_url="https://github.com/username/repo",
    base_branch="before-refactor",
    compare_branch="after-refactor"
)
structure_diff = comparator.compare(categories=["codebase_structure"])

# Check file count changes
file_count_diff = structure_diff["categories"]["codebase_structure"]["file_count"]
print(f"File count change: {file_count_diff['difference']} ({file_count_diff['percent_change']}%)")

# Check symbol count changes
symbol_count_diff = structure_diff["categories"]["codebase_structure"]["symbol_count"]
print(f"Symbol count change: {symbol_count_diff['difference']} ({symbol_count_diff['percent_change']}%)")

# Check module coupling changes
coupling_diff = structure_diff["categories"]["codebase_structure"]["module_coupling_metrics"]["avg_coupling"]
print(f"Module coupling change: {coupling_diff['difference']} ({coupling_diff['percent_change']}%)")

# Check module cohesion changes
cohesion_diff = structure_diff["categories"]["codebase_structure"]["module_cohesion_analysis"]["avg_cohesion"]
print(f"Module cohesion change: {cohesion_diff['difference']} ({cohesion_diff['percent_change']}%)")
```

### Step 4: Verify Functional Equivalence

Verify that the refactoring hasn't changed the functionality:

```python
from codebase_comparator import CodebaseComparator

comparator = CodebaseComparator(
    base_repo_url="https://github.com/username/repo",
    base_branch="before-refactor",
    compare_branch="after-refactor"
)
results = comparator.compare()

# Check for removed public functions (potential API breakage)
removed_public_functions = []
for func in results["categories"]["symbol_level"]["removed_functions"]:
    if func["visibility"] == "public" and not func["name"].startswith("_"):
        removed_public_functions.append(func)

if removed_public_functions:
    print("Warning: The following public functions were removed:")
    for func in removed_public_functions:
        print(f"  {func['name']} in {func['file']}")
else:
    print("Good: No public functions were removed")

# Check for changed function signatures (potential API breakage)
changed_signatures = []
for func in results["categories"]["symbol_level"]["modified_functions"]:
    if func["signature_changed"] and func["visibility"] == "public" and not func["name"].startswith("_"):
        changed_signatures.append(func)

if changed_signatures:
    print("Warning: The following public functions have changed signatures:")
    for func in changed_signatures:
        print(f"  {func['name']} in {func['file']}")
else:
    print("Good: No public function signatures were changed")
```

## Comparing Similar Projects with Different Implementations

Comparing similar projects with different implementations helps you understand different approaches to solving the same problem.

### Step 1: Basic Project Comparison

Start with a basic comparison of two similar projects:

```bash
codegen-on-oss compare --base-repo-url https://github.com/project1/repo --compare-repo-url https://github.com/project2/repo
```

### Step 2: Compare High-Level Structure

Compare the high-level structure of the projects:

```bash
# Using the CLI
codegen-on-oss compare --base-repo-url https://github.com/project1/repo --compare-repo-url https://github.com/project2/repo --categories codebase_structure

# Using the Python API
from codebase_comparator import CodebaseComparator

comparator = CodebaseComparator(
    base_repo_url="https://github.com/project1/repo",
    compare_repo_url="https://github.com/project2/repo"
)
structure_diff = comparator.compare(categories=["codebase_structure"])

# Compare file counts
file_count_diff = structure_diff["categories"]["codebase_structure"]["file_count"]
print(f"Project 1 has {file_count_diff['base']} files")
print(f"Project 2 has {file_count_diff['compare']} files")
print(f"Difference: {file_count_diff['difference']} ({file_count_diff['percent_change']}%)")

# Compare language distribution
lang_diff = structure_diff["categories"]["codebase_structure"]["files_by_language"]
print("Language distribution:")
for lang, diff in lang_diff.items():
    print(f"  {lang}: {diff['base']} vs {diff['compare']} ({diff['percent_change']}%)")

# Compare directory structure
dir_structure1 = structure_diff["categories"]["codebase_structure"]["directory_structure"]["base"]
dir_structure2 = structure_diff["categories"]["codebase_structure"]["directory_structure"]["compare"]
print(f"Project 1 top-level directories: {', '.join(dir_structure1.keys())}")
print(f"Project 2 top-level directories: {', '.join(dir_structure2.keys())}")
```

### Step 3: Compare Code Quality

Compare the code quality of the projects:

```python
from codebase_comparator import CodebaseComparator

comparator = CodebaseComparator(
    base_repo_url="https://github.com/project1/repo",
    compare_repo_url="https://github.com/project2/repo"
)
quality_diff = comparator.compare(categories=["code_quality"])

# Compare complexity
complexity_diff = quality_diff["categories"]["code_quality"]["cyclomatic_complexity"]["avg_complexity"]
print(f"Project 1 average complexity: {complexity_diff['base']}")
print(f"Project 2 average complexity: {complexity_diff['compare']}")
print(f"Difference: {complexity_diff['difference']} ({complexity_diff['percent_change']}%)")

# Compare maintainability
maintainability_diff = quality_diff["categories"]["code_metrics"]["maintainability_index"]["avg_maintainability"]
print(f"Project 1 maintainability: {maintainability_diff['base']}")
print(f"Project 2 maintainability: {maintainability_diff['compare']}")
print(f"Difference: {maintainability_diff['difference']} ({maintainability_diff['percent_change']}%)")

# Compare documentation
documentation_diff = quality_diff["categories"]["code_quality"]["documentation_completeness"]["coverage_percentage"]
print(f"Project 1 documentation coverage: {documentation_diff['base']}%")
print(f"Project 2 documentation coverage: {documentation_diff['compare']}%")
print(f"Difference: {documentation_diff['difference']}%")
```

### Step 4: Compare Architecture Approaches

Compare the architectural approaches of the projects:

```python
from codebase_comparator import CodebaseComparator

comparator = CodebaseComparator(
    base_repo_url="https://github.com/project1/repo",
    compare_repo_url="https://github.com/project2/repo"
)
results = comparator.compare()

# Compare module coupling
coupling1 = results["categories"]["codebase_structure"]["module_coupling_metrics"]["base"]["avg_coupling"]
coupling2 = results["categories"]["codebase_structure"]["module_coupling_metrics"]["compare"]["avg_coupling"]
print(f"Project 1 average module coupling: {coupling1}")
print(f"Project 2 average module coupling: {coupling2}")

# Compare module cohesion
cohesion1 = results["categories"]["codebase_structure"]["module_cohesion_analysis"]["base"]["avg_cohesion"]
cohesion2 = results["categories"]["codebase_structure"]["module_cohesion_analysis"]["compare"]["avg_cohesion"]
print(f"Project 1 average module cohesion: {cohesion1}")
print(f"Project 2 average module cohesion: {cohesion2}")

# Compare dependency structures
deps1 = results["categories"]["codebase_structure"]["module_dependency_graph"]["base"]
deps2 = results["categories"]["codebase_structure"]["module_dependency_graph"]["compare"]
print(f"Project 1 has {len(deps1['modules'])} modules with {deps1['dependency_count']} dependencies")
print(f"Project 2 has {len(deps2['modules'])} modules with {deps2['dependency_count']} dependencies")

# Compare entry points
entry1 = results["categories"]["dependency_flow"]["entry_point_analysis"]["base"]["entry_points"]
entry2 = results["categories"]["dependency_flow"]["entry_point_analysis"]["compare"]["entry_points"]
print(f"Project 1 has {len(entry1)} entry points")
print(f"Project 2 has {len(entry2)} entry points")
```

## Conclusion

This tutorial has demonstrated how to compare codebases in various scenarios using the Codebase Analysis Viewer. By comparing codebases, you can gain valuable insights into code evolution, different implementation approaches, and the impact of refactoring.

Remember that the most effective comparison strategy depends on your specific goals and the nature of the codebases you're comparing. Experiment with different comparison options and metrics to find the approach that works best for your needs.


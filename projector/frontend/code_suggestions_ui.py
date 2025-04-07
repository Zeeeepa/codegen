import streamlit as st
import pandas as pd
import json
import os
from ..backend.code_analyzer import CodeAnalyzer

def render_code_suggestions_ui():
    """Render the code suggestions UI component."""
    st.header("Code Suggestions")
    
    # Initialize code analyzer
    code_analyzer = CodeAnalyzer()
    
    # File upload section
    st.subheader("Analyze Code")
    
    analysis_type = st.radio(
        "Select Analysis Type",
        ["Single File Analysis", "Repository Analysis"],
        horizontal=True
    )
    
    if analysis_type == "Single File Analysis":
        uploaded_file = st.file_uploader("Upload a code file for analysis", type=["py", "js", "ts", "jsx", "tsx"])
        
        if uploaded_file is not None:
            # Read file content
            content = uploaded_file.getvalue().decode("utf-8")
            file_path = uploaded_file.name
            
            # Analyze the file
            with st.spinner("Analyzing code..."):
                suggestions = code_analyzer.suggestion_engine.analyze_code(file_path, content)
                improvements = code_analyzer.generate_improved_code(file_path, content)
            
            # Display results
            if suggestions:
                st.success(f"Found {len(suggestions)} potential improvements")
                
                # Create tabs for different views
                suggestions_tab, code_tab, explanation_tab = st.tabs(["Suggestions", "Code View", "Explanation"])
                
                with suggestions_tab:
                    # Convert suggestions to DataFrame for better display
                    suggestions_data = []
                    for suggestion in suggestions:
                        suggestions_data.append({
                            "Line": suggestion["line"],
                            "Type": suggestion["type"].replace("_", " ").title(),
                            "Description": suggestion["description"]
                        })
                    
                    df = pd.DataFrame(suggestions_data)
                    st.dataframe(df, use_container_width=True)
                    
                    # Show detailed suggestion
                    if suggestions_data:
                        st.subheader("Suggestion Details")
                        selected_suggestion = st.selectbox(
                            "Select a suggestion to see details",
                            range(len(suggestions)),
                            format_func=lambda i: f"Line {suggestions[i]['line']}: {suggestions[i]['type'].replace('_', ' ').title()}"
                        )
                        
                        st.write("**Description:**")
                        st.write(suggestions[selected_suggestion]["description"])
                        
                        st.write("**Code Match:**")
                        st.code(suggestions[selected_suggestion]["match"])
                        
                        st.write("**Example Improvement:**")
                        st.code(suggestions[selected_suggestion]["example"])
                
                with code_tab:
                    st.subheader("Code with Suggestions")
                    
                    # Display code with line numbers and highlight lines with suggestions
                    lines = content.split("\n")
                    suggestion_lines = [s["line"] for s in suggestions]
                    
                    for i, line in enumerate(lines, 1):
                        if i in suggestion_lines:
                            st.markdown(f"<span style='background-color: #ffdddd;'>**{i}:** {line}</span>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"**{i}:** {line}")
                
                with explanation_tab:
                    st.subheader("Improvement Explanation")
                    st.write(improvements["explanation"])
                    
                    # Display estimated effort
                    critical_count = len([s for s in suggestions if s["type"] in ["error_handling", "no_error_handling"]])
                    important_count = len([s for s in suggestions if s["type"] in ["long_function", "complex_conditional", "repeated_code", "large_component"]])
                    minor_count = len(suggestions) - critical_count - important_count
                    
                    st.write("**Estimated Effort:**")
                    effort_data = {
                        "Priority": ["Critical", "Important", "Minor", "Total"],
                        "Issues": [critical_count, important_count, minor_count, len(suggestions)],
                        "Est. Hours": [
                            critical_count * 0.5,
                            important_count * 0.3,
                            minor_count * 0.1,
                            critical_count * 0.5 + important_count * 0.3 + minor_count * 0.1
                        ]
                    }
                    st.dataframe(pd.DataFrame(effort_data), use_container_width=True)
            else:
                st.info("No suggestions found. Your code looks good!")
    
    else:  # Repository Analysis
        st.info("Repository analysis allows you to analyze multiple files and get architectural suggestions.")
        
        repo_path = st.text_input("Enter local repository path or GitHub URL")
        
        if st.button("Analyze Repository") and repo_path:
            with st.spinner("Analyzing repository..."):
                # In a real implementation, this would clone/fetch the repository
                # For demo purposes, we'll use a mock implementation
                
                # Mock repository analysis
                st.warning("Using mock repository data for demonstration. In a real implementation, this would analyze the actual repository.")
                
                # Create mock files content
                files_content = {
                    "src/main.py": "def main():\n    print('Hello, world!')\n    data = fetch_data()\n    process_data(data)\n\ndef fetch_data():\n    return [1, 2, 3, 4, 5]\n\ndef process_data(data):\n    for item in data:\n        print(item * 2)",
                    "src/utils.py": "def calculate_average(numbers):\n    return sum(numbers) / len(numbers)\n\ndef calculate_median(numbers):\n    sorted_numbers = sorted(numbers)\n    n = len(sorted_numbers)\n    if n % 2 == 0:\n        return (sorted_numbers[n//2 - 1] + sorted_numbers[n//2]) / 2\n    else:\n        return sorted_numbers[n//2]"
                }
                
                # Generate suggestions
                suggestions_result = code_analyzer.generate_code_suggestions(files_content)
            
            # Display repository analysis results
            st.success("Repository analysis complete!")
            
            # Create tabs for different views
            overview_tab, files_tab, architecture_tab, plan_tab = st.tabs([
                "Overview", "File Suggestions", "Architecture", "Refactoring Plan"
            ])
            
            with overview_tab:
                st.subheader("Analysis Overview")
                
                # Display summary statistics
                file_count = len(suggestions_result["file_suggestions"])
                total_suggestions = sum(len(suggestions) for suggestions in suggestions_result["file_suggestions"].values())
                architectural_count = len(suggestions_result["architectural_suggestions"])
                
                st.write(f"**Files Analyzed:** {len(files_content)}")
                st.write(f"**Files with Suggestions:** {file_count}")
                st.write(f"**Total Suggestions:** {total_suggestions}")
                st.write(f"**Architectural Recommendations:** {architectural_count}")
                
                # Display code structure metrics
                st.subheader("Code Structure")
                structure = suggestions_result["code_structure"]
                
                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                with metrics_col1:
                    st.metric("Classes", len(structure["classes"]))
                with metrics_col2:
                    st.metric("Functions", len(structure["functions"]))
                with metrics_col3:
                    st.metric("Complexity Score", round(structure["complexity_metrics"]["avg_function_length"] / 10 + structure["complexity_metrics"]["max_nesting_depth"] * 5, 2))
            
            with files_tab:
                st.subheader("File-Level Suggestions")
                
                # Create a selectbox for files with suggestions
                files_with_suggestions = list(suggestions_result["file_suggestions"].keys())
                
                if files_with_suggestions:
                    selected_file = st.selectbox(
                        "Select a file to view suggestions",
                        files_with_suggestions
                    )
                    
                    file_suggestions = suggestions_result["file_suggestions"][selected_file]
                    
                    # Display suggestions for the selected file
                    if file_suggestions:
                        st.write(f"**{len(file_suggestions)} suggestions for {selected_file}**")
                        
                        # Convert suggestions to DataFrame
                        suggestions_data = []
                        for suggestion in file_suggestions:
                            suggestions_data.append({
                                "Line": suggestion["line"],
                                "Type": suggestion["type"].replace("_", " ").title(),
                                "Description": suggestion["description"]
                            })
                        
                        st.dataframe(pd.DataFrame(suggestions_data), use_container_width=True)
                        
                        # Show code with highlighted suggestions
                        st.subheader("Code View")
                        content = files_content[selected_file]
                        lines = content.split("\n")
                        suggestion_lines = [s["line"] for s in file_suggestions]
                        
                        code_container = st.container()
                        with code_container:
                            for i, line in enumerate(lines, 1):
                                if i in suggestion_lines:
                                    st.markdown(f"<span style='background-color: #ffdddd;'>**{i}:** {line}</span>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"**{i}:** {line}")
                else:
                    st.info("No file-level suggestions found.")
            
            with architecture_tab:
                st.subheader("Architectural Recommendations")
                
                arch_suggestions = suggestions_result["architectural_suggestions"]
                if arch_suggestions:
                    for i, suggestion in enumerate(arch_suggestions, 1):
                        with st.expander(f"{i}. {suggestion['type'].replace('_', ' ').title()}", expanded=i==1):
                            st.write(suggestion["description"])
                            st.code(suggestion["example"])
                else:
                    st.info("No architectural recommendations found.")
            
            with plan_tab:
                st.subheader("Refactoring Plan")
                
                plan = suggestions_result["refactoring_plan"]
                
                st.write("**Summary:**")
                st.write(plan["summary"])
                
                st.write("**Prioritized Issues:**")
                
                # Create a DataFrame for the prioritized issues
                priority_data = {
                    "Priority": ["Critical", "Important", "Minor"],
                    "Issues": [
                        len(plan["critical_issues"]),
                        len(plan["important_improvements"]),
                        len(plan["minor_improvements"])
                    ],
                    "Est. Hours": [
                        plan["estimated_effort"]["critical"],
                        plan["estimated_effort"]["important"],
                        plan["estimated_effort"]["minor"]
                    ]
                }
                
                st.dataframe(pd.DataFrame(priority_data), use_container_width=True)
                
                st.write(f"**Total Estimated Effort:** {plan['estimated_effort']['total']:.1f} hours")
                
                # File breakdown
                st.subheader("File Breakdown")
                
                file_data = []
                for file_path, count in plan["file_breakdown"].items():
                    file_data.append({
                        "File": file_path,
                        "Suggestions": count
                    })
                
                if file_data:
                    st.dataframe(pd.DataFrame(file_data), use_container_width=True)

def render_code_improvement_ui():
    """Render the code improvement UI component."""
    st.header("Code Improvement")
    
    # Initialize code analyzer
    code_analyzer = CodeAnalyzer()
    
    st.write("Upload a code file to get AI-powered improvement suggestions and automated refactoring.")
    
    uploaded_file = st.file_uploader("Upload a code file", type=["py", "js", "ts", "jsx", "tsx"])
    
    if uploaded_file is not None:
        # Read file content
        content = uploaded_file.getvalue().decode("utf-8")
        file_path = uploaded_file.name
        
        # Options for improvement
        st.subheader("Improvement Options")
        
        improvement_types = st.multiselect(
            "Select improvement types",
            ["Error Handling", "Code Structure", "Documentation", "Performance", "All"],
            default=["All"]
        )
        
        if st.button("Generate Improved Code"):
            with st.spinner("Analyzing and improving code..."):
                # In a real implementation, this would use the selected improvement types
                # For now, we'll use the default implementation
                improvements = code_analyzer.generate_improved_code(file_path, content)
            
            # Display results
            st.success("Code improvement complete!")
            
            # Create tabs for different views
            original_tab, improved_tab, diff_tab = st.tabs(["Original Code", "Improved Code", "Diff View"])
            
            with original_tab:
                st.subheader("Original Code")
                st.code(improvements["original_code"], language=file_path.split(".")[-1])
            
            with improved_tab:
                st.subheader("Improved Code")
                # In a real implementation, this would show the actual improved code
                # For now, we'll just show the original with a note
                st.info("In a full implementation, this would show the improved code with all suggestions applied.")
                st.code(improvements["original_code"], language=file_path.split(".")[-1])
            
            with diff_tab:
                st.subheader("Diff View")
                st.info("In a full implementation, this would show a diff between the original and improved code.")
                
                # Display changes
                if improvements["changes"]:
                    st.write(f"**{len(improvements['changes'])} suggested changes:**")
                    
                    for i, change in enumerate(improvements["changes"], 1):
                        with st.expander(f"{i}. Line {change['line']}: {change['type'].replace('_', ' ').title()}", expanded=i==1):
                            st.write(change["description"])
                            st.write("**Example:**")
                            st.code(change["example"])
                else:
                    st.info("No changes suggested. Your code looks good!")

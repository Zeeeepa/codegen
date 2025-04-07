"""
UI components for displaying merge information in the projector application.
"""
import streamlit as st
import pandas as pd
from datetime import datetime

def render_merge_history(project):
    """Render the merge history for a project."""
    st.subheader("Merge History")
    
    if hasattr(project, 'merges') and project.merges:
        # Create a dataframe for merges
        merges_data = []
        for merge in project.merges:
            merges_data.append({
                "Type": merge.get("type", "unknown"),
                "Title": merge.get("title", ""),
                "PR Number": merge.get("pr_number", ""),
                "From Branch": merge.get("head_branch", ""),
                "To Branch": merge.get("base_branch", ""),
                "Merged At": merge.get("merged_at", "")
            })
        
        # Display merges in a dataframe
        merges_df = pd.DataFrame(merges_data)
        st.dataframe(merges_df)
        
        # Display merge count
        st.metric("Total Merges", len(project.merges))
        
        # Expandable section to view all merges
        with st.expander("View All Merges", expanded=False):
            for i, merge in enumerate(project.merges):
                st.markdown(f"### Merge #{i+1}")
                st.markdown(f"**Type:** {merge.get('type', 'unknown')}")
                st.markdown(f"**Title:** {merge.get('title', '')}")
                st.markdown(f"**PR Number:** {merge.get('pr_number', '')}")
                st.markdown(f"**From Branch:** {merge.get('head_branch', '')}")
                st.markdown(f"**To Branch:** {merge.get('base_branch', '')}")
                st.markdown(f"**Merged At:** {merge.get('merged_at', '')}")
                st.markdown("---")
    else:
        st.info("No merges recorded for this project.")

def render_project_tabs_with_merges(project, github_manager, slack_manager):
    """Render project tabs including a merge history tab."""
    # Create tabs for different project views
    tabs = st.tabs(["Overview", "Features", "Documents", "GitHub", "Slack", "Merges"])
    
    # Merges Tab
    with tabs[5]:
        render_merge_history(project)
    
    return tabs

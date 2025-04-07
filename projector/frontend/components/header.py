import streamlit as st

def render_header(title):
    """Render a page header with the given title."""
    st.title(title)
    st.markdown("---")
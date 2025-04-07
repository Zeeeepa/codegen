"""
Accessibility settings component for the projector application.
"""
import streamlit as st
import logging
from .session_state import set_font_size, toggle_high_contrast, toggle_reduced_motion

def apply_accessibility_styles():
    """Apply accessibility styles based on session state settings."""
    # Font size styles
    font_size_css = ""
    if st.session_state.font_size == "small":
        font_size_css = """
        .stApp {
            font-size: 0.9rem;
        }
        """
    elif st.session_state.font_size == "medium":
        font_size_css = """
        .stApp {
            font-size: 1rem;
        }
        """
    elif st.session_state.font_size == "large":
        font_size_css = """
        .stApp {
            font-size: 1.2rem;
        }
        """
    
    # High contrast styles
    high_contrast_css = ""
    if st.session_state.high_contrast:
        high_contrast_css = """
        .stApp {
            color: white !important;
            background-color: black !important;
        }
        .stButton>button {
            color: black !important;
            background-color: white !important;
            border: 2px solid black !important;
        }
        .stTextInput>div>div>input {
            color: black !important;
            background-color: white !important;
        }
        .stSelectbox>div>div>div {
            color: black !important;
            background-color: white !important;
        }
        """
    
    # Reduced motion styles
    reduced_motion_css = ""
    if st.session_state.reduced_motion:
        reduced_motion_css = """
        * {
            transition: none !important;
            animation: none !important;
        }
        """
    
    # Apply all styles
    st.markdown(f"""
        <style>
            {font_size_css}
            {high_contrast_css}
            {reduced_motion_css}
        </style>
    """, unsafe_allow_html=True)

def render_accessibility_settings():
    """Render accessibility settings panel."""
    st.subheader("🌐 Accessibility Settings")
    
    # Font size
    st.write("**Font Size**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Small", key="small_font", 
                    help="Set font size to small",
                    disabled=st.session_state.font_size == "small"):
            set_font_size("small")
            st.rerun()
    with col2:
        if st.button("Medium", key="medium_font", 
                    help="Set font size to medium",
                    disabled=st.session_state.font_size == "medium"):
            set_font_size("medium")
            st.rerun()
    with col3:
        if st.button("Large", key="large_font", 
                    help="Set font size to large",
                    disabled=st.session_state.font_size == "large"):
            set_font_size("large")
            st.rerun()
    
    # High contrast mode
    st.write("**Display Options**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "High Contrast: " + ("ON" if st.session_state.high_contrast else "OFF"), 
            key="high_contrast",
            help="Toggle high contrast mode for better visibility"
        ):
            toggle_high_contrast()
            st.rerun()
    
    with col2:
        if st.button(
            "Reduced Motion: " + ("ON" if st.session_state.reduced_motion else "OFF"), 
            key="reduced_motion",
            help="Reduce animations and motion effects"
        ):
            toggle_reduced_motion()
            st.rerun()
    
    # Keyboard shortcuts
    st.write("**Keyboard Shortcuts**")
    shortcuts = {
        "Alt + 1-9": "Navigate to different pages",
        "Alt + S": "Toggle sidebar",
        "Alt + A": "Open accessibility settings",
        "Alt + D": "Toggle dark/light mode",
        "Alt + H": "Show help"
    }
    
    for key, description in shortcuts.items():
        st.write(f"**{key}**: {description}")
    
    # Screen reader information
    st.write("**Screen Reader Support**")
    st.write("This application supports screen readers. All images have alt text, and interactive elements have appropriate ARIA labels.")
    
    # Apply the styles
    apply_accessibility_styles()
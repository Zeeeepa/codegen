import streamlit as st

def main():
    st.title("Test App")
    
    # Define the pattern with the original syntax
    pattern1 = r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{3})"
    st.write(f"Original pattern: {pattern1}")
    
    # Define the pattern with the fixed syntax
    pattern2 = r"def\s+(\w+)\([^)]*\):\s*(?!\s*[\"\\']{\"3})"
    st.write(f"Fixed pattern: {pattern2}")

if __name__ == "__main__":
    main()

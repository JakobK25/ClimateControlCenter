import streamlit as st
import sys
import os
import atexit

# Add page config as the FIRST Streamlit command
st.set_page_config(page_title="Climate Control Center", layout="wide")

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import the app
from src.fieldLogger.app import FieldLoggerApp

def main():
    app = FieldLoggerApp()
    
    # Register cleanup handler
    atexit.register(app.cleanup)
    
    # Run the application
    app.run()

if __name__ == "__main__":
    main()
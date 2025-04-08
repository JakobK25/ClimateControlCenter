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

# This function will be called when the script exits completely (not on rerun)
def cleanup():
    if 'arduino_board' in st.session_state and st.session_state.arduino_board:
        try:
            st.session_state.arduino_board.exit()
            st.session_state.arduino_board = None
            st.session_state.arduino_initialized = False
        except:
            pass

def main():
    # Register cleanup for complete exit
    atexit.register(cleanup)
    
    # Initialize app
    app = FieldLoggerApp()
    
    # Run the application
    app.run()

if __name__ == "__main__":
    main()
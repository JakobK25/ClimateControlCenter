import streamlit as st
from src.fieldLogger.app import FieldLoggerApp
import atexit

def main():
    app = FieldLoggerApp()
    
    # Register cleanup handler
    atexit.register(app.cleanup)
    
    # Run the application
    app.run()

if __name__ == "__main__":
    main()
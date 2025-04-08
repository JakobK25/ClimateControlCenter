import streamlit as st
from ..config import Config  # Fix the import

def main():
    # Remove page config since it's in the main file now
    # st.set_page_config(page_title="Field Logger", page_icon="🌱", Layout="wide")
    st.title("ClimateControlCenter")


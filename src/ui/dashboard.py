import time
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
from src.db.models import get_recent_sensor_data

def setup_dashboard():
    """Initialize the Streamlit dashboard."""
    # Set up the page configuration
    st.set_page_config(
        page_title="Climate Control Center", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Add CSS for better styling
    st.markdown("""
        <style>
        .main {
            padding-top: 1rem;
        }
        .stMetric {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 10px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Create empty placeholder containers for dynamic content
    title_container = st.empty()
    sensor_container = st.empty()
    chart_container = st.empty()
    history_container = st.empty()
    
    return {
        'title': title_container,
        'sensors': sensor_container,
        'chart': chart_container,
        'history': history_container
    }

def update_dashboard(containers, config, data, conn=None):
    """Update the Streamlit dashboard with current sensor data."""
    try:
        # Update title section
        with containers['title']:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.title("Climate Control Center")
                st.write(f"Running in {config['DB_ENV']} mode - Connected to {config['DB_NAME']}.{config['TABLE_NAME']}")
            with col2:
                # Add current date and time
                st.write(f"Date: {dt.datetime.now().strftime('%Y-%m-%d')}")
                st.write(f"Time: {dt.datetime.now().strftime('%H:%M:%S')}")
        
        # Extract data
        temperature = data.get('temperature')
        light_percent = data.get('light_percent')
        light_category = data.get('light_category')
        humidity = data.get('humidity')
        changes = data.get('changes', {})
        
        # Show alert if significant changes detected
        alert_message = None
        if (changes.get('temp_change_pct', 0) > 2 or 
            changes.get('light_change_pct', 0) > 2 or 
            changes.get('humidity_change_pct', 0) > 2):
            alert_message = "⚠️ Significant environmental change detected!"
            st.warning(alert_message)
                
        # Update sensor readings section
        with containers['sensors']:
            st.subheader("Current Readings")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="Temperature", 
                    value=f"{temperature}°C" if temperature is not None else "N/A",
                    delta=f"{changes.get('temp_change_pct', 0):.1f}%" if changes.get('temp_change_pct') is not None else None
                )
                
            with col2:
                st.metric(
                    label="Light", 
                    value=f"{light_percent}%" if light_percent is not None else "N/A",
                    delta=f"{changes.get('light_change_pct', 0):.1f}%" if changes.get('light_change_pct') is not None else None
                )
                st.caption(f"Category: {light_category}")
                
            with col3:
                st.metric(
                    label="Humidity", 
                    value=f"{humidity}" if humidity is not None else "N/A",
                    delta=f"{changes.get('humidity_change_pct', 0):.1f}%" if changes.get('humidity_change_pct') is not None else None
                )
        
        # Update history chart section if we have database connection
        if conn:
            with containers['history']:
                st.subheader("Sensor History")
                
                # Get historical data from database
                recent_data = get_recent_sensor_data(conn, config['TABLE_NAME'], limit=30)
                
                if recent_data:
                    # Convert to DataFrame for easier plotting
                    df = pd.DataFrame(recent_data, columns=['temperature', 'humidity', 'light', 'timestamp'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df = df.sort_values('timestamp')
                    
                    # Create tabs for different charts
                    tab1, tab2, tab3 = st.tabs(["Temperature", "Light", "Humidity"])
                    
                    with tab1:
                        st.line_chart(df.set_index('timestamp')['temperature'])
                    
                    with tab2:
                        st.line_chart(df.set_index('timestamp')['light'])
                    
                    with tab3:
                        st.line_chart(df.set_index('timestamp')['humidity'])
                else:
                    st.info("No historical data available yet. Data will appear after several readings.")
        
        # Update simple status section
        with containers['chart']:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.caption(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                
            with col2:
                # Add indicator for whether LED is on
                if alert_message:
                    st.markdown("🔴 LED Status: **ON**")
                else:
                    st.markdown("⚪ LED Status: **OFF**")
    
    except Exception as e:
        st.error(f"Dashboard error: {e}")
        import traceback
        st.code(traceback.format_exc())
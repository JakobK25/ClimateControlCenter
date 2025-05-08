import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

def main(app):
    """
    Main dashboard UI.
    """
    # Set up the main UI structure
    st.title("Climate Control Center")
    
    # Add CSS for equal-sized containers
    st.markdown("""
    <style>
    /* Make containers equal size */
    div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        height: 210px !important;
        box-sizing: border-box;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 15px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Store last refresh time in session state
    if 'last_refresh_display' not in st.session_state:
        st.session_state.last_refresh_display = datetime.now()
        
    # Store last auto refresh time in session state
    if 'last_auto_refresh' not in st.session_state:
        st.session_state.last_auto_refresh = datetime.now()
    
    # Check if 10 minutes have passed since last auto refresh
    current_time = datetime.now()
    if current_time - st.session_state.last_auto_refresh > timedelta(minutes=10):
        # Update the readings directly without full page reload
        app.process_readings()
        app.save_to_database()
        st.session_state.last_refresh_display = current_time
        st.session_state.last_auto_refresh = current_time
        st.rerun()
    
    # Add sidebar with manual refresh button
    with st.sidebar:
        st.header("Refresh Controls")
        
        # Add manual refresh button with callback
        if st.button("Refresh Now", key="fast_refresh"):
            # Update the readings directly without full page reload
            app.process_readings()
            app.save_to_database()
            st.session_state.last_refresh_display = datetime.now()
            st.rerun()
        
        # Display last refresh time
        st.caption(f"Last refreshed: {st.session_state.last_refresh_display.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Display next auto refresh time (hidden in a comment for debugging if needed)
        next_refresh = st.session_state.last_auto_refresh + timedelta(minutes=10)
        st.caption(f"Next auto-refresh: {next_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Display sensor readings
    try:
        # Extract readings from app
        readings = app.readings
        
        # Create columns for metrics with equal width
        col1, col2, col3 = st.columns(3)

        # Display metrics in containers
        with col1:
            with st.container():
                st.subheader("Soil Moisture")
                soil = readings['soil_humidity']
                st.metric(
                    label="Moisture", 
                    value=f"{soil['percentage']}%" if soil['percentage'] is not None else "N/A",
                )
                st.caption(f"Status: {soil['status']}")

        with col2:
            with st.container():
                st.subheader("Air Temperature")
                temp = readings['air_temperature']
                st.metric(
                    label="Temperature", 
                    value=f"{temp['temperature']}°C" if temp['temperature'] is not None else "N/A",
                )
                st.write("")
                st.write("")

        with col3:
            with st.container():
                st.subheader("Light Level")
                light = readings['air_light']
                st.metric(
                    label="Light", 
                    value=f"{light['light']}%" if light['light'] is not None else "N/A",
                )
                st.caption(f"Status: {light['status']}")
                
        # Display historical data
        st.header("Sensor History (Last Hour)")
        
        # Get historical data from database
        from ..database import get_historical_data
        hist_data = get_historical_data(app.db_conn, app.db_cursor)
        
        # Display charts
        if not hist_data.empty:
            create_chart(hist_data)
        else:
            st.info("No historical data available yet. Data will appear here as it's collected.")
            
    except Exception as e:
        st.error(f"Error displaying data: {e}")
        import traceback
        st.code(traceback.format_exc())

def create_chart(df):
    """
    Create charts for the historical sensor data.
    """
    if df.empty:
        return st.warning("No data available for the chart.")
    
    # Set time as index for better chart display
    chart_df = df.copy()
    chart_df = chart_df.set_index('timestamp')
    
    # Use tabs for a more compact display
    tab1, tab2, tab3 = st.tabs(["Soil Moisture", "Temperature", "Light"])
    
    with tab1:
        st.line_chart(chart_df['soil_moisture'], use_container_width=True, height=300)
    
    with tab2:
        st.line_chart(chart_df['air_temp'], use_container_width=True, height=300)
    
    with tab3:
        st.line_chart(chart_df['air_light'], use_container_width=True, height=300)


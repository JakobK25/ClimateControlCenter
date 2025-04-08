import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def main(app):
    """Main dashboard UI."""
    # Initialize session state for refresh tracking
    if 'last_refresh_time' not in st.session_state:
        st.session_state.last_refresh_time = datetime.now()
    
    # Set up the main UI structure
    st.title("Climate Control Center")
    
    # Add custom CSS for equal-sized containers
    st.markdown("""
    <style>
    .metric-box {
        min-height: 200px;
        height: 200px;
        padding: 10px;
        box-sizing: border-box;
    }
    .stContainer {
        height: 200px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Add sidebar with refresh settings
    with st.sidebar:
        st.header("Refresh Settings")
        refresh_rate = st.slider("Refresh Rate (seconds)", min_value=1, max_value=60, value=app.config.REFRESH_RATE)
        
        # Calculate time until next refresh
        time_elapsed = datetime.now() - st.session_state.last_refresh_time
        time_until_refresh = timedelta(seconds=refresh_rate) - time_elapsed
        seconds_remaining = max(0, int(time_until_refresh.total_seconds()))
        minutes, seconds = divmod(seconds_remaining, 60)
        
        st.write(f"Next refresh in: {minutes}m {seconds}s")
        
        # Show progress bar
        progress_value = min(1.0, max(0.0, time_elapsed.total_seconds() / refresh_rate))
        st.progress(progress_value)
        
        # Add manual refresh button
        manual_refresh = st.button("Refresh Now")
        
        # Display last refresh time
        st.caption(f"Last refreshed: {st.session_state.last_refresh_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Display sensor readings
    try:
        # Extract readings from app
        readings = app.readings
        
        # Create columns for layout
        col1, col2 = st.columns(2)
        
        with col1:
            # Soil Moisture container
            with st.container():
                container = st.container(border=True)
                with container:
                    st.markdown('<div class="metric-box">', unsafe_allow_html=True)
                    st.subheader("Soil Moisture")
                    soil = readings['soil_humidity']
                    st.metric(
                        label="Moisture", 
                        value=f"{soil['percentage']}%" if soil['percentage'] is not None else "N/A",
                    )
                    st.caption(f"Status: {soil['status']}")
                    # Add empty space to ensure equal height
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Add some spacing between containers
            st.write("")
            
            # Air Flow container
            with st.container():
                container = st.container(border=True)
                with container:
                    st.markdown('<div class="metric-box">', unsafe_allow_html=True)
                    st.subheader("Air Flow")
                    flow = readings['air_wind']
                    st.metric(
                        label="Air Flow", 
                        value=f"{flow['speed']} m/s" if flow['speed'] is not None else "N/A",
                    )
                    st.caption(f"Status: {flow['status']}")
                    st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            # Air Temperature container
            with st.container():
                container = st.container(border=True)
                with container:
                    st.markdown('<div class="metric-box">', unsafe_allow_html=True)
                    st.subheader("Air Temperature")
                    temp = readings['air_temperature']
                    st.metric(
                        label="Temperature", 
                        value=f"{temp['temperature']}°C" if temp['temperature'] is not None else "N/A",
                    )
                    # Add extra space since this has no status
                    st.write("")
                    st.write("")
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Add some spacing between containers
            st.write("")
            
            # Light Level container
            with st.container():
                container = st.container(border=True)
                with container:
                    st.markdown('<div class="metric-box">', unsafe_allow_html=True)
                    st.subheader("Light Level")
                    light = readings['air_light']
                    st.metric(
                        label="Light", 
                        value=f"{light['light']}%" if light['light'] is not None else "N/A",
                    )
                    st.caption(f"Status: {light['status']}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
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
        
        # Handle refresh logic
        if manual_refresh:
            # Clean up Arduino connection before refresh
            app.arduino.close()
            
            # Update refresh time
            st.session_state.last_refresh_time = datetime.now()
            
            # Trigger rerun
            st.rerun()
            
        if (datetime.now() - st.session_state.last_refresh_time).total_seconds() >= refresh_rate:
            st.session_state.last_refresh_time = datetime.now()
            st.rerun()
            
    except Exception as e:
        st.error(f"Error displaying data: {e}")
        import traceback
        st.code(traceback.format_exc())

def create_chart(df):
    """Create charts for the historical sensor data."""
    if df.empty:
        return st.warning("No data available for the chart.")
    
    # Set time as index for better chart display
    chart_df = df.copy()
    chart_df = chart_df.set_index('timestamp')
    
    # Use tabs for a more compact display
    tab1, tab2, tab3, tab4 = st.tabs(["Soil Moisture", "Temperature", "Air Flow", "Light"])
    
    with tab1:
        st.line_chart(chart_df['soil_moisture'], use_container_width=True, height=300)
    
    with tab2:
        st.line_chart(chart_df['air_temp'], use_container_width=True, height=300)
    
    with tab3:
        st.line_chart(chart_df['air_flow'], use_container_width=True, height=300)
    
    with tab4:
        st.line_chart(chart_df['air_light'], use_container_width=True, height=300)


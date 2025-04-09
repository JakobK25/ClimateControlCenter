import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

def main(app):
    """Main dashboard UI."""
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
    
    # Store last refresh time in sidebar for display purposes
    if 'last_refresh_display' not in st.session_state:
        st.session_state.last_refresh_display = datetime.now()
    
    # Add sidebar with refresh settings
    with st.sidebar:
        st.header("Refresh Settings")
        
        # Get refresh rate from slider
        refresh_rate = st.slider("Refresh Rate (seconds)", 
                               min_value=1, 
                               max_value=60, 
                               value=int(app.config.REFRESH_RATE))
        
        # Add manual refresh button
        manual_refresh = st.button("Refresh Now")
        
        # Display last refresh time
        st.caption(f"Last refreshed: {st.session_state.last_refresh_display.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # NEW: Use Streamlit's built-in auto-refresh capability
        # This triggers a full page reload at the specified interval
        st.empty()  # This empty element will be replaced with auto-refresh
        
        # Add a note about refresh
        st.info(f"Page will auto-refresh every {refresh_rate} seconds")
        
    # Handle manual refresh button
    if manual_refresh:
        # Update display time
        st.session_state.last_refresh_display = datetime.now()
        # Close Arduino connection before refresh
        try:
            app.arduino.close()
        except:
            pass
        # Hard refresh with redirect to self
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        ctx = get_script_run_ctx()
        if ctx is not None:
            url = ctx.session_info.current_url
            st.markdown(f"""
            <meta http-equiv="refresh" content="0;URL='{url}'">
            """, unsafe_allow_html=True)
            st.stop()
    
    # NEW APPROACH: Add auto-refresh meta tag with JavaScript
    # This will refresh the entire page at the specified interval
    refresh_html = f"""
    <script>
    // Set timeout to refresh the page
    setTimeout(function() {{
        window.location.reload();
    }}, {refresh_rate * 1000});
    
    // Update countdown timer
    var countdownElement = document.getElementById('countdown');
    var seconds = {refresh_rate};
    function updateCountdown() {{
        seconds--;
        if (seconds < 0) return;
        var minutes = Math.floor(seconds / 60);
        var remainingSeconds = seconds % 60;
        if (countdownElement) {{
            countdownElement.innerText = minutes + "m " + remainingSeconds + "s";
        }}
        setTimeout(updateCountdown, 1000);
    }}
    updateCountdown();
    </script>
    """
    
    # Insert the refresh script
    st.components.v1.html(refresh_html, height=0)
    
    # Update display refresh time whenever page loads
    st.session_state.last_refresh_display = datetime.now()
    
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
    """Create charts for the historical sensor data."""
    if df.empty:
        return st.warning("No data available for the chart.")
    
    # Set time as index for better chart display
    chart_df = df.copy()
    chart_df = chart_df.set_index('timestamp')
    
    # Use tabs for a more compact display - removed air_flow tab
    tab1, tab2, tab3 = st.tabs(["Soil Moisture", "Temperature", "Light"])
    
    with tab1:
        st.line_chart(chart_df['soil_moisture'], use_container_width=True, height=300)
    
    with tab2:
        st.line_chart(chart_df['air_temp'], use_container_width=True, height=300)
    
    with tab3:
        st.line_chart(chart_df['air_light'], use_container_width=True, height=300)


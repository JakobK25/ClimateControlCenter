import time
import streamlit as st

def setup_dashboard():
    """Initialize the Streamlit dashboard."""
    # Set up the page configuration
    st.set_page_config(page_title="Climate Control Center", layout="wide")
    
    # Create empty placeholder containers for dynamic content
    title_container = st.empty()
    sensor_container = st.empty()
    chart_container = st.empty()
    
    return {
        'title': title_container,
        'sensors': sensor_container,
        'chart': chart_container
    }

def update_dashboard(containers, config, data):
    """Update the Streamlit dashboard with current sensor data."""
    try:
        # Update title section
        with containers['title']:
            st.title("Climate Control Center")
            st.write(f"Running in {config['DB_ENV']} mode - Connected to {config['DB_NAME']}.{config['TABLE_NAME']}")
        
        # Extract data
        temperature = data.get('temperature')
        light_percent = data.get('light_percent')
        light_category = data.get('light_category')
        humidity = data.get('humidity')
        changes = data.get('changes', {})
                
        # Update sensor readings section
        with containers['sensors']:
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
        
        # Update chart section
        with containers['chart']:
            st.subheader("Sensor History")
            st.write(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            st.write("Update frequency: every 15 seconds")
            
            # Show alert if significant changes detected
            if (changes.get('temp_change_pct', 0) > 2 or 
                changes.get('light_change_pct', 0) > 2 or 
                changes.get('humidity_change_pct', 0) > 2):
                st.warning("⚠️ Significant change detected!")
    
    except Exception as e:
        st.error(f"Dashboard error: {e}")
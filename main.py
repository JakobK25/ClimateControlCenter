import pyfirmata
from pyfirmata import util
import time
import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import psycopg2
import math
import struct
from datetime import datetime, timedelta
from threading import Thread

# Set page config
st.set_page_config(page_title="Climate Control Center", layout="wide")

# Load environment variables only once
@st.cache_resource
def load_environment():
    load_dotenv()
    return {
        "ARDUINO_PORT": os.getenv('ARDUINO_PORT', 'COM6'),
        "POSTGRES_USER": os.getenv('POSTGRES_USER', 'postgres'),
        "POSTGRES_PASSWORD": os.getenv('POSTGRES_PASSWORD', 'password1!'),
        "POSTGRES_DB": os.getenv('POSTGRES_DB', 'postgres')
    }

# Initialize Arduino and database connections only once
@st.cache_resource
def initialize_connections(env):
    # Connect to PostgreSQL database
    try:
        # Remove autocommit from connection parameters
        conn = psycopg2.connect(
            dbname=env["POSTGRES_DB"],
            user=env["POSTGRES_USER"],
            password=env["POSTGRES_PASSWORD"],
            host='localhost',
            port='5432'
        )
        # Set autocommit after connection is established
        conn.autocommit = True
        
        db = conn.cursor()
        
        # Create table needs to be in a transaction
        conn.autocommit = False
        try:
            create_table_query = """
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    soil_moisture FLOAT,
                    air_temp FLOAT,
                    air_flow FLOAT,  -- Changed from air_humidity
                    air_light FLOAT
                )
            """
            db.execute(create_table_query)
            conn.commit()
        except Exception as e:
            conn.rollback()
            st.error(f"Error creating table: {e}")
            raise
        finally:
            # Set back to autocommit for other operations
            conn.autocommit = True
            
    except Exception as e:
        st.error(f"Error connecting to PostgreSQL: {e}")
        raise

    # Initialize Arduino board
    try:
        board = pyfirmata.Arduino(env["ARDUINO_PORT"])
        it = pyfirmata.util.Iterator(board)
        it.start()
        
        # Setup pins
        SOIL_MOISTURE_PIN = 0
        AIR_TEMP_PIN = 1
        AIR_FLOW_PIN = 2
        AIR_LIGHT_PIN = 3
        
        board.analog[SOIL_MOISTURE_PIN].enable_reporting()
        board.analog[AIR_TEMP_PIN].enable_reporting()
        board.analog[AIR_FLOW_PIN].enable_reporting()
        board.analog[AIR_LIGHT_PIN].enable_reporting()
    except Exception as e:
        st.error(f"Error initializing Arduino: {e}")
        raise
    
    return board, conn, db

# Define pin numbers (constants)
SOIL_MOISTURE_PIN = 0
AIR_TEMP_PIN = 1
AIR_FLOW_PIN = 2  # Changed from AIR_HUMIDITY_PIN
AIR_LIGHT_PIN = 3

# Setup Thresholds
SOIL_MOISTURE_THRESHOLD = 0.5
AIR_TEMP_THRESHOLD = 25.0
AIR_FLOW_THRESHOLD = 5.0  # New threshold in m/s
AIR_LIGHT_THRESHOLD = 300.0

def calculate_air_humidity(ah_raw_value):
    if ah_raw_value is None:
        return {'percentage': None, 'status': None}
    
    try:
        # Calibration values - adjust these based on actual measurements
        DRY_VALUE = 0.8200    # Value when sensor is in very dry air (e.g., with silica gel)
        WET_VALUE = 0.4100    # Value when sensor is in high humidity (e.g., near boiling water)
        
        # Calculate humidity percentage (0% = dry, 100% = wet)
        # Constrain reading to calibration range
        constrained_value = max(WET_VALUE, min(DRY_VALUE, ah_raw_value))
        
        # Map the value from sensor range to 0-100% range (invert if needed)
        humidity_percentage = round(((DRY_VALUE - constrained_value) / (DRY_VALUE - WET_VALUE)) * 100, 1)
        
        # Ensure percentage is within valid range
        humidity_percentage = max(0, min(100, humidity_percentage))
        
    except Exception as e:
        st.error(f"Error calculating air humidity: {e}")
        return {'percentage': None, 'status': None}
    
    # Determine humidity status
    if humidity_percentage < 20:
        status = "Very Dry"
    elif humidity_percentage < 40:
        status = "Dry"
    elif humidity_percentage < 60:
        status = "Moderate"
    elif humidity_percentage < 80:
        status = "Moist"
    else:
        status = "Wet"

    return {
        'percentage': humidity_percentage,
        'status': status
    }
    
def calculate_air_temp(at_raw_value):
    if at_raw_value is None:
        return {'temperature': None, 'status': None}
    
    try:
        SERIES_RESISTOR = 10000
        BETA_COEFFICIENT = 3950
        NOMINAL_TEMPERATURE = 25
        NOMINAL_RESISTANCE = 10000

        if at_raw_value == 0:
            resistance = float('inf')
        elif at_raw_value == 1:
            resistance = 0
        else:
            resistance = SERIES_RESISTOR * (1 - at_raw_value) / at_raw_value

        steinhart = resistance / NOMINAL_RESISTANCE
        steinhart = math.log(steinhart)
        steinhart /= BETA_COEFFICIENT
        steinhart += 1.0 / (NOMINAL_TEMPERATURE + 273.15)
        steinhart = 1.0 / steinhart
        celcius = round(steinhart - 273.15, 1)
        corrected_celcius = celcius - 5
    
    except Exception as e:
        st.error(f"Error calculating air temperature: {e}")
        return {'temperature': None, 'status': None}
    
    return {
        'temperature': corrected_celcius,
    }

def calculate_soil_moisture(sm_raw_value):
    if sm_raw_value is None:
        return {'moisture': None, 'status': None}
    
    try:
        # Calibration values from actual sensor readings
        WET_VALUE = 0.4900   # Value when submerged in water
        DRY_VALUE = 0.6600   # Value when in regular air
        
        # Calculate moisture percentage (0% = dry, 100% = wet)
        # Constrain reading to calibration range
        constrained_value = max(WET_VALUE, min(DRY_VALUE, sm_raw_value))
        
        # Map the value from sensor range to 0-100% range
        sm_percentage = round(((DRY_VALUE - constrained_value) / (DRY_VALUE - WET_VALUE)) * 100, 1)
        
        # Ensure percentage is within valid range
        sm_percentage = max(0, min(100, sm_percentage))
        
    except Exception as e:
        st.error(f"Error calculating soil moisture: {e}")
        return {'moisture': None, 'status': None}
    
    if sm_percentage < 20:
        status = "Very Dry"
    elif sm_percentage < 40:
        status = "Dry"
    elif sm_percentage < 60:
        status = "Moderate"
    elif sm_percentage < 80:
        status = "Moist"
    else:
        status = "Wet"

    return {
        'moisture': sm_percentage,
        'status': status
    }
    
def calculate_air_light(al_raw_value):
    if al_raw_value is None:
        return {'light': None, 'status': None}
    
    try:        
        # Direct translation: raw value * 100 = percentage
        # For example: 0.0 = 0%, 0.36 = 36%, etc.
        light_percentage = round(al_raw_value * 100, 1)
        
        # Ensure percentage is within valid range
        light_percentage = max(0, min(100, light_percentage))
        
    except Exception as e:
        st.error(f"Error calculating light level: {e}")
        return {'light': None, 'status': None}
    
    # Determine light status
    if light_percentage < 20:
        status = "Very Dark"
    elif light_percentage < 40:
        status = "Dark"
    elif light_percentage < 60:
        status = "Moderate"
    elif light_percentage < 80:
        status = "Bright"
    else:
        status = "Very Bright"

    return {
        'light': light_percentage,
        'status': status
    }

def calculate_air_flow(af_raw_value):
    """Convert raw air flow sensor reading to speed and status."""
    if af_raw_value is None:
        return {'speed': None, 'status': None}
    
    try:
        # Calibration values for wind/flow sensor
        # These should be adjusted based on actual measurements
        MIN_VALUE = 0.1     # Value when no air flow
        MAX_VALUE = 0.9     # Value at maximum measurable flow
        
        # Calculate flow percentage (0% = no flow, 100% = maximum flow)
        # Constrain reading to calibration range
        constrained_value = max(MIN_VALUE, min(MAX_VALUE, af_raw_value))
        
        # Map the value from sensor range to 0-100% range
        flow_percentage = round(((constrained_value - MIN_VALUE) / (MAX_VALUE - MIN_VALUE)) * 100, 1)
        
        # Convert to approximate speed in m/s (adjust based on sensor specifications)
        # This is a simple linear mapping - replace with proper calibration formula if available
        flow_speed = round(flow_percentage * 0.1, 2)  # Example: 100% = 10 m/s
        
        # Ensure values are within valid ranges
        flow_percentage = max(0, min(100, flow_percentage))
        flow_speed = max(0, flow_speed)
        
    except Exception as e:
        st.error(f"Error calculating air flow: {e}")
        return {'speed': None, 'percentage': None, 'status': None}
    
    # Determine flow status
    if flow_percentage < 20:
        status = "Very Low"
    elif flow_percentage < 40:
        status = "Low"
    elif flow_percentage < 60:
        status = "Moderate"
    elif flow_percentage < 80:
        status = "High"
    else:
        status = "Very High"

    return {
        'speed': flow_speed,
        'percentage': flow_percentage,
        'status': status
    }

def last_hour_readings(conn, db, hours=1):
    try:
        time_from = datetime.now() - timedelta(hours=hours)
        query = """
            select * from sensor_data
            where timestamp >= %s
            order by timestamp ASC
        """

        db.execute(query, (time_from,))
        rows = db.fetchall()

        if rows:
            df = pd.DataFrame(rows, columns=[desc[0] for desc in db.description])
            return df
        else:
            return pd.DataFrame(columns=['id', 'timestamp', 'soil_moisture', 'air_temp', 'air_flow', 'air_light'])
    except Exception as e:
        st.error(f"Error fetching last hour readings: {e}")
        return pd.DataFrame(columns=['id', 'timestamp', 'soil_moisture', 'air_temp', 'air_flow', 'air_light'])
    
def create_chart(df):
    """Create charts for the historical sensor data."""
    if df.empty:
        return st.warning("No data available for the chart.")
    
    # Set time as index for better chart display
    chart_df = df.copy()
    chart_df = chart_df.set_index('timestamp')
    
    # Create separate charts for each sensor
    st.subheader("Soil Moisture History")
    fig1 = st.line_chart(chart_df['soil_moisture'], use_container_width=True, height=250)
    
    st.subheader("Temperature History")
    fig2 = st.line_chart(chart_df['air_temp'], use_container_width=True, height=250)
    
    st.subheader("Air Flow History")
    fig3 = st.line_chart(chart_df['air_flow'], use_container_width=True, height=250)
    
    st.subheader("Light Level History")
    fig4 = st.line_chart(chart_df['air_light'], use_container_width=True, height=250)
    
    return fig1, fig2, fig3, fig4

# Add a function to handle database operations safely
def safe_db_execute(conn, cursor, query, data=None):
    """Execute a database query safely with proper transaction handling."""
    try:
        if data:
            cursor.execute(query, data)
        else:
            cursor.execute(query)
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()  # Roll back the transaction on error
        return False, str(e)

# Main app logic
def main():
    # Initialize session state for auto-refresh
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()
    
    # Store the value in a regular variable for the thread to access
    last_refresh_time = st.session_state.last_refresh
    
    # Get environment variables
    env = load_environment()
    
    # Set up the main UI structure
    st.title("Climate Control Center")
    
    # Add sidebar with auto-refresh information
    with st.sidebar:
        st.header("Refresh Settings")
        refresh_interval = 5  # minutes in full
        st.info(f"Auto-refresh every {refresh_interval} minutes")
        
        # Calculate time until next refresh
        time_elapsed = datetime.now() - st.session_state.last_refresh
        time_until_refresh = timedelta(minutes=refresh_interval) - time_elapsed
        
        # Show minutes remaining with a descriptive message
        minutes_remaining = max(0, int(time_until_refresh.total_seconds() // 60))
        
        if minutes_remaining > 1:
            st.write(f"Next refresh in about {minutes_remaining} minutes")
        elif minutes_remaining == 1:
            st.write("Next refresh in about 1 minute")
        else:
            seconds_remaining = max(0, int(time_until_refresh.total_seconds()))
            if seconds_remaining > 30:
                st.write("Next refresh in less than a minute")
            else:
                st.write("Next refresh coming up soon...")
        
        # Create a progress bar for auto-refresh
        progress_value = min(1.0, max(0.0, time_elapsed.total_seconds() / (refresh_interval * 60)))
        progress = st.progress(progress_value)
        
        # Add manual refresh button
        manual_refresh = st.button("Refresh Now")
        
        # Display last refresh time
        st.caption(f"Last refreshed: {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")

    # Initialize connections
    try:
        board, conn, db = initialize_connections(env)
    except Exception as e:
        st.error("Failed to initialize connections. Please check your settings.")
        return
        
    # Read and display sensor data
    try:
        # Read sensor values
        sm_raw_value = board.analog[SOIL_MOISTURE_PIN].read()
        at_raw_value = board.analog[AIR_TEMP_PIN].read()
        af_raw_value = board.analog[AIR_FLOW_PIN].read()
        al_raw_value = board.analog[AIR_LIGHT_PIN].read()
        
        # Wait for valid readings
        time.sleep(0.1)

        # Calculate sensor values
        soil_moisture = calculate_soil_moisture(sm_raw_value)
        air_temp = calculate_air_temp(at_raw_value)
        air_flow = calculate_air_flow(af_raw_value)
        air_light = calculate_air_light(al_raw_value)
        
        # Update the UI containers with fresh data
        col1, col2 = st.columns(2)
        with col1:
            with st.container():
                st.subheader("Soil Moisture")
                st.metric(
                    label="Moisture", 
                    value=f"{soil_moisture['moisture']}%" if soil_moisture['moisture'] is not None else "N/A",
                )
                st.caption(f"Status: {soil_moisture['status']}")
            
            with st.container():
                st.subheader("Air Flow")
                st.metric(
                    label="Air Flow", 
                    value=f"{air_flow['speed']} m/s" if air_flow and 'speed' in air_flow else "N/A",
                )
                st.caption(f"Status: {air_flow['status'] if air_flow and 'status' in air_flow else 'Unknown'}")
        
        with col2:
            with st.container():
                st.subheader("Air Temperature")
                st.metric(
                    label="Temperature", 
                    value=f"{air_temp['temperature']}°C" if air_temp['temperature'] is not None else "N/A",
                )
            
            with st.container():
                st.subheader("Light Level")
                st.metric(
                    label="Light", 
                    value=f"{air_light['light']}%" if air_light['light'] is not None else "N/A",
                )
                st.caption(f"Status: {air_light['status']}")
        
        # Write data to PostgreSQL database
        try:
            # First check if we have valid data to insert
            if (soil_moisture['moisture'] is not None and 
                air_temp['temperature'] is not None and 
                air_flow is not None and 'percentage' in air_flow and 
                air_light is not None and 'light' in air_light):
                
                insert_query = """
                    INSERT INTO sensor_data (timestamp, soil_moisture, air_temp, air_flow, air_light)
                    VALUES (%s, %s, %s, %s, %s)
                """
                data = (
                    datetime.now(),
                    soil_moisture['moisture'],
                    air_temp['temperature'],
                    air_flow['percentage'],
                    air_light['light']
                )
                
                # Use the safe execution function
                success, error = safe_db_execute(conn, db, insert_query, data)
                
                if success:
                    st.sidebar.success("Data saved to database")
                else:
                    st.sidebar.error(f"Database error: {error}")
                    # Reconnect to the database if needed
                    try:
                        # Close the current connection if it's still open
                        db.close()
                        conn.close()
                    except:
                        pass
                        
                    # Re-initialize the connection for next time
                    board, conn, db = initialize_connections(env)
            else:
                st.sidebar.warning("Not saving to database: one or more sensor values are missing")
                
        except Exception as e:
            st.error(f"Error writing to database: {e}")
            import traceback
            st.sidebar.error("Failed to save data")
            st.sidebar.code(traceback.format_exc())
            
            # Try to rollback any pending transaction
            try:
                conn.rollback()
            except:
                pass
        
    except Exception as e:
        st.error(f"Error reading sensor data: {e}")
        import traceback
        st.code(traceback.format_exc())

    # Display historical data charts
    st.header("Sensor History (Last Hour)")

    # Get historical data
    hist_data = last_hour_readings(conn, db)

    # Display the charts
    if not hist_data.empty:
        create_chart(hist_data)
    else:
        st.info("No historical data available yet. Data will appear here as it's collected.")

    # Check if it's time to auto-refresh (5 minutes passed) or manual refresh button pressed
    current_time = datetime.now()
    if manual_refresh or (current_time - st.session_state.last_refresh) > timedelta(minutes=refresh_interval):
        # Update the last refresh time
        st.session_state.last_refresh = current_time
        # Trigger page rerun
        st.rerun()
    else:
        # If it's not time to refresh yet, add a 1-second automatic rerun
        # This will update the countdown timer every second
        time.sleep(1)
        st.rerun()

# Run the main function
if __name__ == "__main__":
    main()
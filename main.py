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
                    air_humidity FLOAT,
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
        AIR_HUMIDITY_PIN = 2
        AIR_LIGHT_PIN = 3
        
        board.analog[SOIL_MOISTURE_PIN].enable_reporting()
        board.analog[AIR_TEMP_PIN].enable_reporting()
        board.analog[AIR_HUMIDITY_PIN].enable_reporting()
        board.analog[AIR_LIGHT_PIN].enable_reporting()
    except Exception as e:
        st.error(f"Error initializing Arduino: {e}")
        raise
    
    return board, conn, db

# Define pin numbers (constants)
SOIL_MOISTURE_PIN = 0
AIR_TEMP_PIN = 1
AIR_HUMIDITY_PIN = 2
AIR_LIGHT_PIN = 3

# Setup Thresholds
SOIL_MOISTURE_THRESHOLD = 0.5
AIR_TEMP_THRESHOLD = 25.0
AIR_HUMIDITY_THRESHOLD = 60.0
AIR_LIGHT_THRESHOLD = 300.0

def calculate_air_humidity(ah_raw_value):
    if ah_raw_value is None:
        return {'percentage': None, 'status': None}  # Return consistent structure
    
    air_value = 1023 - ah_raw_value
    water_value = 1023 - air_value

    if air_value == water_value:
        percentage = 0
    else:
        constrained = max(water_value, min(air_value, ah_raw_value))
        percentage = round(100 - ((constrained - water_value) * 100 / (air_value - water_value)), 1)

    if percentage < 20:
        status = "Very Dry"
    elif percentage < 40:
        status = "Dry"
    elif percentage < 60:
        status = "Moderate"
    elif percentage < 80:
        status = "Moist"
    else:
        status = "Wet"
    
    return {
        'percentage': percentage,
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
    
    except Exception as e:
        st.error(f"Error calculating air temperature: {e}")
        return {'temperature': None, 'status': None}
    
    return {
        'temperature': celcius,
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
        al_raw_value = 1023 - al_raw_value
        al_percentage = round((al_raw_value / 1023) * 100, 1)
    except Exception as e:
        st.error(f"Error calculating air light: {e}")
        return {'light': None, 'status': None}
    
    if al_percentage < 20:
        status = "Very Low"
    elif al_percentage < 40:
        status = "Low"
    elif al_percentage < 60:
        status = "Moderate"
    elif al_percentage < 80:
        status = "High"
    else:
        status = "Very High"

    return {
        'light': al_percentage,
        'status': status
    }

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
    
    # Get environment variables
    env = load_environment()
    
    # Initialize connections
    try:
        board, conn, db = initialize_connections(env)
    except Exception as e:
        st.error("Failed to initialize connections. Please check your settings.")
        return
    
    # Set up the main UI structure
    st.title("Climate Control Center")
    
    # Add sidebar with auto-refresh information
    with st.sidebar:
        st.header("Refresh Settings")
        refresh_interval = 5  # minutes
        st.info(f"Auto-refresh every {refresh_interval} minutes")
        
        # Calculate time until next refresh
        time_elapsed = datetime.now() - st.session_state.last_refresh
        time_until_refresh = timedelta(minutes=refresh_interval) - time_elapsed
        minutes, seconds = divmod(max(0, time_until_refresh.seconds), 60)
        
        # Display time until next refresh
        st.write(f"Next refresh in: {minutes}m {seconds}s")
        
        # Add manual refresh button
        manual_refresh = st.button("Refresh Now")
        
        # Display last refresh time
        st.caption(f"Last refreshed: {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create a progress bar for auto-refresh
    progress_seconds = min(time_elapsed.seconds, refresh_interval * 60)
    progress = st.progress(progress_seconds / (refresh_interval * 60))
    
    # Create placeholders for each sensor reading
    col1, col2 = st.columns(2)
    
    # Read and display sensor data
    try:
        # Read sensor values
        sm_raw_value = board.analog[SOIL_MOISTURE_PIN].read()
        at_raw_value = board.analog[AIR_TEMP_PIN].read()
        ah_raw_value = board.analog[AIR_HUMIDITY_PIN].read()
        al_raw_value = board.analog[AIR_LIGHT_PIN].read()
        
        # Wait for valid readings
        time.sleep(0.1)

        # Calculate sensor values
        soil_moisture = calculate_soil_moisture(sm_raw_value)
        air_temp = calculate_air_temp(at_raw_value)
        air_humidity = calculate_air_humidity(ah_raw_value)
        air_light = calculate_air_light(al_raw_value)
        
        # Update the UI containers with fresh data
        with col1:
            with st.container():
                st.subheader("Soil Moisture")
                st.metric(
                    label="Moisture", 
                    value=f"{soil_moisture['moisture']}%" if soil_moisture['moisture'] is not None else "N/A",
                )
                st.caption(f"Status: {soil_moisture['status']}")
            
            with st.container():
                st.subheader("Air Humidity")
                st.metric(
                    label="Humidity", 
                    value=f"{air_humidity['percentage']}%" if air_humidity and 'percentage' in air_humidity else "N/A",
                )
                st.caption(f"Status: {air_humidity['status'] if air_humidity and 'status' in air_humidity else 'Unknown'}")
        
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
                air_humidity is not None and 'percentage' in air_humidity and 
                air_light is not None and 'light' in air_light):
                
                insert_query = """
                    INSERT INTO sensor_data (timestamp, soil_moisture, air_temp, air_humidity, air_light)
                    VALUES (%s, %s, %s, %s, %s)
                """
                data = (
                    datetime.now(),
                    soil_moisture['moisture'],
                    air_temp['temperature'],
                    air_humidity['percentage'],
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

    # Check if it's time to auto-refresh (5 minutes passed) or manual refresh button pressed
    if manual_refresh or (datetime.now() - st.session_state.last_refresh) > timedelta(minutes=refresh_interval):
        # Update the last refresh time
        st.session_state.last_refresh = datetime.now()
        # Trigger page rerun
        st.rerun()

# Run the main function
if __name__ == "__main__":
    main()
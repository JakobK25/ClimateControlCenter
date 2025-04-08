from .config import Config
import streamlit as st
import psycopg2
import os
from datetime import datetime

def init_db_connection(config):
    """Initialize database connection and cursor."""
    # Connect to PostgreSQL database
    try:
        conn = psycopg2.connect(**config.get_db_params())
        conn.autocommit = True
        
        cursor = conn.cursor()
        
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
            cursor.execute(create_table_query)
            conn.commit()
        except Exception as e:
            conn.rollback()
            st.error(f"Error creating table: {e}")
            raise
        finally:
            # Set back to autocommit for other operations
            conn.autocommit = True
            
        return conn, cursor
            
    except Exception as e:
        st.error(f"Error connecting to PostgreSQL: {e}")
        raise

def save_sensor_data(conn, cursor, readings):
    """Save sensor readings to database."""
    try:
        # Check if we have valid data to insert
        if all(key in readings for key in ['soil_humidity', 'air_temperature', 'air_wind', 'air_light']):
            
            # Extract the percentage/values from each reading
            soil_moisture = readings['soil_humidity']['percentage'] if 'percentage' in readings['soil_humidity'] else None
            air_temp = readings['air_temperature']['temperature'] if 'temperature' in readings['air_temperature'] else None
            air_flow = readings['air_wind']['speed'] if 'speed' in readings['air_wind'] else None
            air_light = readings['air_light']['light'] if 'light' in readings['air_light'] else None
            
            if all(val is not None for val in [soil_moisture, air_temp, air_flow, air_light]):
                insert_query = """
                    INSERT INTO sensor_data (timestamp, soil_moisture, air_temp, air_flow, air_light)
                    VALUES (%s, %s, %s, %s, %s)
                """
                data = (
                    datetime.now(),
                    soil_moisture,
                    air_temp,
                    air_flow,
                    air_light
                )
                
                cursor.execute(insert_query, data)
                conn.commit()
                return True, "Data saved to database"
            else:
                return False, "One or more sensor values are None"
        else:
            return False, "One or more sensor readings are missing"
                
    except Exception as e:
        conn.rollback()
        return False, f"Error writing to database: {e}"

def get_historical_data(conn, cursor, hours=1):
    """Get historical sensor data from the last X hours."""
    from datetime import timedelta
    import pandas as pd
    
    try:
        time_from = datetime.now() - timedelta(hours=hours)
        query = """
            SELECT * FROM sensor_data
            WHERE timestamp >= %s
            ORDER BY timestamp ASC
        """

        cursor.execute(query, (time_from,))
        rows = cursor.fetchall()

        if rows:
            df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])
            return df
        else:
            return pd.DataFrame(columns=['id', 'timestamp', 'soil_moisture', 'air_temp', 'air_flow', 'air_light'])
    except Exception as e:
        st.error(f"Error fetching historical data: {e}")
        return pd.DataFrame(columns=['id', 'timestamp', 'soil_moisture', 'air_temp', 'air_flow', 'air_light'])
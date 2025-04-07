from config import config
import streamlit as st
import psycopg2
import os

def init_db_connection():
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
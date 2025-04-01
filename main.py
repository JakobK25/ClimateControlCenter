import pyfirmata
import time
import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import psycopg2

# Load environment variables from .env file
load_dotenv()

# Get environment variables
ARDUINO_PORT = os.getenv('ARDUINO_PORT', 'COM5')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'password1!')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'postgres')

# Initialize the Arduino board
try:
    board = pyfirmata.Arduino(ARDUINO_PORT)
    print(f"Connected to Arduino on port: {ARDUINO_PORT}")

    it = pyfirmata.util.Iterator(board)
    it.start()
    time.sleep(1)  # Give time for the board to initialize
except Exception as e:
    print(f"Failed to connect to Arduino: {e}")
    exit(1)


# Database connection string (if needed)
try:
    db_connection_string = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/{POSTGRES_DB}"
    print(f"Database connection string: {db_connection_string}")

    # Setup the database connection
    conn = psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host='localhost',
        port='5432'
    )
    print("Connected to PostgreSQL database")

 
except Exception as e:
    print(f"Failed to create database connection string: {e}")
    exit(1)

# Create a table if it doesn't exist
try:
    with conn.cursor() as cursor:
        # First, check if the table exists and what columns it has
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'sensor_data'
        """)
        columns = cursor.fetchall()
        print(f"Existing columns in sensor_data: {columns}")
        
        if not columns:
            # Create the table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id SERIAL PRIMARY KEY,
                    temperature INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("Table 'sensor_data' created with columns: id, temperature, timestamp")
        elif 'temperature' not in [col[0] for col in columns]:
            # If the table exists but doesn't have a temperature column, drop and recreate
            cursor.execute("DROP TABLE sensor_data")
            conn.commit()
            cursor.execute("""
                CREATE TABLE sensor_data (
                    id SERIAL PRIMARY KEY,
                    temperature INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("Table 'sensor_data' recreated with correct columns")
        else:
            print("Table 'sensor_data' already exists with correct columns")
except Exception as e:
    print(f"Failed to configure table: {e}")
    exit(1)

# Configure the analog pin for reading
board.analog[0].enable_reporting()
print("Analog pin 0 configured for reading")

# Read data from arduino and add to database
while True:
    try:
        # Read data from Arduino (example: analog pin A0)
        print("Reading data from Arduino...")
        analog_value = board.analog[0].read()
        print(f"Raw analog value: {analog_value}")
        
        if analog_value is not None:
            # Convert to temperature (example conversion - adjust as needed)
            temperature = int(analog_value * 1023)  # Scale to 0-1023
            
            # Insert data into PostgreSQL database
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO sensor_data (temperature) VALUES (%s)", (temperature,))
                conn.commit()
                print(f"Inserted temperature: {temperature} into database")
        time.sleep(2)  # Shorter delay for testing

    except KeyboardInterrupt:
        print("Exiting...")
        break
    except Exception as e:
        print(f"Error: {e}")
        print(f"Type: {type(e)}")
        break

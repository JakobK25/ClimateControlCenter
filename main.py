import pyfirmata
import time
import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import psycopg2
import math

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
                    temperature FLOAT NOT NULL,
                    humidity FLOAT NOT NULL,
                    light FLOAT NOT NULL,
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
                    temperature FLOAT NOT NULL,
                    humidity FLOAT NOT NULL,
                    light FLOAT NOT NULL,
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

# Setup pins on the arduino

# Input
board.analog[0].enable_reporting() # Temperature sensor (analog pin A0)
board.analog[1].enable_reporting() # Light sensor (analog pin A1)
board.analog[2].enable_reporting() # Humidity sensor (analog pin A2)


# Output
board.digital[2].mode = pyfirmata.OUTPUT # LED (digital pin 2)

# Read data from arduino and add to database
while True:
    try:
        # Read all data from the sensors
        temperature_raw = board.analog[0].read()
        light_raw = board.analog[1].read()
        humidity_raw = board.analog[2].read()
        
        # Calculate human-readable temperature
        if temperature_raw is not None:
            try:
                # UPDATED OPTION 1: Direct calibration based on known points
                # If 0.4976 = 20°C, create a CORRECTED linear equation
                temperature_celsius = round((temperature_raw * 40), 1)  # This will give ~20°C at 0.4976
                
                # OPTION 2: Revised thermistor calculation for correct circuit connection
                # Assuming thermistor is actually connected to ground (not VCC) with 10K pullup
                if temperature_raw > 0:  # Prevent division by zero
                    resistance = 10000 * ((1 - temperature_raw) / temperature_raw)
                    
                    # B-parameter equation with adjusted constants
                    B_constant = 4275
                    T0 = 298.15       # 25°C in Kelvin
                    R0 = 100000       # 100KΩ at 25°C
                    
                    # Calculate temperature in Kelvin
                    temperature_kelvin = 1 / ((1 / T0) + (1 / B_constant) * math.log(resistance / R0))
                    # Convert to Celsius
                    thermistor_celsius = round(temperature_kelvin - 273.15, 1)
                    
                    # Print both calculations for comparison
                    print(f"Raw: {temperature_raw}, Resistance: {resistance:.1f}Ω")
                    print(f"Linear model: {temperature_celsius}°C, Thermistor model: {thermistor_celsius}°C")
                else:
                    print(f"Raw: {temperature_raw} (invalid reading)")
                    thermistor_celsius = None
                    
                # Use the linear calibration for now
                # temperature_celsius = thermistor_celsius  # Uncomment to use thermistor model instead
            except (ValueError, ZeroDivisionError, TypeError) as e:
                print(f"Temperature calculation error: {e}")
                temperature_celsius = None
        else:
            temperature_celsius = None
            
        # Calculate human-readable light values
        if light_raw is not None:
            # Convert to percentage (0-100%)
            light_percent = round(light_raw * 100, 1)
            
            # Convert to descriptive category
            if light_raw < 0.1:
                light_category = "Very dark"
            elif light_raw < 0.3:
                light_category = "Dark"
            elif light_raw < 0.5:
                light_category = "Moderate light"
            elif light_raw < 0.8:
                light_category = "Bright"
            else:
                light_category = "Very bright"          
        else:
            light_percent = None
            light_category = "Unknown"
            
        # Print all sensor data with human-readable values
        print(f"Temperature: {temperature_raw} → {temperature_celsius}°C")
        print(f"Light: {light_raw} → {light_percent}% ({light_category})")
        print(f"Humidity: {humidity_raw}")
        
        # Insert all climate data into the database
        if temperature_celsius is not None and light_raw is not None and humidity_raw is not None:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO sensor_data (temperature, humidity, light) 
                    VALUES (%s, %s, %s)
                """, (temperature_celsius, humidity_raw, light_raw))
                conn.commit()
                print("Data inserted into database")
        else:
            print("Data not inserted into database due to missing values")

        sleep_time = 3  # seconds
        time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("Exiting...")
        break
    except Exception as e:
        print(f"Error: {e}")
        print(f"Type: {type(e)}")
        break

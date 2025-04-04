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
ARDUINO_PORT = os.getenv('ARDUINO_PORT', 'COM3')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'password1!')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'postgres')

# Ask user for environment selection
print("=== Climate Control Center ===")
env_selection = input("Run in production or testing mode? (p/t): ").lower()

# Set database configuration based on selection
if env_selection.startswith('p'):
    DB_ENV = "PRODUCTION"
    DB_NAME = POSTGRES_DB
    TABLE_NAME = "sensor_data"
    DB_HOST = "localhost"  # Connect to local machine
    DB_PORT = "5432"       # Standard PostgreSQL port
else:
    DB_ENV = "TESTING"
    DB_NAME = f"{POSTGRES_DB}_test"
    TABLE_NAME = "sensor_data_test"
    DB_HOST = "localhost"  # Connect to local machine 
    DB_PORT = "5433"       # Test DB exposed on different port

print(f"Running in {DB_ENV} mode. Data will be saved to {DB_NAME}.{TABLE_NAME}")

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

# Database connection string
try:
    # Use Docker service names for host when running in container
    db_connection_string = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    print(f"Database connection string: {db_connection_string}")

    # Setup the database connection
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    print(f"Connected to PostgreSQL database: {DB_NAME} on {DB_HOST}:{DB_PORT}")

    # Create the database if it doesn't exist
    # This needs to be run as a separate connection to the postgres database
    if DB_ENV == "TESTING":
        try:
            # Connect to default postgres database
            postgres_conn = psycopg2.connect(
                dbname="postgres",
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                host='localhost',
                port='5432'
            )
            postgres_conn.autocommit = True
            
            with postgres_conn.cursor() as cursor:
                # Check if database exists
                cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
                exists = cursor.fetchone()
                
                if not exists:
                    print(f"Creating test database: {DB_NAME}")
                    cursor.execute(f"CREATE DATABASE {DB_NAME}")
                    
            postgres_conn.close()
        except Exception as e:
            print(f"Could not create test database: {e}")
except Exception as e:
    print(f"Failed to connect to database: {e}")
    exit(1)

# Create a table if it doesn't exist
try:
    with conn.cursor() as cursor:
        # First, check if the table exists and what columns it has
        cursor.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{TABLE_NAME}'
        """)
        columns = cursor.fetchall()
        print(f"Existing columns in {TABLE_NAME}: {columns}")
        
        if not columns:
            # Create the table if it doesn't exist
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    id SERIAL PRIMARY KEY,
                    temperature FLOAT NOT NULL,
                    humidity FLOAT NOT NULL,
                    light FLOAT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print(f"Table '{TABLE_NAME}' created with columns: id, temperature, humidity, light, timestamp")
        else:
            print(f"Table '{TABLE_NAME}' already exists with columns: {columns}")
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

# Add these variables before the while loop to track previous values
prev_temperature = None
prev_light = None
prev_humidity = None
last_change_time = time.time()

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
                # Direct calibration based on known points
                temperature_celsius = round((temperature_raw * 40), 1)  # ~20°C at 0.4976
                
                # Thermistor calculationt
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
            
        # Check for significant changes in sensor values
        current_time = time.time()
        if (prev_temperature is not None and prev_light is not None and 
            prev_humidity is not None and current_time - last_change_time >= 5):
            
            # Calculate percentage changes
            if temperature_celsius is not None and prev_temperature > 0:
                temp_change_pct = (temperature_celsius - prev_temperature) / prev_temperature * 100
            else:
                temp_change_pct = 0
                
            if light_raw is not None and prev_light > 0:
                light_change_pct = (light_raw - prev_light) / prev_light * 100
            else:
                light_change_pct = 0
                
            if humidity_raw is not None and prev_humidity > 0:
                humidity_change_pct = (humidity_raw - prev_humidity) / prev_humidity * 100
            else:
                humidity_change_pct = 0
            
            # Turn on LED if any value rises by more than 2%
            if temp_change_pct > 2 or light_change_pct > 2 or humidity_change_pct > 2:
                board.digital[2].write(1)  # Turn on LED
                print(f"ALERT: Significant rise detected! Temp: {temp_change_pct:.1f}%, Light: {light_change_pct:.1f}%, Humidity: {humidity_change_pct:.1f}%")
            else:
                board.digital[2].write(0)  # Turn off LED
            
            # Update last change check time
            last_change_time = current_time
        
        # Print environment and readings
        print(f"[{DB_ENV}] Temperature: {temperature_celsius}°C | Light: {light_percent}% ({light_category}) | Humidity: {humidity_raw}")
        
        # Update previous values for next comparison
        prev_temperature = temperature_celsius
        prev_light = light_raw
        prev_humidity = humidity_raw
        
        # Insert all climate data into the appropriate database table
        if temperature_celsius is not None and light_raw is not None and humidity_raw is not None:
            with conn.cursor() as cursor:
                cursor.execute(f"""
                    INSERT INTO {TABLE_NAME} (temperature, humidity, light) 
                    VALUES (%s, %s, %s)
                """, (temperature_celsius, humidity_raw, light_raw))
                conn.commit()
                print(f"Data inserted into {DB_ENV} database")
        else:
            print("Data not inserted into database due to missing values")

        sleep_time = 3  # seconds
        time.sleep(sleep_time)

    except KeyboardInterrupt:
        # Turn off LED and close connections before exiting
        board.digital[2].write(0)
        conn.close()
        print(f"Exiting {DB_ENV} mode...")
        break
    except Exception as e:
        print(f"Error: {e}")
        print(f"Type: {type(e)}")
        conn.close()
        break

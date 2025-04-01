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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                id SERIAL PRIMARY KEY,
                temprature INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("Table 'sensor_data' is ready")
except Exception as e:
    print(f"Failed to create table: {e}")
    exit(1)

# Read data from arduino and add to database
while True:
    try:
        # Read data from Arduino (example: analog pin A0)
        print("Reading data from Arduino...")
        analog_value = board.analog[0].read()
        if analog_value is not None:
            analog_value = int(analog_value * 1023)  # Scale to 0-1023

            # Insert data into PostgreSQL database
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO sensor_data (value) VALUES (%s)", (analog_value,))
                conn.commit()
                print(f"Inserted value: {analog_value} into database")
        time.sleep(10) 


    except KeyboardInterrupt:
        print("Exiting...")
        break
    except Exception as e:
        print(f"Error: {e}")
        break

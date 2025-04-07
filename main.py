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


# Get environment variables
try:
    load_dotenv()

    ARDUINO_PORT = os.getenv('ARDUINO_PORT', 'COM6')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'password1!')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'postgres')
except Exception as e:
    st.error(f"Error loading environment variables: {e}")
    raise

# Connect to PostgreSQL database
try:
    conn = psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host='localhost',
        port='5432'
    )
    db = conn.cursor()
except Exception as e:
    st.error(f"Error connecting to PostgreSQL: {e}")
    raise

# Initialize Arduino board
try:
    board = pyfirmata.Arduino(ARDUINO_PORT)
    it = pyfirmata.util.Iterator(board)
    it.start()
except Exception as e:
    st.error(f"Error initializing Arduino: {e}")
    raise

# Define pin numbers
SOIL_MOISTURE_PIN = 0
AIR_TEMP_PIN = 1
AIR_HUMIDITY_PIN = 2
AIR_LIGHT_PIN = 3

# Setup pins
board.analog[SOIL_MOISTURE_PIN].enable_reporting()
board.analog[AIR_TEMP_PIN].enable_reporting()
board.analog[AIR_HUMIDITY_PIN].enable_reporting()
board.analog[AIR_LIGHT_PIN].enable_reporting()

# Setup Thresholds
SOIL_MOISTURE_THRESHOLD = 0.5
AIR_TEMP_THRESHOLD = 25.0
AIR_HUMIDITY_THRESHOLD = 60.0
AIR_LIGHT_THRESHOLD = 300.0

def calculate_air_humidity(ah_raw_value):
    if ah_raw_value is None:
        return None
    air_value = 1023 - ah_raw_value
    water_value = 1023 - air_value

    if air_value == water_value
        percentage = 0
    else:
        contrained = max(water_value, min(air_value, ah_raw_value))
        percentage = round(100.((contrained - water_value) * 100 / (air_value - water_value)), 1)

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
        sm_raw_value = 1023 - sm_raw_value
        sm_percentage = round((sm_raw_value / 1023) * 100, 1)
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
    
    

            


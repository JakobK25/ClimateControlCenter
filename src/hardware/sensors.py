import time
from src.utils.calculations import calculate_temperature, calculate_light
from src.db.models import insert_sensor_data

def read_sensor_data(board):
    """Read raw data from Arduino sensors."""
    return {
        'temperature_raw': board.analog[0].read(),
        'light_raw': board.analog[1].read(),
        'humidity_raw': board.analog[2].read(),
    }

def process_sensor_data(raw_data, prev_values, board, conn=None, config=None):
    """Process raw sensor data into human-readable values and check for significant changes."""
    # Extract raw values
    temperature_raw = raw_data['temperature_raw']
    light_raw = raw_data['light_raw']
    humidity_raw = raw_data['humidity_raw']
    
    # Process temperature data
    temperature_data = calculate_temperature(temperature_raw)
    temperature_celsius = temperature_data.get('linear_celsius')
    
    # Process light data
    light_data = calculate_light(light_raw)
    light_percent = light_data.get('percent')
    light_category = light_data.get('category')
    
    # Check for significant changes
    current_time = time.time()
    changes = {}
    
    if (prev_values['temperature'] is not None and 
        prev_values['light'] is not None and 
        prev_values['humidity'] is not None and 
        current_time - prev_values['last_change_time'] >= 5):
        
        # Calculate percentage changes
        if temperature_celsius is not None and prev_values['temperature'] > 0:
            temp_change_pct = (temperature_celsius - prev_values['temperature']) / prev_values['temperature'] * 100
        else:
            temp_change_pct = 0
            
        if light_raw is not None and prev_values['light'] > 0:
            light_change_pct = (light_raw - prev_values['light']) / prev_values['light'] * 100
        else:
            light_change_pct = 0
            
        if humidity_raw is not None and prev_values['humidity'] > 0:
            humidity_change_pct = (humidity_raw - prev_values['humidity']) / prev_values['humidity'] * 100
        else:
            humidity_change_pct = 0
        
        changes = {
            'temp_change_pct': temp_change_pct,
            'light_change_pct': light_change_pct,
            'humidity_change_pct': humidity_change_pct
        }
        
        # Turn on LED if any value rises by more than 2%
        if temp_change_pct > 2 or light_change_pct > 2 or humidity_change_pct > 2:
            board.digital[2].write(1)  # Turn on LED
            print(f"ALERT: Significant rise detected! Temp: {temp_change_pct:.1f}%, Light: {light_change_pct:.1f}%, Humidity: {humidity_change_pct:.1f}%")
        else:
            board.digital[2].write(0)  # Turn off LED
        
        # Update last change check time
        prev_values['last_change_time'] = current_time
    
    # Print environment and readings
    if config:
        print(f"[{config['DB_ENV']}] Temperature: {temperature_celsius}°C | Light: {light_percent}% ({light_category}) | Humidity: {humidity_raw}")
    
    # Insert data into database if available
    if conn and config and temperature_celsius is not None and light_raw is not None and humidity_raw is not None:
        insert_sensor_data(conn, config['TABLE_NAME'], temperature_celsius, humidity_raw, light_raw)
    
    # Update previous values
    new_prev_values = {
        'temperature': temperature_celsius,
        'light': light_raw,
        'humidity': humidity_raw,
        'last_change_time': prev_values['last_change_time']
    }
    
    # Prepare processed data for return
    processed_data = {
        'temperature': temperature_celsius,
        'light_percent': light_percent,
        'light_category': light_category,
        'humidity': humidity_raw,
        'raw_data': raw_data,
        'temperature_data': temperature_data,
        'changes': changes
    }
    
    return processed_data, new_prev_values
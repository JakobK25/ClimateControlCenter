import math

def calculate_temperature(temperature_raw):
    """Calculate human-readable temperature from raw sensor data."""
    result = {
        'raw': temperature_raw,
        'linear_celsius': None,
        'thermistor_celsius': None,
        'resistance': None
    }
    
    if temperature_raw is None:
        return result
    
    try:
        # Direct calibration based on known points
        result['linear_celsius'] = round((temperature_raw * 40), 1)  # ~20°C at 0.4976
        
        # Thermistor calculation
        if temperature_raw > 0:  # Prevent division by zero
            resistance = 10000 * ((1 - temperature_raw) / temperature_raw)
            result['resistance'] = resistance
            
            # B-parameter equation with adjusted constants
            B_constant = 4275
            T0 = 298.15       # 25°C in Kelvin
            R0 = 100000       # 100KΩ at 25°C
            
            # Calculate temperature in Kelvin
            temperature_kelvin = 1 / ((1 / T0) + (1 / B_constant) * math.log(resistance / R0))
            # Convert to Celsius
            result['thermistor_celsius'] = round(temperature_kelvin - 273.15, 1)
            
            # Print diagnostic info
            print(f"Raw: {temperature_raw}, Resistance: {resistance:.1f}Ω")
            print(f"Linear model: {result['linear_celsius']}°C, Thermistor model: {result['thermistor_celsius']}°C")
        else:
            print(f"Raw: {temperature_raw} (invalid reading)")
    
    except (ValueError, ZeroDivisionError, TypeError) as e:
        print(f"Temperature calculation error: {e}")
    
    return result

def calculate_light(light_raw):
    """Calculate human-readable light values from raw sensor data."""
    result = {
        'raw': light_raw,
        'percent': None,
        'category': "Unknown"
    }
    
    if light_raw is None:
        return result
    
    # Convert to percentage (0-100%)
    result['percent'] = round(light_raw * 100, 1)
    
    # Convert to descriptive category
    if light_raw < 0.1:
        result['category'] = "Very dark"
    elif light_raw < 0.3:
        result['category'] = "Dark"
    elif light_raw < 0.5:
        result['category'] = "Moderate light"
    elif light_raw < 0.8:
        result['category'] = "Bright"
    else:
        result['category'] = "Very bright"
    
    return result
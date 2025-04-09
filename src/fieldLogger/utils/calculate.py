import math
import streamlit as st

class Calculate:
    def __init__(self, sensor_values):
        # Initialize with sensor values
        self.air_temperature = sensor_values.get('air_temperature')
        self.air_light = sensor_values.get('air_light')
        self.soil_humidity = sensor_values.get('soil_humidity')
    
    def calculate_soil_humidity(self):
        """Calculate soil humidity percentage and status."""
        if self.soil_humidity is None:
            return {'percentage': None, 'status': None}
        
        try:
            # Calibration values from actual sensor readings
            WET_VALUE = 0.4900   # Value when submerged in water
            DRY_VALUE = 0.6600   # Value when in regular air
            
            # Calculate moisture percentage (0% = dry, 100% = wet)
            # Constrain reading to calibration range
            constrained_value = max(WET_VALUE, min(DRY_VALUE, self.soil_humidity))
            
            # Map the value from sensor range to 0-100% range
            percentage = round(((DRY_VALUE - constrained_value) / (DRY_VALUE - WET_VALUE)) * 100, 1)
            
            # Ensure percentage is within valid range
            percentage = max(0, min(100, percentage))
            
        except Exception as e:
            st.error(f"Error calculating soil humidity: {e}")
            return {'percentage': None, 'status': None}
        
        # Determine status based on percentage
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
    
    def calculate_air_temp(self):
        """Calculate air temperature in Celsius."""
        if self.air_temperature is None:
            return {'temperature': None, 'status': None}

        try:
            SERIES_RESISTOR = 10000
            BETA_COEFFICIENT = 3950
            NOMINAL_TEMPERATURE = 25
            NOMINAL_RESISTANCE = 10000

            if self.air_temperature == 0:
                resistance = float('inf')
            elif self.air_temperature == 1:
                resistance = 0
            else:
                resistance = SERIES_RESISTOR * (1 - self.air_temperature) / self.air_temperature

            steinhart = resistance / NOMINAL_RESISTANCE
            steinhart = math.log(steinhart)
            steinhart /= BETA_COEFFICIENT
            steinhart += 1.0 / (NOMINAL_TEMPERATURE + 273.15)
            steinhart = 1.0 / steinhart
            celcius = round(steinhart - 273.15, 1)
            corrected_celcius = celcius - 5
            
        except Exception as e:
            st.error(f"Error calculating air temperature: {e}")
            return {'temperature': None, 'status': None}
        
        return {
            'temperature': corrected_celcius
        }
    
    def calculate_air_light(self):
        """Calculate light level percentage and status."""
        if self.air_light is None:
            return {'light': None, 'status': None}
        
        try:
            # Direct translation: raw value * 100 = percentage
            light_percentage = round(self.air_light * 100, 1)
            
            # Ensure percentage is within valid range
            light_percentage = max(0, min(100, light_percentage))
            
        except Exception as e:
            st.error(f"Error calculating light level: {e}")
            return {'light': None, 'status': None}
        
        # Determine status based on light percentage
        if light_percentage < 20:
            status = "Very Dark"
        elif light_percentage < 40:
            status = "Dark"
        elif light_percentage < 60:
            status = "Moderate"
        elif light_percentage < 80:
            status = "Bright"
        else:
            status = "Very Bright"
        
        return {
            'light': light_percentage, 
            'status': status
        }


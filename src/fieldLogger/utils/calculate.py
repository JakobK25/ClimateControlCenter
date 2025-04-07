from config import config
import math


class Calculate:
    def calculate_air_humidity(self)
        if self.airtemperature is None:
            return {'percentage': None, 'status': None}
        
        try:
            DRY_VALUE = 0.8200
            WET_VALUE = 0.4100

            constrained_value = max(min(self.airtemperature, DRY_VALUE), WET_VALUE)
            percentage = (DRY_VALUE - constrained_value) / (DRY_VALUE - WET_VALUE) * 100
            percentage = max(0, min(percentage, 100))  # Ensure percentage is between 0 and 100

        except Exception as e:
            print(f"Error calculating air humidity: {e}")
            percentage = {'percentage': None, 'status': None}

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
    
    def calculate_soil_humidity(self):
        if self.soil_humidity is None:
            return {'percentage': None, 'status': None}
        
        try:
            DRY_VALUE = 0.6600
            WET_VALUE = 0.4900

            constrained_value = max(min(self.soil_humidity, DRY_VALUE), WET_VALUE)
            percentage = (DRY_VALUE - constrained_value) / (DRY_VALUE - WET_VALUE) * 100
            percentage = max(0, min(percentage, 100))  # Ensure percentage is between 0 and 100

        except Exception as e:
            print(f"Error calculating soil humidity: {e}")
            percentage = {'percentage': None, 'status': None}

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
        if self.airtemprature is None:
            return {'temperature': None, 'status': None}

        try:
            SERIES_RESISTOR = 10000.0  # Resistance of the thermistor at 25 degrees Celsius
            BETA_COEFFICIENT = 3950.0  # Beta coefficient of the thermistor
            NOMINAL_TEMPERATURE = 298.15  # Nominal temperature in Kelvin (25 degrees Celsius)
            NOMINAL_RESISTANCE = 10000.0  # Resistance at nominal temperature

            if self.airtemperature == 0
                resistance = float('inf')
            elif self.airtemperature == 1:
                resistance = 0
            else:
                resistance = SERIES_RESISTOR * (1023.0 / self.airtemperature - 1.0)

            steinhart = resistance / NOMINAL_RESISTANCE
            steinhart = math.log(steinhart) / BETA_COEFFICIENT
            steinhart += 1.0 / NOMINAL_TEMPERATURE
            steinhart = 1.0 / steinhart
            celcius = steinhart - 273.15  # Convert to Celsius
            celcius = round(celcius, 2)  # Round to 2 decimal places

        except Exception as e:
            print(f"Error calculating air temperature: {e}")
            celcius = {'temperature': None, 'status': None}
        
        return {
            'temperature': celcius, 
        }
    
    def calculate_air_wind(self):
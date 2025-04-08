from .config import Config
from .database import init_db_connection, save_sensor_data
from .arduino import ArduinoHandler
from .utils.calculate import Calculate
from .ui.dashboard import main as dashboard_ui
import streamlit as st
import time

class FieldLoggerApp:
    def __init__(self):
        """Initialize the Field Logger App."""
        self.config = Config()
        self.db_conn, self.db_cursor = init_db_connection(self.config)
        self.arduino = ArduinoHandler(self.config)
        self.readings = {}
        
    def read_sensors(self):
        """Read sensor values from Arduino."""
        try:
            return self.arduino.read_sensors()
        except Exception as e:
            st.error(f"Failed to read sensors: {e}")
            # Return default values as fallback
            return {
                "air_temperature": 0.5,  # Default value
                "air_wind": 0.2,
                "air_light": 0.5,
                "soil_humidity": 0.5
            }
    
    def process_readings(self):
        """Process raw sensor readings into meaningful values."""
        # Get raw sensor values
        sensor_values = self.read_sensors()
        
        # Create calculator instance
        calculator = Calculate(sensor_values)
        
        # Calculate sensor readings
        self.readings = {
            'soil_humidity': calculator.calculate_soil_humidity(),
            'air_temperature': calculator.calculate_air_temp(),
            'air_wind': calculator.calculate_air_wind(),
            'air_light': calculator.calculate_air_light()
        }
        
        return self.readings
    
    def save_to_database(self):
        """Save current readings to database."""
        success, message = save_sensor_data(self.db_conn, self.db_cursor, self.readings)
        return success, message
    
    def run(self):
        """Main application loop."""
        try:
            # Process sensor readings
            self.process_readings()
            
            # Save to database
            db_success, db_message = self.save_to_database()
            if db_success:
                st.sidebar.success(db_message)
            else:
                st.sidebar.warning(db_message)
            
            # Display UI
            dashboard_ui(self)
            
        except Exception as e:
            st.error(f"Error in application: {e}")
            import traceback
            st.code(traceback.format_exc())
        
    def cleanup(self):
        """Clean up resources before exiting."""
        try:
            # First close Arduino
            if hasattr(self, 'arduino'):
                self.arduino.close()
            
            # Then close database connections
            if hasattr(self, 'db_cursor') and self.db_cursor:
                self.db_cursor.close()
                
            if hasattr(self, 'db_conn') and self.db_conn:
                self.db_conn.close()
        except Exception as e:
            print(f"Error during cleanup: {e}")
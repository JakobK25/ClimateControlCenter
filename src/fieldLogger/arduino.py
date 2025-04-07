import pyfirmata
from pyfirmata import util
import time
import streamlit as st

class ArduinoHandler:
    def __init__(self, config):
        self.config = config
        self.board = None
        self.initialize_board()
    
    def initialize_board(self):
        """Initialize Arduino board and setup pins."""
        try:
            self.board = pyfirmata.Arduino(self.config.ARDUINO_PORT)
            it = pyfirmata.util.Iterator(self.board)
            it.start()
            
            # Setup pins from config
            pins = self.config.get_sensor_pins()
            for pin_name, pin_number in pins.items():
                if pin_number is not None:
                    self.board.analog[int(pin_number)].enable_reporting()
                    
            # Wait for pins to be ready
            time.sleep(0.1)
        except Exception as e:
            st.error(f"Error initializing Arduino: {e}")
            raise Exception(f"Error initializing Arduino: {e}")
    
    def read_sensors(self):
        """Read all sensor values."""
        if not self.board:
            raise Exception("Arduino board not initialized")
            
        pins = self.config.get_sensor_pins()
        sensor_values = {}
        
        for name, pin in pins.items():
            if pin is not None:
                sensor_values[name] = self.board.analog[int(pin)].read()
                
        return sensor_values
    
    def close(self):
        """Close the board connection."""
        if self.board:
            self.board.exit()
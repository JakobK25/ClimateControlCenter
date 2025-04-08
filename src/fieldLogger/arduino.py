import pyfirmata
from pyfirmata import util
import time
import streamlit as st
import serial
import atexit

class ArduinoHandler:
    # Class variable to track instances
    _instances = []
    
    def __init__(self, config):
        self.config = config
        self.board = None
        
        # Add this instance to the class instances list
        ArduinoHandler._instances.append(self)
        
        # Register a cleanup handler
        atexit.register(self.close)
        
        # Initialize the board
        self.initialize_board()
    
    def initialize_board(self):
        """Initialize Arduino board and setup pins."""
        # First, try to close any existing connections to this port
        try:
            # Force close any existing connection to this port
            ArduinoHandler._force_close_port(self.config.ARDUINO_PORT)
            time.sleep(0.5)  # Wait for port to release
            
            # Now connect to Arduino
            self.board = pyfirmata.Arduino(self.config.ARDUINO_PORT)
            it = pyfirmata.util.Iterator(self.board)
            it.start()
            
            # Setup pins from config
            pins = self.config.get_sensor_pins()
            for pin_name, pin_number in pins.items():
                if pin_number is not None:
                    self.board.analog[int(pin_number)].enable_reporting()
                    
            # Wait for pins to be ready
            time.sleep(0.2)
        except Exception as e:
            st.error(f"Error initializing Arduino: {e}")
            raise Exception(f"Error initializing Arduino: {e}")
    
    @staticmethod
    def _force_close_port(port_name):
        """Force close a COM port"""
        try:
            # Try to open and immediately close the port to release it
            ser = serial.Serial(port_name)
            ser.close()
        except:
            # If it fails, the port might already be closed or unavailable
            pass
    
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
        if hasattr(self, 'board') and self.board:
            try:
                self.board.exit()
                self.board = None
            except:
                pass

    @classmethod
    def cleanup_all(cls):
        """Class method to clean up all instances."""
        for instance in cls._instances:
            instance.close()
        cls._instances = []
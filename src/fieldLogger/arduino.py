import pyfirmata
from pyfirmata import util
import time
import streamlit as st
import serial

class ArduinoHandler:
    def __init__(self, config):
        self.config = config
        
        # Initialize or get the board from session state
        if 'arduino_board' not in st.session_state:
            # First run - need to initialize
            self.initialize_board()
        else:
            # Rerun - use existing board if it's valid
            self.board = st.session_state.arduino_board
            if self.board is None:
                # If board was closed or is invalid, reinitialize
                self.initialize_board()
    
    def initialize_board(self):
        """Initialize Arduino board and setup pins."""
        try:
            # Try to close any existing connection first
            self.close()
            
            # Small delay to ensure port is released
            time.sleep(0.2)
            
            # Try to connect
            self.board = pyfirmata.Arduino(self.config.ARDUINO_PORT)
            st.session_state.arduino_board = self.board
            
            # Start iterator
            it = pyfirmata.util.Iterator(self.board)
            it.start()
            
            # Setup pins from config
            pins = self.config.get_sensor_pins()
            for pin_name, pin_number in pins.items():
                if pin_number is not None:
                    self.board.analog[int(pin_number)].enable_reporting()
                    
            # Wait for pins to be ready
            time.sleep(0.2)
            st.sidebar.success(f"Connected to Arduino on {self.config.ARDUINO_PORT}")
            
        except Exception as e:
            st.sidebar.error(f"Error initializing Arduino: {e}")
            self.board = None
            st.session_state.arduino_board = None
            raise Exception(f"Error initializing Arduino: {e}")
    
    def read_sensors(self):
        """Read all sensor values."""
        if self.board is None:
            # Try to initialize again
            self.initialize_board()
            if self.board is None:
                raise Exception("Arduino board not initialized")
            
        pins = self.config.get_sensor_pins()
        sensor_values = {}
        
        try:
            for name, pin in pins.items():
                if pin is not None:
                    sensor_values[name] = self.board.analog[int(pin)].read()
        except Exception as e:
            # If reading fails, try to reconnect once
            st.sidebar.warning(f"Sensor reading error: {e}. Attempting to reconnect...")
            self.initialize_board()
            
            # Try reading again after reconnection
            for name, pin in pins.items():
                if pin is not None:
                    sensor_values[name] = self.board.analog[int(pin)].read()
                
        return sensor_values
    
    def close(self):
        """Close the board connection."""
        if hasattr(self, 'board') and self.board is not None:
            try:
                self.board.exit()
            except:
                pass
            self.board = None
            
        # Also try to forcibly close the COM port
        try:
            ser = serial.Serial(self.config.ARDUINO_PORT)
            ser.close()
        except:
            pass
            
        # Clear from session state
        if 'arduino_board' in st.session_state:
            st.session_state.arduino_board = None
import pyfirmata
from pyfirmata import util
import time
import streamlit as st
import serial

class ArduinoHandler:
    def __init__(self, config):
        self.config = config
        self.board = None
        
        # Store connection in session state to reuse between reruns
        if 'arduino_initialized' not in st.session_state:
            st.session_state.arduino_initialized = False
            self.initialize_board()
        else:
            # Connection already established in session state
            st.sidebar.success("Using existing Arduino connection")
    
    def initialize_board(self):
        """Initialize Arduino board and setup pins."""
        try:
            # Close any existing connections to this port first
            try:
                # Force close the port in case it's stuck open
                ser = serial.Serial(self.config.ARDUINO_PORT)
                ser.close()
                time.sleep(0.5)  # Give the port time to close
            except:
                # Port might already be closed, that's okay
                pass
                
            # Now try to connect
            self.board = pyfirmata.Arduino(self.config.ARDUINO_PORT)
            it = pyfirmata.util.Iterator(self.board)
            it.start()
            
            # Setup pins from config
            pins = self.config.get_sensor_pins()
            for pin_name, pin_number in pins.items():
                if pin_number is not None:
                    self.board.analog[int(pin_number)].enable_reporting()
                    
            # Wait for pins to be ready
            time.sleep(0.5)
            
            # Store board in session state
            st.session_state.arduino_board = self.board
            st.session_state.arduino_initialized = True
            
            st.sidebar.success(f"Connected to Arduino on {self.config.ARDUINO_PORT}")
            
        except Exception as e:
            st.error(f"Error initializing Arduino: {e}")
            
            # Provide troubleshooting information
            st.sidebar.error("Arduino Connection Failed")
            st.sidebar.info("""
            Troubleshooting:
            1. Check if Arduino IDE is open and close it
            2. Try unplugging and reconnecting the Arduino
            3. Verify COM6 is the correct port (check Device Manager)
            4. Try running as administrator
            """)
            
            raise Exception(f"Error initializing Arduino: {e}")
    
    def read_sensors(self):
        """Read all sensor values."""
        # Use the board from session state if available
        board = getattr(st.session_state, 'arduino_board', self.board)
        
        if not board:
            raise Exception("Arduino board not initialized")
            
        pins = self.config.get_sensor_pins()
        sensor_values = {}
        
        for name, pin in pins.items():
            if pin is not None:
                sensor_values[name] = board.analog[int(pin)].read()
                
        return sensor_values
    
    def close(self):
        """Close the board connection."""
        # Only close if we need to exit completely, not on rerun
        if 'arduino_board' in st.session_state and st.session_state.arduino_board:
            try:
                st.session_state.arduino_board.exit()
                st.session_state.arduino_board = None
                st.session_state.arduino_initialized = False
            except:
                pass
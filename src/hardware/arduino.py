import time
import pyfirmata

def setup_arduino(port):
    """Initialize the Arduino board and configure pins."""
    try:
        # Connect to the Arduino board
        board = pyfirmata.Arduino(port)
        print(f"Connected to Arduino on port: {port}")
        
        # Start the iterator to handle incoming data
        it = pyfirmata.util.Iterator(board)
        it.start()
        time.sleep(1)  # Give time for the board to initialize
        
        # Setup input pins
        board.analog[0].enable_reporting()  # Temperature sensor (analog pin A0)
        board.analog[1].enable_reporting()  # Light sensor (analog pin A1)
        board.analog[2].enable_reporting()  # Humidity sensor (analog pin A2)
        
        # Setup output pins
        board.digital[2].mode = pyfirmata.OUTPUT  # LED (digital pin 2)
        
        return board
    
    except Exception as e:
        print(f"Failed to connect to Arduino: {e}")
        exit(1)
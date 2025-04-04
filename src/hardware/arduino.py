import time
import pyfirmata
import logging

logger = logging.getLogger("ClimateControl.Arduino")

def setup_arduino(port):
    """Initialize the Arduino board and configure pins."""
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            # Connect to the Arduino board
            board = pyfirmata.Arduino(port)
            logger.info(f"Connected to Arduino on port: {port}")
            
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
            
            # Test LED
            board.digital[2].write(1)
            time.sleep(0.5)
            board.digital[2].write(0)
            
            logger.info("Arduino initialization complete")
            return board
        
        except Exception as e:
            retry_count += 1
            logger.error(f"Failed to connect to Arduino (attempt {retry_count}/{max_retries}): {e}")
            
            if retry_count < max_retries:
                logger.info(f"Retrying in 5 seconds...")
                time.sleep(5)
            else:
                logger.critical("Failed to connect to Arduino after multiple attempts")
                raise ConnectionError(f"Could not connect to Arduino on port {port}: {e}")
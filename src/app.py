import time

# Use absolute imports here
from src.config.settings import get_environment
from src.hardware.arduino import setup_arduino
from src.db.connection import setup_database
from src.db.models import setup_tables
from src.hardware.sensors import read_sensor_data, process_sensor_data
from src.ui.dashboard import setup_dashboard, update_dashboard

def main():
    """Main entry point for the Climate Control Center application."""
    print("=== Climate Control Center ===")
    
    # Get environment settings
    config = get_environment()
    
    # Setup hardware
    board = setup_arduino(config['ARDUINO_PORT'])
    
    # Setup database
    conn = setup_database(config)
    
    # Setup tables
    setup_tables(conn, config['TABLE_NAME'])
    
    # Setup dashboard
    containers = setup_dashboard()
    
    # Setup sensor tracking variables
    prev_values = {
        'temperature': None,
        'light': None,
        'humidity': None,
        'last_change_time': time.time()
    }
    
    # Main loop
    try:
        while True:
            # Read sensor data
            raw_data = read_sensor_data(board)
            
            # Process sensor readings
            processed_data, prev_values = process_sensor_data(raw_data, prev_values, board)
            
            # Update the dashboard
            update_dashboard(containers, config, processed_data)
            
            # Sleep to avoid overwhelming the system
            time.sleep(15)
    
    except KeyboardInterrupt:
        # Clean shutdown
        if board:
            board.digital[2].write(0)  # Turn off LED
        if conn:
            conn.close()
        print(f"Exiting {config['DB_ENV']} mode...")
    except Exception as e:
        print(f"Error: {e}")
        print(f"Type: {type(e)}")
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
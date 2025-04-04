import os
from dotenv import load_dotenv

def get_environment():
    """Load and configure environment settings."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Get environment variables
    arduino_port = os.getenv('ARDUINO_PORT', 'COM3')
    postgres_user = os.getenv('POSTGRES_USER', 'postgres')
    postgres_password = os.getenv('POSTGRES_PASSWORD', 'password1!')
    postgres_db = os.getenv('POSTGRES_DB', 'postgres')
    
    # Ask user for environment selection
    env_selection = input("Run in production or testing mode? (p/t): ").lower()
    
    # Set database configuration based on selection
    if env_selection.startswith('p'):
        db_env = "PRODUCTION"
        db_name = postgres_db
        table_name = "sensor_data"
        db_host = "localhost"  # Connect to local machine
        db_port = "5432"       # Standard PostgreSQL port
    else:
        db_env = "TESTING"
        db_name = f"{postgres_db}_test"
        table_name = "sensor_data_test"
        db_host = "localhost"  # Connect to local machine 
        db_port = "5433"       # Test DB exposed on different port
    
    print(f"Running in {db_env} mode. Data will be saved to {db_name}.{table_name}")
    
    # Return config as a dictionary
    return {
        'ARDUINO_PORT': arduino_port,
        'POSTGRES_USER': postgres_user,
        'POSTGRES_PASSWORD': postgres_password,
        'POSTGRES_DB': postgres_db,
        'DB_ENV': db_env,
        'DB_NAME': db_name,
        'TABLE_NAME': table_name,
        'DB_HOST': db_host,
        'DB_PORT': db_port,
    }
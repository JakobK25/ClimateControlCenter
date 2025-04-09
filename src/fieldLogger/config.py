from dotenv import load_dotenv
import os
import psycopg2

# Load environment variables from .env file
class Config:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        # Database configuration
        self.POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
        self.POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password1!")
        self.POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")
        self.POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
        self.POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

        # Arduino configuration
        self.ARDUINO_PORT = os.getenv("ARDUINO_PORT", "COM6")

        # Sensor configuration
        self.AIR_TEMPERATURE_SENSOR = int(os.getenv("AIR_TEMPERATURE_SENSOR", 1))
        self.AIR_LIGHT_SENSOR = int(os.getenv("AIR_LIGHT_SENSOR", 3))
        self.SOIL_HUMIDITY_SENSOR = int(os.getenv("SOIL_HUMIDITY_SENSOR", 0))

        # Application configuration
        self.REFRESH_RATE = int(os.getenv("REFRESH_RATE", 5))  # Default to 5 seconds if not set

    def get_db_string(self):
        """Returns the database connection string."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    def get_db_params(self):
        """Returns database connection parameters as a dictionary."""
        return {
            "dbname": self.POSTGRES_DB,
            "user": self.POSTGRES_USER,
            "password": self.POSTGRES_PASSWORD,
            "host": self.POSTGRES_HOST,
            "port": self.POSTGRES_PORT
        }

    def get_sensor_pins(self):
        """Returns a dictionary of sensor pins."""
        return {
            "air_temperature": self.AIR_TEMPERATURE_SENSOR,
            "air_light": self.AIR_LIGHT_SENSOR,
            "soil_humidity": self.SOIL_HUMIDITY_SENSOR
        }

def init_db_connection(config):
    # Connect to PostgreSQL database
    try:
        conn = psycopg2.connect(
            dbname=config.POSTGRES_DB,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT
        )
        conn.autocommit = True
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        raise



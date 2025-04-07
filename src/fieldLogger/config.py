from dotenv import load_dotenv
import os

# Load environment variables from .env file

class Config:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        # Database configuration
        self.POSTGRES_USER = os.getenv("POSTGRES_USER")
        self.POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
        self.POSTGRES_DB = os.getenv("POSTGRES_DB")

        # Arduino configuration
        self.ARDUINO_PORT = os.getenv("ARDUINO_PORT")

        # Sensor configuration
        self.AIR_TEMPERATURE_SENSOR = os.getenv("AIR_TEMPERATURE_SENSOR")
        self.AIR_WIND_SESNOR = os.getenv("AIR_WIND_SENSOR")
        self.AIR_LIGHT_SENSOR = os.getenv("AIR_LIGHT_SENSOR")
        self.SOIL_HUMIDITY_SENSOR = os.getenv("SOIL_HUMIDITY_SENSOR")

        # Application configuration
        self.REFRESH_RATE = int(os.getenv("REFRESH_RATE", 5))  # Default to 5 seconds if not set

    def get_db_string(self):
        """Returns the database connection string."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@localhost:5432/{self.POSTGRES_DB}"

    def get_sensor_pins(self):
        """Returns a list of sensor pins."""
        return {
            "air_temperature": self.AIR_TEMPERATURE_SENSOR,
            "air_wind": self.AIR_WIND_SESNOR,
            "air_light": self.AIR_LIGHT_SENSOR,
            "soil_humidity": self.SOIL_HUMIDITY_SENSOR,
        }
    

    
# Climate Control Center

A comprehensive environmental monitoring system using Arduino sensors and Streamlit dashboard.

## Overview

Climate Control Center is a robust monitoring system that tracks environmental conditions using Arduino sensors. The system collects data from soil moisture, air temperature, humidity, and light sensors, displays real-time readings in a responsive dashboard, and stores historical data in a PostgreSQL database for analysis.

## Features

- **Real-time Monitoring**: View current readings from multiple environmental sensors
- **Data Visualization**: Clear metric displays with status indicators
- **Automatic Refresh**: Data updates every 5 minutes with progress tracking
- **Manual Refresh**: Force data updates with a single click
- **Historical Data**: All readings are stored in a PostgreSQL database
- **Containerized Setup**: Run the entire system with Docker and Docker Compose
- **Calibrated Sensor Readings**: Converts raw sensor data to meaningful values

## Requirements

### Hardware
- Arduino board (connected via USB)
- Soil moisture sensor (analog pin A0)
- Air temperature sensor (analog pin A1)
- Air flow sensor (analog pin A2)
- Light sensor (analog pin A3)

### Software
- Python 3.11+
- PostgreSQL database
- Docker & Docker Compose (optional)

## Installation

### Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/jakobk25/ClimateControlCenter.git
   cd ClimateControlCenter
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv
   # On Windows
   .\.venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** (use the sample below)
   ```
   # [POSTGRES]
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=password1!
   POSTGRES_DB=postgres

   # [ARDUINO]
   ARDUINO_PORT=COM6  # Change to match your Arduino port
   ```

5. **Start the PostgreSQL database**
   ```bash
   # If you have PostgreSQL installed locally, ensure it's running
   # Or use Docker to run just the database:
   docker-compose up postgres
   ```

6. **Run the application**
   ```bash
   streamlit run main.py
   ```

### Docker Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/jakobk25/ClimateControlCenter.git
   cd ClimateControlCenter
   ```

2. **Create a `.env` file** (see above)

3. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the dashboard**
   ```
   http://localhost:8000
   ```

## Usage

1. **Connect your Arduino** with the sensors properly wired:
   - Soil moisture sensor to A0
   - Temperature sensor to A1
   - Humidity sensor to A2
   - Light sensor to A3

2. **Launch the application** using one of the installation methods above

3. **View the dashboard** to see current readings
   - The data will automatically refresh every 5 minutes
   - Use the "Refresh Now" button for immediate updates

4. **Monitor sensor statuses** to track environmental conditions:
   - Soil moisture (Very Dry → Wet)
   - Air temperature (in °C)
   - Air humidity (Very Dry → Wet)
   - Light level (Very Low → Very High)

## Configuration

### Sensor Calibration

The sensors are pre-calibrated with the following values, which you can adjust in the code:

- **Soil Moisture**:
  - Dry value (in air): 0.6600
  - Wet value (in water): 0.4900

- **Temperature**:
  - Uses a 10kΩ thermistor with B=3950

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| POSTGRES_USER | PostgreSQL username | postgres |
| POSTGRES_PASSWORD | PostgreSQL password | password1! |
| POSTGRES_DB | PostgreSQL database name | postgres |
| ARDUINO_PORT | Serial port for Arduino | COM6 |

## Project Structure

```
ClimateControlCenter/
├── main.py                # Main application file
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── Dockerfile             # Docker configuration
├── compose.yml            # Docker Compose configuration
├── LICENSE                # MIT License
└── README.md              # This file
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

### Common Issues

- **Arduino Connection Error**: Verify the correct port is specified in the `.env` file
- **Database Connection Error**: Ensure PostgreSQL is running and credentials are correct
- **Sensor Reading Errors**: Check wiring and calibration values

## Future Improvements

- Add alerts for critical sensor values
- Implement mobile notifications
- Create historical data visualization charts
- Add machine learning to predict environmental trends

---

Developed with ❤️ using Python, Streamlit, and Arduino
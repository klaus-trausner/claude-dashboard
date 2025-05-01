# MQTT Flask Dashboard

This application provides a web-based dashboard for monitoring MQTT data from various sensors. It collects data from an MQTT broker and displays it in real-time through a Flask web application.

## Features

- Real-time MQTT data monitoring
- Dashboard with visualizations
- Historical data tracking
- Current data overview
- Data export capabilities
- Responsive design for desktop and mobile

## Technical Stack

- Backend: Python with Flask
- MQTT Client: Paho MQTT
- Frontend: HTML, CSS, JavaScript
- Visualization: Chart.js
- Styling: Bootstrap 5

## Setup Instructions

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Internet connection for loading external libraries (Bootstrap, Chart.js)

### Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd mqtt-flask-dashboard
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install required packages:
   ```
   pip install flask paho-mqtt
   ```

### Directory Structure

```
mqtt-flask-dashboard/
├── app.py              # Main Flask application
├── templates/          # HTML templates
│   ├── base.html       # Base template with navigation
│   ├── home.html       # Home page
│   ├── dashboard.html  # Dashboard with visualizations
│   ├── current_data.html  # Current sensor readings
│   └── long_time_data.html  # Historical data analysis
├── static/             # Static assets
│   └── css/
│       └── style.css   # Custom CSS
└── README.md           # This file
```

### Configuration

The MQTT connection parameters are configured in `app.py`:

```python
# MQTT Configuration
MQTT_BROKER = "81.7.10.99"
MQTT_PORT = 1883
MQTT_USER = "klaus"
MQTT_PASSWORD = "DHisddS!"
MQTT_TOPICS = [
    "esp32/zisterne",
    "esp32/temperature",
    "esp32/pressure",
    "esp32/humidity",
    "bodenfeuchte",
    "steuerungstemperatur",
    "status",
    "send_settings",
    "ext1/temperature",
    "ext1/humidity",
    "innen",
    "test"
]
```

You can modify these settings to match your MQTT broker configuration.

### Running the Application

1. Make sure your virtual environment is activated.

2. Run the Flask application:
   ```
   python app.py
   ```

3. Access the dashboard in your web browser at:
   ```
   http://localhost:5000/
   ```

## Pages

- **Home**: Welcome page with basic information and connection status
- **Dashboard**: Overview of all sensor data with charts and key metrics
- **Current Data**: Latest readings from all sensors in tabular and card format
- **Long Time Data**: Historical data with filtering options and statistics

## Data Storage

The application stores data in memory while running:

- `current_data`: Contains the latest values for each topic
- `historical_data`: Stores the last 100 values for each topic

For persistent storage, you would need to integrate with a database.

## Security Notes

- The application uses plain text password authentication for MQTT.
- For production use, consider using TLS/SSL for secure MQTT communication.
- Do not expose the dashboard to the public internet without proper authentication
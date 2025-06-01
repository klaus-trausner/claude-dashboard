# MQTT Flask Dashboard

This application provides a web-based dashboard for monitoring MQTT data from various sensors. It collects data from an MQTT broker and displays it in real-time through a Flask web application.

## Features

- Real-time MQTT data monitoring
- Dashboard with visualizations
- Historical data tracking
- Current data overview
- Data export capabilities
- Responsive design for desktop and mobile
- Ability to change device settings via an API endpoint.

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

The project has the following core structure:
```
mqtt-flask-dashboard/
├── app.py              # Main Flask application
├── static/             # Static assets (CSS, JavaScript, images)
│   └── css/
│       └── style.css   # Custom CSS
├── templates/          # HTML templates
│   ├── base.html       # Base template with navigation
│   ├── home.html       # Home page
│   ├── dashboard.html  # Dashboard with visualizations
│   ├── current_data.html  # Current sensor readings
│   └── long_time_data.html  # Historical data analysis
└── README.md           # This file
```
(Note: A virtual environment directory like `venv/` or `.claude/` may also be present if you follow the setup instructions, but it's not part of the core project files.)

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
    "send_settings",  # Topic used by devices to publish their current settings
    "ext1/temperature",
    "ext1/humidity",
    "innen",
    "test"
]
```
The `send_settings` topic is used by devices to publish their current settings to the application. The application listens to this topic to stay updated on device configurations.

The application also uses a separate MQTT topic to send setting changes *to* devices:
```python
# Topic to publish setting changes to
MQTT_PUBLISH_TOPIC_SETTINGS = "changeSetting"
```
This topic is used by the `/api/change_setting` endpoint.

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

## API Endpoints

- **`/api/current_data` (GET)**: Retrieves the most recent data for all MQTT topics.
  Example response:
  ```json
  {
    "esp32/temperature": {"value": "25.5", "timestamp": "YYYY-MM-DD HH:MM:SS"},
    "esp32/humidity": {"value": "60", "timestamp": "YYYY-MM-DD HH:MM:SS"}
  }
  ```
- **`/api/historical_data` (GET)**: Retrieves the last 100 data points for each MQTT topic.
  Example response:
  ```json
  {
    "esp32/temperature": [
      {"value": "25.5", "timestamp": "YYYY-MM-DD HH:MM:SS"},
      {"value": "25.6", "timestamp": "YYYY-MM-DD HH:MM:SS"}
    ]
  }
  ```
- **`/api/topics` (GET)**: Returns a list of all MQTT topics the application is subscribed to.
  Example response:
  ```json
  [
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
- **`/api/change_setting` (POST)**: Allows publishing a setting change to the `MQTT_PUBLISH_TOPIC_SETTINGS` topic.
  - Method: `POST`
  - Parameters (form data):
    - `setting_name` (string): The name or key of the setting to change.
    - `setting_value` (string): The new value for the setting.
  - Action: Publishes a JSON payload `["setting_name", "setting_value"]` to the configured MQTT topic for settings changes.
  - Success Response: HTML snippet `<span class="text-success small ms-2">Saved!</span>`
  - Error Response: HTML snippet `<span class="text-danger small ms-2">Error saving!</span>` or `<span class="text-danger small ms-2">Server error!</span>` with appropriate HTTP status codes.

## Data Storage

The application stores data in memory while running:

- `current_data`: Contains the latest values for each topic
- `historical_data`: Stores the last 100 values for each topic

For persistent storage, you would need to integrate with a database.

## Security Notes

- The application uses plain text password authentication for MQTT.
- For production use, consider using TLS/SSL for secure MQTT communication.
- Do not expose the dashboard to the public internet without proper authentication
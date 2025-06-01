# MQTT Flask Dashboard

This application provides a web-based dashboard for monitoring MQTT data from various sensors. It collects data from an MQTT broker and displays it in real-time through a Flask web application.

## Features

- Real-time MQTT data monitoring
- Dashboard with visualizations
- Historical data tracking
- Current data overview
- Data export capabilities
- Responsive design for desktop and mobile
- User authentication (registration and login) using JWT.
- Ability to change device settings via a protected API endpoint (requires login).

## Technical Stack

- Backend: Python with Flask
  - Flask-SQLAlchemy (Database ORM)
  - Flask-Migrate (Database migrations)
  - Flask-JWT-Extended (JWT Authentication)
  - bcrypt (Password hashing)
- MQTT Client: Paho MQTT
- Database: SQLite (default)
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
   All dependencies are listed in `requirements.txt`.
   ```
   pip install -r requirements.txt
   ```
   This includes: `Flask, paho-mqtt, Flask-SQLAlchemy, Flask-Migrate, bcrypt, Flask-JWT-Extended`, and their dependencies.

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

You can modify these settings to match your MQTT broker configuration. For enhanced security, consider moving MQTT credentials (USER, PASSWORD) to environment variables as well.

### Environment Variables
The application can be configured using the following environment variables:

-   **`DATABASE_URL`**: The SQLAlchemy database connection string.
    -   Default: `sqlite:///./app.db` (a local SQLite file named `app.db` in the project root).
    -   Example for PostgreSQL: `postgresql://user:password@host:port/dbname`
    -   To set for local development (e.g., in bash):
        ```bash
        export DATABASE_URL='sqlite:///./app.db'
        ```

-   **`JWT_SECRET_KEY`**: A secret key for JWT signing. This **must** be a strong, random string in a production environment.
    -   Default: A placeholder key is provided for development (e.g., `'a-very-secure-default-secret-key-CHANGE-ME'`). **Do not use this default in production.**
    -   The application will log a warning if the default key is used.
    -   To set for local development (e.g., in bash):
        ```bash
        export JWT_SECRET_KEY='your-chosen-super-secret-and-random-string'
        ```

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
  - **Requires Authentication**: JWT Bearer token in `Authorization` header.
  - Parameters (form data):
    - `setting_name` (string): The name or key of the setting to change.
    - `setting_value` (string): The new value for the setting.
  - Action: Publishes a JSON payload `["setting_name", "setting_value"]` to the configured MQTT topic for settings changes.
  - Success Response: HTML snippet `<span class="text-success small ms-2">Saved!</span>`
  - Error Response: HTML snippet `<span class="text-danger small ms-2">Error saving!</span>` or `<span class="text-danger small ms-2">Server error!</span>` with appropriate HTTP status codes.

## Authentication

The application uses JWT (JSON Web Tokens) for authentication. Users can register and login to obtain an access token, which is then required for protected endpoints.

### Authentication Pages
-   **`/login`**: Web page for user login.
-   **`/register`**: Web page for new user registration.

### Authentication API Endpoints
-   **`POST /auth/register`**: Registers a new user.
    -   Request Body (JSON): `{"username": "your_username", "password": "your_password"}`
    -   Success Response (201): `{"msg": "User created successfully"}`
    -   Error Responses (400): `{"msg": "Username and password required"}` or `{"msg": "Username already exists"}`
-   **`POST /auth/login`**: Logs in an existing user.
    -   Request Body (JSON): `{"username": "your_username", "password": "your_password"}`
    -   Success Response (200): `{"access_token": "your_jwt_access_token"}`
    -   Error Response (401): `{"msg": "Bad username or password"}`

### Using Access Tokens
To access protected endpoints like `/api/change_setting`, include the JWT in the `Authorization` header of your request:
```
Authorization: Bearer <your_jwt_access_token>
```

## Data Storage

The application now uses an SQLite database (`app.db` by default) for persistent storage, managed via Flask-SQLAlchemy. The following data is stored:

-   **User Data**: Stores user credentials for authentication.
    -   `username`: User's chosen username (unique).
    -   `password_hash`: Hashed version of the user's password (using bcrypt).
-   **Sensor Data**: Stores historical readings from MQTT topics.
    -   `topic`: The MQTT topic of the message.
    -   `value`: The payload/content of the message (stored as a string).
    -   `timestamp`: The date and time when the message was received and stored (UTC).

Database schema migrations are handled by Flask-Migrate. The database is created and updated using `flask db upgrade` based on models defined in `app.py`.

## Security Notes

- The application uses plain text password authentication for MQTT.
- For production use, consider using TLS/SSL for secure MQTT communication.
- Do not expose the dashboard to the public internet without proper authentication
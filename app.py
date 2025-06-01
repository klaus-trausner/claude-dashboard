from flask import Flask, render_template, jsonify, request
import paho.mqtt.client as mqtt
from threading import Thread # For MQTT client background thread
import json
import time
import logging
from datetime import datetime
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import bcrypt

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Database Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# Use environment variable for database URI, with a default for local development
default_db_uri = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', default_db_uri)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Use environment variable for JWT secret key, with a strong default (but still recommend changing it)
# For production, JWT_SECRET_KEY *must* be set as an environment variable to a secure, random string.
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'a-very-secure-default-secret-key-CHANGE-ME')
# Add a log warning if default JWT_SECRET_KEY is used.
if app.config['JWT_SECRET_KEY'] == 'a-very-secure-default-secret-key-CHANGE-ME':
    logger.warning("WARNING: Using default JWT_SECRET_KEY. This should be changed for production by setting the JWT_SECRET_KEY environment variable.")

db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app) # Initialize JWTManager

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(200), nullable=False)
    value = db.Column(db.String(500), nullable=False) # Storing value as string for flexibility
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) # Uses datetime imported at top

    def __repr__(self):
        return f'<SensorData {self.topic} {self.value} {self.timestamp}>'

# Data storage
# current_data, historical_data, and data_lock removed as data is now in DB.

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
    "send_settings",  # Keep listening to get current settings
    "ext1/temperature",
    "ext1/humidity",
    "innen",
    "test",
    # "changeSetting" # No need to subscribe, we only publish to this
]
MQTT_PUBLISH_TOPIC_SETTINGS = "changeSetting"  # Topic to publish changes

# Global MQTT client instance
mqtt_client = None

# MQTT callback functions


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT Broker")
        # Subscribe to all topics
        for topic in MQTT_TOPICS:
            client.subscribe(topic)
            logger.info(f"Subscribed to {topic}")
    else:
        logger.error(f"Failed to connect to MQTT Broker, return code: {rc}")


def on_message(client, userdata, msg):
    topic = msg.topic
    try:
        payload_str = msg.payload.decode('utf-8')
        logger.info(f"Received message on topic {topic}: {payload_str}")
        message_timestamp = datetime.utcnow() # Ensure datetime is imported from datetime

        sensor_entry = SensorData(topic=topic, value=payload_str, timestamp=message_timestamp)
        with app.app_context(): # Ensure app is accessible
            db.session.add(sensor_entry)
            db.session.commit()
        logger.info(f"Stored message for {topic} in database.")
    except Exception as e:
        logger.error(f"Error processing message on topic {topic}: {e}")
        with app.app_context(): # Attempt to rollback in case of error
            db.session.rollback()

# Initialize MQTT client


def start_mqtt_client():
    global mqtt_client  # Allow modification of the global variable
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        mqtt_client = client  # Assign to global variable
        logger.info("MQTT client started and assigned.")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {e}")
        mqtt_client = None
        return None

# Flask routes


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/current_data')
def current_data_page():
    # Optionally filter out 'send_settings' from here if desired
    return render_template('current_data.html')


@app.route('/long_time_data')
def long_time_data():
    return render_template('long_time_data.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

# API endpoints to get the data


@app.route('/api/current_data')
def get_current_data():
    latest_data = {}
    try:
        # Ensure SensorData, db, json are available
        # Ensure datetime is available if formatting timestamp from db (though strftime is on datetime object)
        distinct_topics = db.session.query(SensorData.topic).distinct().all()
        for topic_tuple in distinct_topics:
            topic_name = topic_tuple[0]
            last_entry = SensorData.query.filter_by(topic=topic_name).order_by(SensorData.timestamp.desc()).first()
            if last_entry:
                value_to_return = last_entry.value
                if topic_name == "send_settings": # Assuming "send_settings" topic still exists
                    try:
                        value_to_return = json.loads(last_entry.value) # Ensure json is imported
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse JSON for send_settings topic from DB: {last_entry.value}")
                latest_data[topic_name] = {
                    'value': value_to_return,
                    'timestamp': last_entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                }
        return jsonify(latest_data)
    except Exception as e:
        logger.error(f"Error in /api/current_data: {e}")
        return jsonify({ "error": str(e) }), 500


@app.route('/api/historical_data')
def get_historical_data():
    history = {}
    try:
        # Ensure SensorData, db are available
        distinct_topics = db.session.query(SensorData.topic).distinct().all()
        for topic_tuple in distinct_topics:
            topic_name = topic_tuple[0]
            entries = SensorData.query.filter_by(topic=topic_name).order_by(SensorData.timestamp.desc()).limit(100).all()
            history[topic_name] = [{
                'value': entry.value, # Raw string value from DB
                'timestamp': entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            } for entry in reversed(entries)] # Reversed to show oldest first from the last 100
        return jsonify(history)
    except Exception as e:
        logger.error(f"Error in /api/historical_data: {e}")
        return jsonify({ "error": str(e) }), 500


@app.route('/api/topics')
def get_topics():
    # Exclude changeSetting if it was accidentally added
    readable_topics = [t for t in MQTT_TOPICS if t !=
                       MQTT_PUBLISH_TOPIC_SETTINGS]
    return jsonify(readable_topics)

# --- New API Endpoint for Changing Settings ---


@app.route('/api/change_setting', methods=['POST'])
@jwt_required()
def change_setting():
    current_user_identity = get_jwt_identity()
    global mqtt_client
    if not mqtt_client:
        logger.error(f"User '{current_user_identity}': MQTT client not available to publish setting change.")
        return jsonify(success=False, message="MQTT client not connected"), 500

    setting_name = request.form.get('setting_name')
    setting_value = request.form.get('setting_value')

    if not setting_name or setting_value is None:
        logger.warning(f"User '{current_user_identity}': Missing setting_name or setting_value in request for /api/change_setting.")
        return jsonify(success=False, message="Missing data"), 400

    try:
        # Format payload as ["key", "value_as_string"]
        payload_list = [setting_name, str(setting_value)]
        payload_string = json.dumps(payload_list)

        logger.info(
            f"User '{current_user_identity}' attempting to publish to {MQTT_PUBLISH_TOPIC_SETTINGS}: {payload_string}"
        )
        result = mqtt_client.publish(
            MQTT_PUBLISH_TOPIC_SETTINGS, payload=payload_string)
        # Wait briefly for publish confirmation
        result.wait_for_publish(timeout=5)

        if result.is_published():
            logger.info(
                f"User '{current_user_identity}' successfully published setting change for {setting_name} to {setting_value}")
            return f'<span class="text-success small ms-2">Saved!</span>'
        else:
            logger.error(
                f"User '{current_user_identity}': Failed to publish setting change for {setting_name}. MQTT publish rc: {result.rc}")
            return f'<span class="text-danger small ms-2">Error saving!</span>', 500

    except Exception as e:
        logger.error(
            f"User '{current_user_identity}': Error publishing setting change for {setting_name}: {e}")
        return f'<span class="text-danger small ms-2">Server error!</span>', 500
# --- End New API Endpoint ---

# ---- Authentication Endpoints ----

@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"msg": "Username and password required"}), 400

    if User.query.filter_by(username=username).first(): # User model should be accessible
        return jsonify({"msg": "Username already exists"}), 400

    new_user = User(username=username)
    new_user.set_password(password) # Hashes password using bcrypt

    try:
        db.session.add(new_user) # db object should be accessible
        db.session.commit()
        logger.info(f"User {username} created successfully") # logger should be accessible
        return jsonify({"msg": "User created successfully"}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error during registration for {username}: {e}")
        return jsonify({"msg": "Error creating user", "error": str(e)}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"msg": "Username and password required"}), 400

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        access_token = create_access_token(identity=username) # create_access_token should be imported
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"msg": "Bad username or password"}), 401

if __name__ == '__main__':
    # Start MQTT client in a separate thread
    mqtt_thread = Thread(target=start_mqtt_client, daemon=True)
    mqtt_thread.start()

    # Give MQTT client a moment to connect before starting Flask
    time.sleep(2)

    if mqtt_client:
        try:
            # Run Flask app
            # Important: use_reloader=False is crucial when using background threads like MQTT
            app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
        except KeyboardInterrupt:
            logger.info("Flask app stopping.")
        finally:
            # Stop MQTT client when Flask app stops
            if mqtt_client:
                logger.info("Stopping MQTT client loop.")
                mqtt_client.loop_stop()
                mqtt_client.disconnect()
                logger.info("MQTT client disconnected.")
    else:
        logger.error(
            "Could not start MQTT client. Flask app will run without MQTT functionality.")
        # Optionally run Flask anyway, or exit
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

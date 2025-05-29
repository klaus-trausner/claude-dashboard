from flask import Flask, render_template, jsonify, request  # Added request
import paho.mqtt.client as mqtt
from threading import Thread, Lock  # Added Lock for potential thread safety
import json
import time
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Data storage
current_data = {}
historical_data = {}
data_lock = Lock()  # Lock for thread-safe access to shared data

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
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        processed_value = payload_str  # Default to string

        # --- Modification: Parse send_settings specifically ---
        if topic == "send_settings":
            try:
                # Assuming the payload for send_settings is a JSON dict string
                processed_value = json.loads(payload_str)
                logger.info(f"Parsed send_settings data: {processed_value}")
            except json.JSONDecodeError as json_err:
                logger.error(
                    f"Failed to parse JSON from topic {topic}: {json_err}. Storing raw string.")
                processed_value = payload_str  # Fallback to raw string if parsing fails
        # --- End Modification ---

        with data_lock:  # Use lock for thread safety
            # Store current data
            current_data[topic] = {
                'value': processed_value,  # Store potentially parsed value
                'timestamp': timestamp
            }

            # Store historical data (limited to 100 entries per topic)
            if topic not in historical_data:
                historical_data[topic] = []

            # Store raw payload in historical data for consistency? Or processed?
            # Let's store the raw payload for history, as parsing might change.
            historical_data[topic].append({
                'value': payload_str,
                'timestamp': timestamp
            })

            # Limit historical data to last 100 entries
            if len(historical_data[topic]) > 100:
                historical_data[topic] = historical_data[topic][-100:]

    except Exception as e:
        logger.error(f"Error processing message on topic {topic}: {e}")

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

# API endpoints to get the data


@app.route('/api/current_data')
def get_current_data():
    with data_lock:  # Use lock for thread-safe access
        return jsonify(current_data)


@app.route('/api/historical_data')
def get_historical_data():
    with data_lock:  # Use lock for thread-safe access
        return jsonify(historical_data)


@app.route('/api/topics')
def get_topics():
    # Exclude changeSetting if it was accidentally added
    readable_topics = [t for t in MQTT_TOPICS if t !=
                       MQTT_PUBLISH_TOPIC_SETTINGS]
    return jsonify(readable_topics)

# --- New API Endpoint for Changing Settings ---


@app.route('/api/change_setting', methods=['POST'])
def change_setting():
    global mqtt_client
    if not mqtt_client:
        logger.error("MQTT client not available to publish setting change.")
        return jsonify(success=False, message="MQTT client not connected"), 500

    setting_name = request.form.get('setting_name')
    setting_value = request.form.get('setting_value')

    if not setting_name or setting_value is None:
        logger.warning("Missing setting_name or setting_value in request.")
        return jsonify(success=False, message="Missing data"), 400

    try:
        # Format payload as ["key", "value_as_string"]
        payload_list = [setting_name, str(setting_value)]
        payload_string = json.dumps(payload_list)

        logger.info(
            f"Attempting to publish to {MQTT_PUBLISH_TOPIC_SETTINGS}: {payload_string}")
        result = mqtt_client.publish(
            MQTT_PUBLISH_TOPIC_SETTINGS, payload=payload_string)
        # Wait briefly for publish confirmation
        result.wait_for_publish(timeout=5)

        if result.is_published():
            logger.info(
                f"Successfully published setting change for {setting_name} to {setting_value}")
            # Optionally, update current_data immediately for faster UI feedback
            # with data_lock:
            #    if "send_settings" in current_data and isinstance(current_data["send_settings"].get("value"), dict):
            #       current_data["send_settings"]["value"][setting_name] = setting_value # Store raw value, type might differ
            #       current_data["send_settings"]["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " (local update)"

            # Return the updated value or just success
            # Returning the value allows HTMX to update the input if needed
            # Simple confirmation for HTMX
            return f'<span class="text-success small ms-2">Saved!</span>'
        else:
            logger.error(
                f"Failed to publish setting change for {setting_name}. MQTT publish rc: {result.rc}")
            return f'<span class="text-danger small ms-2">Error saving!</span>', 500

    except Exception as e:
        logger.error(
            f"Error publishing setting change for {setting_name}: {e}")
        return f'<span class="text-danger small ms-2">Server error!</span>', 500
# --- End New API Endpoint ---


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

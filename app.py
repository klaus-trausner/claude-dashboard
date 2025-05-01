from flask import Flask, render_template, jsonify
import paho.mqtt.client as mqtt
from threading import Thread
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
        payload = msg.payload.decode('utf-8')
        logger.info(f"Received message on topic {topic}: {payload}")

        # Store current data
        current_data[topic] = {
            'value': payload,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Store historical data (limited to 100 entries per topic)
        if topic not in historical_data:
            historical_data[topic] = []

        historical_data[topic].append({
            'value': payload,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        # Limit historical data to last 100 entries
        if len(historical_data[topic]) > 100:
            historical_data[topic] = historical_data[topic][-100:]

    except Exception as e:
        logger.error(f"Error processing message: {e}")

# Initialize MQTT client


def start_mqtt_client():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        return client
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {e}")
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
    return render_template('current_data.html')


@app.route('/long_time_data')
def long_time_data():
    return render_template('long_time_data.html')

# API endpoints to get the data


@app.route('/api/current_data')
def get_current_data():
    return jsonify(current_data)


@app.route('/api/historical_data')
def get_historical_data():
    return jsonify(historical_data)


@app.route('/api/topics')
def get_topics():
    return jsonify(MQTT_TOPICS)


if __name__ == '__main__':
    # Start MQTT client in a separate thread
    mqtt_client = start_mqtt_client()

    if mqtt_client:
        try:
            # Run Flask app
            app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
        finally:
            # Stop MQTT client when Flask app stops
            mqtt_client.loop_stop()
    else:
        logger.error("Could not start MQTT client. Exiting.")

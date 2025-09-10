# Smart Kitchen Monitoring System - Gas, Temperature, and Motion/Light Sensors
import time
import json
import paho.mqtt.client as mqtt
from counterfit_connection import CounterFitConnection

# Initialize connection to Counterfit
CounterFitConnection.init('127.0.0.1', 5000)

# Pin definitions
GAS_SENSOR_PIN = 0
TEMP_SENSOR_PIN = 2
MOTION_SENSOR_PIN = 4  # Simulated motion/light sensor (digital input)

LED_GAS_PIN = 1        # Red LED for Gas Alert
LED_TEMP_PIN = 3       # Blue LED for Temp Alert
LED_LIGHT_PIN = 5      # Yellow LED for Motion/Light control

# Thresholds
GAS_THRESHOLD = 300       # ppm
TEMP_THRESHOLD = 35.0     # °C
LIGHT_THRESHOLD = 400     # Simulated LDR value

# Initialize all LEDs to OFF
CounterFitConnection.set_actuator_float_value(LED_GAS_PIN, 0)
CounterFitConnection.set_actuator_float_value(LED_TEMP_PIN, 0)
CounterFitConnection.set_actuator_float_value(LED_LIGHT_PIN, 0)

# MQTT Configuration
broker_address = "localhost"
topic_gas_data = "smart_kitchen/gas"
topic_temp_data = "smart_kitchen/temp_humidity"
topic_motion_data = "smart_kitchen/motion_light"
topic_alerts = "smart_kitchen/alerts"

# MQTT client setup
def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    client.subscribe(topic_alerts)

def on_message(client, userdata, msg):
    print(f"Received MQTT message on {msg.topic}: {msg.payload.decode()}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker_address, 1883, 60)
client.loop_start()

try:
    while True:
        # ---------- GAS SENSOR ----------
        gas_value = CounterFitConnection.get_sensor_int_value(GAS_SENSOR_PIN)
        gas_alert = gas_value > GAS_THRESHOLD

        client.publish(topic_gas_data, json.dumps({
            "gas_value": gas_value,
            "unit": "ppm"
        }))
        CounterFitConnection.set_actuator_float_value(LED_GAS_PIN, 1 if gas_alert else 0)

        # ---------- TEMPERATURE SENSOR ----------
        raw_temp = CounterFitConnection.get_sensor_int_value(TEMP_SENSOR_PIN)
        temperature = raw_temp / 10.0
        humidity = 60  # fixed/simulated

        temp_alert = temperature > TEMP_THRESHOLD

        client.publish(topic_temp_data, json.dumps({
            "temperature": temperature,
            "humidity": humidity,
            "unit": "C / %"
        }))
        CounterFitConnection.set_actuator_float_value(LED_TEMP_PIN, 1 if temp_alert else 0)

        # ---------- MOTION/LIGHT SENSOR ----------
        light_value = CounterFitConnection.get_sensor_int_value(MOTION_SENSOR_PIN)
        motion_detected = light_value < LIGHT_THRESHOLD  # Less light = presence detected

        client.publish(topic_motion_data, json.dumps({
            "light_value": light_value,
            "motion_detected": motion_detected
        }))
        CounterFitConnection.set_actuator_float_value(LED_LIGHT_PIN, 1 if motion_detected else 0)

        # ---------- ALERT LOGIC ----------
        if gas_alert or temp_alert:
            alert_msg = "Gas leak" if gas_alert else "High Temp"
            client.publish(topic_alerts, json.dumps({
                "alert": alert_msg,
                "gas_value": gas_value,
                "temperature": temperature
            }))

        # ---------- Debug Output ----------
        print(f"\n[Sensor Readings]")
        print(f"Gas: {gas_value} ppm ({'ALERT' if gas_alert else 'OK'})")
        print(f"Temp: {temperature}°C ({'ALERT' if temp_alert else 'OK'})")
        print(f"Light: {light_value} ({'MOTION' if motion_detected else 'No motion'})")
        print(f"LEDs - Gas: {gas_alert}, Temp: {temp_alert}, Light: {motion_detected}")

        time.sleep(5)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    client.loop_stop()
    client.disconnect()

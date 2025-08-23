"""Constants for Awtrix MQTT Bridge."""
from homeassistant.const import Platform

DOMAIN = "awtrix_mqtt_bridge"
PLATFORMS = [Platform.SENSOR, Platform.SWITCH]

# Configuration keys
CONF_MQTT_HOST = "mqtt_host"
CONF_MQTT_PORT = "mqtt_port"
CONF_MQTT_USERNAME = "mqtt_username"
CONF_MQTT_PASSWORD = "mqtt_password"
CONF_MQTT_CLIENT_ID = "mqtt_client_id"
CONF_MQTT_BASE_TOPIC = "mqtt_base_topic"
CONF_AWTRIX_HOST = "awtrix_host"
CONF_AWTRIX_PORT = "awtrix_port"

# Default values
DEFAULT_MQTT_PORT = 1883
DEFAULT_MQTT_BASE_TOPIC = "homeassistant"
DEFAULT_AWTRIX_PORT = 7000
DEFAULT_MQTT_CLIENT_ID = "awtrix_mqtt_bridge"

# Awtrix API endpoints
AWTRIX_API_CUSTOM_APP = "/api/custom"
AWTRIX_API_NOTIFY = "/api/notify"
AWTRIX_API_SETTINGS = "/api/settings"

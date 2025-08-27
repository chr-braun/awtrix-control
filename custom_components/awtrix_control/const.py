"""Constants for AWTRIX Control."""
from typing import Final

DOMAIN: Final = "awtrix_control"
NAME: Final = "AWTRIX Control"
DEFAULT_NAME: Final = "AWTRIX Control"

# Platforms - Wird in __init__.py definiert
# PLATFORMS = [Platform.SENSOR]  # Entfernt - wird in __init__.py definiert

# MQTT Topics
DEFAULT_TOPIC = "awtrix_0b86f0/notify"
CONF_MQTT_TOPIC: Final = "mqtt_topic"
DEFAULT_MQTT_TOPIC: Final = "awtrix_0b86f0/notify"

# Default Values
DEFAULT_COLOR: Final = "#00FF00"
DEFAULT_ICON: Final = 2400
DEFAULT_EFFECT: Final = "scroll"
DEFAULT_DURATION: Final = 10

# Automatisierungs-Typen
AUTOMATION_TYPES = {
    "time_based": "Zeit-basiert",
    "sensor_change": "Sensor-Änderung",
    "manual_trigger": "Manueller Trigger",
    "state_change": "Zustands-Änderung"
}

# Effekte
EFFECTS = {
    "none": "Kein Effekt",
    "scroll": "Scroll",
    "fade": "Fade",
    "blink": "Blinken",
    "rainbow": "Regenbogen"
}

# Standard-Farben
DEFAULT_COLORS = {
    "red": "#FF0000",
    "green": "#00FF00", 
    "blue": "#0000FF",
    "yellow": "#FFFF00",
    "cyan": "#00FFFF",
    "magenta": "#FF00FF",
    "white": "#FFFFFF",
    "orange": "#FF8000"
}


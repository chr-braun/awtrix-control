"""Services for AWTRIX Control integration."""
import json
import logging
from datetime import datetime
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CONF_MQTT_TOPIC, DEFAULT_MQTT_TOPIC, DEFAULT_COLOR, DEFAULT_ICON, DEFAULT_EFFECT, DEFAULT_DURATION

_LOGGER = logging.getLogger(__name__)

def _get_mqtt_topic(hass: HomeAssistant) -> str:
    """Get MQTT topic from config or use default."""
    try:
        if DOMAIN in hass.data and hass.data[DOMAIN]:
            config_entry_id = next(iter(hass.data[DOMAIN]))
            config_entry = hass.config_entries.async_get_entry(config_entry_id)
            if config_entry:
                return config_entry.data.get(CONF_MQTT_TOPIC, DEFAULT_MQTT_TOPIC)
    except Exception as e:
        _LOGGER.warning("Konnte MQTT-Topic nicht aus Config holen: %s", e)
    return DEFAULT_MQTT_TOPIC

async def _send_mqtt_message(hass: HomeAssistant, payload: dict) -> bool:
    """Send MQTT message to AWTRIX."""
    try:
        mqtt_topic = _get_mqtt_topic(hass)
        await hass.services.async_call(
            "mqtt", "publish",
            {
                "topic": mqtt_topic,
                "payload": json.dumps(payload),
                "qos": 0,
                "retain": False
            }
        )
        return True
    except Exception as e:
        _LOGGER.error("Fehler beim Senden an AWTRIX: %s", e)
        return False

async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for AWTRIX Control."""
    
    async def send_text(call: ServiceCall) -> None:
        """Send text to AWTRIX."""
        text = call.data.get("text", "")
        slot = call.data.get("slot", 0)
        color = call.data.get("color", DEFAULT_COLOR)
        icon = call.data.get("icon", DEFAULT_ICON)
        effect = call.data.get("effect", DEFAULT_EFFECT)
        duration = call.data.get("duration", DEFAULT_DURATION)
        
        payload = {
            "text": text,
            "slot": slot,
            "color": color,
            "icon": icon,
            "effect": effect,
            "duration": duration
        }
        
        if await _send_mqtt_message(hass, payload):
            _LOGGER.info("Text erfolgreich an AWTRIX gesendet: %s", text)
    
    async def send_time(call: ServiceCall) -> None:
        """Send current time to AWTRIX."""
        slot = call.data.get("slot", 0)
        color = call.data.get("color", "#FFFFFF")
        
        current_time = dt_util.now().strftime("%H:%M")
        
        payload = {
            "text": current_time,
            "slot": slot,
            "color": color,
            "icon": 2400,
            "effect": "none",
            "duration": 10
        }
        
        if await _send_mqtt_message(hass, payload):
            _LOGGER.info("Zeit erfolgreich an AWTRIX gesendet: %s", current_time)
    
    async def send_sensor(call: ServiceCall) -> None:
        """Send sensor value to AWTRIX."""
        sensor_name = call.data.get("sensor_name", "Sensor")
        sensor_entity = call.data.get("sensor_entity", "")
        slot = call.data.get("slot", 0)
        color = call.data.get("color", "#00FFFF")
        
        if sensor_entity:
            state = hass.states.get(sensor_entity)
            if state:
                value = state.state
                unit = state.attributes.get("unit_of_measurement", "")
                text = f"{sensor_name}: {value}{unit}"
            else:
                text = f"{sensor_name}: N/A"
        else:
            text = f"{sensor_name}: Kein Sensor"
        
        payload = {
            "text": text,
            "slot": slot,
            "color": color,
            "icon": 2422,
            "effect": "scroll",
            "duration": 15
        }
        
        if await _send_mqtt_message(hass, payload):
            _LOGGER.info("Sensor erfolgreich an AWTRIX gesendet: %s", text)
    
    async def send_date(call: ServiceCall) -> None:
        """Send current date to AWTRIX."""
        slot = call.data.get("slot", 0)
        color = call.data.get("color", "#00FFFF")
        
        current_date = dt_util.now().strftime("%d.%m.%Y")
        
        payload = {
            "text": current_date,
            "slot": slot,
            "color": color,
            "icon": 2400,
            "effect": "none",
            "duration": 10
        }
        
        if await _send_mqtt_message(hass, payload):
            _LOGGER.info("Datum erfolgreich an AWTRIX gesendet: %s", current_date)
    
    async def send_test(call: ServiceCall) -> None:
        """Send test message to AWTRIX."""
        slot = call.data.get("slot", 0)
        color = call.data.get("color", "#00FF00")
        
        test_text = "Test erfolgreich!"
        
        payload = {
            "text": test_text,
            "slot": slot,
            "color": color,
            "icon": 2400,
            "effect": "blink",
            "duration": 5
        }
        
        if await _send_mqtt_message(hass, payload):
            _LOGGER.info("Test erfolgreich an AWTRIX gesendet: %s", test_text)
    
    async def reload_integration(call: ServiceCall) -> None:
        """Reload AWTRIX Control integration without restarting Home Assistant."""
        try:
            config_entry = None
            for entry in hass.config_entries.async_entries(DOMAIN):
                config_entry = entry
                break
            
            if config_entry:
                await hass.config_entries.async_reload(config_entry.entry_id)
                _LOGGER.info("AWTRIX Control Integration erfolgreich neu geladen")
            else:
                _LOGGER.warning("Keine AWTRIX Control Config Entry gefunden")
                
        except Exception as e:
            _LOGGER.error("Fehler beim Neuladen der Integration: %s", e)
    
    # Register services
    try:
        hass.services.async_register("awtrix_control", "send_text", send_text)
        hass.services.async_register("awtrix_control", "send_time", send_time)
        hass.services.async_register("awtrix_control", "send_date", send_date)
        hass.services.async_register("awtrix_control", "send_sensor", send_sensor)
        hass.services.async_register("awtrix_control", "send_test", send_test)
        hass.services.async_register("awtrix_control", "reload_integration", reload_integration)
        _LOGGER.info("AWTRIX Control Services erfolgreich registriert")
    except Exception as e:
        _LOGGER.error("Fehler beim Registrieren der Services: %s", e)

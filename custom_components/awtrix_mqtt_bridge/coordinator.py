"""Data coordinator for Awtrix MQTT Bridge."""
import logging
import asyncio
from datetime import timedelta
from typing import Dict, Any, Optional

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers import entity_registry as er
import paho.mqtt.client as mqtt
import aiohttp
import json

from .const import (
    DOMAIN,
    CONF_MQTT_HOST,
    CONF_MQTT_PORT,
    CONF_MQTT_USERNAME,
    CONF_MQTT_PASSWORD,
    CONF_MQTT_CLIENT_ID,
    CONF_MQTT_BASE_TOPIC,
    CONF_AWTRIX_HOST,
    CONF_AWTRIX_PORT,
    AWTRIX_API_CUSTOM_APP,
)

_LOGGER = logging.getLogger(__name__)

class AwtrixMqttCoordinator(DataUpdateCoordinator):
    """Coordinator to manage MQTT and Awtrix communication."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        
        self.entry = entry
        self.config = entry.data
        self.sensor_mappings: Dict[str, Dict[str, Any]] = {}
        self.mqtt_client: Optional[mqtt.Client] = None
        
    async def async_setup(self) -> None:
        """Set up the coordinator."""
        await self._setup_mqtt()
        
    async def _setup_mqtt(self) -> None:
        """Set up MQTT client."""
        if self.mqtt_client:
            try:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
            except Exception:
                pass  # Ignore errors when cleaning up
        
        try:
            self.mqtt_client = mqtt.Client(
                client_id=self.config[CONF_MQTT_CLIENT_ID],
                callback_api_version=mqtt.CallbackAPIVersion.VERSION1
            )
        except (AttributeError, TypeError):
            # Fallback for older paho-mqtt versions
            self.mqtt_client = mqtt.Client(client_id=self.config[CONF_MQTT_CLIENT_ID])
        
        if self.config.get(CONF_MQTT_USERNAME):
            self.mqtt_client.username_pw_set(
                self.config[CONF_MQTT_USERNAME],
                self.config.get(CONF_MQTT_PASSWORD)
            )
        
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_message = self._on_mqtt_message
        self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
        
        try:
            await self.hass.async_add_executor_job(
                self.mqtt_client.connect,
                self.config[CONF_MQTT_HOST],
                self.config[CONF_MQTT_PORT],
                60
            )
            
            self.mqtt_client.loop_start()
            _LOGGER.info("MQTT client setup completed")
        except Exception as exc:
            _LOGGER.error("Failed to setup MQTT client: %s", exc)
            raise
        
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection."""
        if rc == 0:
            _LOGGER.info("Connected to MQTT broker")
            # Subscribe to sensor topics
            topic = f"{self.config[CONF_MQTT_BASE_TOPIC]}/+/+/state"
            client.subscribe(topic)
        else:
            _LOGGER.error("Failed to connect to MQTT broker: %s", rc)
        
    def _on_mqtt_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnect."""
        _LOGGER.warning("MQTT client disconnected with code: %s", rc)
        if rc != 0:
            _LOGGER.error("Unexpected MQTT disconnection. Will attempt to reconnect.")
    
    def _on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            _LOGGER.debug("MQTT message received: %s = %s", topic, payload)
            
            # Process sensor updates
            self.hass.async_create_task(self._process_sensor_update(topic, payload))
        except Exception as exc:
            _LOGGER.error("Error processing MQTT message: %s", exc)
    
    async def _process_sensor_update(self, topic: str, payload: str) -> None:
        """Process sensor update and send to Awtrix if mapped."""
        try:
            # Check if this sensor is mapped to an Awtrix app
            for sensor_id, mapping in self.sensor_mappings.items():
                # Try different ways to match the sensor
                mapped_topic = mapping.get("mqtt_topic", "")
                if mapped_topic and (mapped_topic == topic or topic.endswith(f"/{sensor_id}/state")):
                    await self._send_to_awtrix(sensor_id, payload, mapping)
                    break
        except Exception as exc:
            _LOGGER.error("Error processing sensor update for %s: %s", topic, exc)
    
    async def _send_to_awtrix(self, sensor_id: str, value: str, mapping: Dict[str, Any]) -> None:
        """Send sensor data to Awtrix display."""
        try:
            awtrix_host = self.config[CONF_AWTRIX_HOST]
            awtrix_port = self.config[CONF_AWTRIX_PORT]
            
            # Format the display text
            display_text = mapping.get("format", "{value}").replace("{value}", str(value))
            if mapping.get("display_name"):
                display_text = f"{mapping['display_name']}: {display_text}"
            
            # Prepare Awtrix payload
            payload = {
                "text": display_text,
                "icon": mapping.get("icon", 1),
                "color": mapping.get("color", [255, 255, 255]),
                "duration": mapping.get("duration", 5) * 1000,  # Convert to milliseconds
            }
            
            # Add effects
            effect = mapping.get("effect", "none")
            if effect == "scroll":
                payload["scrollSpeed"] = 50
            elif effect == "fade":
                payload["fadeText"] = True
            elif effect == "blink":
                payload["blinkText"] = 500
            elif effect == "rainbow":
                payload["rainbow"] = True
            
            # Use slot_id from mapping, fallback to sensor_id
            app_name = mapping.get("slot_id", sensor_id)
            url = f"http://{awtrix_host}:{awtrix_port}{AWTRIX_API_CUSTOM_APP}"
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json={str(app_name): payload}) as response:
                    if response.status == 200:
                        _LOGGER.debug("Successfully sent to Awtrix slot %s: %s", app_name, display_text)
                    else:
                        response_text = await response.text()
                        _LOGGER.error("Failed to send to Awtrix (HTTP %s): %s", response.status, response_text)
                        
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout sending to Awtrix: %s", sensor_id)
        except aiohttp.ClientError as exc:
            _LOGGER.error("Network error sending to Awtrix: %s", exc)
        except Exception as exc:
            _LOGGER.error("Unexpected error sending to Awtrix: %s", exc)
    
    async def add_sensor_mapping(self, sensor_id: str, mapping: Dict[str, Any]) -> None:
        """Add a sensor to Awtrix mapping."""
        self.sensor_mappings[sensor_id] = mapping
        _LOGGER.info("Added sensor mapping: %s -> %s", sensor_id, mapping)
    
    async def remove_sensor_mapping(self, sensor_id: str) -> None:
        """Remove a sensor mapping."""
        if sensor_id in self.sensor_mappings:
            del self.sensor_mappings[sensor_id]
            _LOGGER.info("Removed sensor mapping: %s", sensor_id)
    
    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data."""
        return {
            "sensor_mappings": self.sensor_mappings,
            "mqtt_connected": self.mqtt_client and self.mqtt_client.is_connected(),
        }

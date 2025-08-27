"""Sensor platform for AWTRIX Control integration."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DEFAULT_NAME

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AWTRIX Control sensor platform."""
    
    # Get config data
    config_data = config_entry.data
    name = config_data.get("name", DEFAULT_NAME)
    
    # Create sensor entities
    entities = [
        AwtrixControlSensor(name, "status", "Status"),
        AwtrixControlSensor(name, "last_message", "Letzte Nachricht"),
        AwtrixControlSensor(name, "message_count", "Nachrichten gesendet"),
    ]
    
    async_add_entities(entities)


class AwtrixControlSensor(SensorEntity):
    """AWTRIX Control sensor entity."""

    def __init__(self, name: str, sensor_type: str, sensor_name: str) -> None:
        """Initialize the sensor."""
        self._attr_name = f"{name} {sensor_name}"
        self._attr_unique_id = f"awtrix_control_{sensor_type}"
        self._attr_native_value = "Bereit"
        self._attr_icon = "mdi:led-matrix"
        
        # Set initial state based on sensor type
        if sensor_type == "status":
            self._attr_native_value = "Bereit"
        elif sensor_type == "last_message":
            self._attr_native_value = "Keine"
        elif sensor_type == "message_count":
            self._attr_native_value = "0"
    
    @property
    def extra_state_attributes(self) -> dict[str, StateType]:
        """Return entity specific state attributes."""
        return {
            "integration": "awtrix_control",
            "sensor_type": "status",
        }

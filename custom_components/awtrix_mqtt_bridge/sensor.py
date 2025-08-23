"""Sensor platform for Awtrix MQTT Bridge."""
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AwtrixMqttCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor platform."""
    coordinator: AwtrixMqttCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    sensors = [
        AwtrixMqttBridgeStatusSensor(coordinator),
        AwtrixMappingCountSensor(coordinator),
    ]
    
    async_add_entities(sensors, True)

class AwtrixMqttBridgeStatusSensor(CoordinatorEntity, SensorEntity):
    """Status sensor for Awtrix MQTT Bridge."""
    
    def __init__(self, coordinator: AwtrixMqttCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._attr_name = "Awtrix MQTT Bridge Status"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_status"
        
    @property
    def state(self) -> str:
        """Return the state of the sensor."""
        if self.coordinator.data.get("mqtt_connected", False):
            return "connected"
        return "disconnected"
        
    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        return {
            "mqtt_host": self.coordinator.config.get("mqtt_host"),
            "awtrix_host": self.coordinator.config.get("awtrix_host"),
            "sensor_mappings": len(self.coordinator.sensor_mappings),
        }

class AwtrixMappingCountSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing number of active mappings."""
    
    def __init__(self, coordinator: AwtrixMqttCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._attr_name = "Awtrix Active Mappings"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_mappings"
        self._attr_unit_of_measurement = "mappings"
        
    @property
    def state(self) -> int:
        """Return the number of active mappings."""
        return len(self.coordinator.sensor_mappings)
        
    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        return {
            "mappings": list(self.coordinator.sensor_mappings.keys()),
        }

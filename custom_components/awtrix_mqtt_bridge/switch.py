"""Switch platform for Awtrix MQTT Bridge."""
import logging
from homeassistant.components.switch import SwitchEntity
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
    """Set up switch platform."""
    coordinator: AwtrixMqttCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    switches = [
        AwtrixBridgeToggleSwitch(coordinator),
    ]
    
    async_add_entities(switches, True)

class AwtrixBridgeToggleSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable the bridge."""
    
    def __init__(self, coordinator: AwtrixMqttCoordinator) -> None:
        """Initialize switch."""
        super().__init__(coordinator)
        self._attr_name = "Awtrix MQTT Bridge"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_toggle"
        self._attr_device_class = "switch"
        self._is_on = True
        
    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._is_on and bool(self.coordinator.mqtt_client and self.coordinator.mqtt_client.is_connected())
        
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
        
    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        try:
            if not self.coordinator.mqtt_client or not self.coordinator.mqtt_client.is_connected():
                await self.coordinator._setup_mqtt()
            self._is_on = True
            self.async_write_ha_state()
            _LOGGER.info("Awtrix MQTT Bridge enabled")
        except Exception as exc:
            _LOGGER.error("Failed to enable Awtrix MQTT Bridge: %s", exc)
            self._is_on = False
            self.async_write_ha_state()
        
    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        try:
            self._is_on = False
            if self.coordinator.mqtt_client:
                await self.hass.async_add_executor_job(self.coordinator.mqtt_client.loop_stop)
                await self.hass.async_add_executor_job(self.coordinator.mqtt_client.disconnect)
            self.async_write_ha_state()
            _LOGGER.info("Awtrix MQTT Bridge disabled")
        except Exception as exc:
            _LOGGER.error("Error disabling Awtrix MQTT Bridge: %s", exc)
            self.async_write_ha_state()

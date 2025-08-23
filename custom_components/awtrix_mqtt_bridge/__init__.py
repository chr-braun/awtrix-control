"""Awtrix MQTT Bridge Integration for Home Assistant."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery
from homeassistant.const import Platform
from homeassistant.components.frontend import add_extra_js_url

from .const import DOMAIN, PLATFORMS
from .coordinator import AwtrixMqttCoordinator
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Awtrix MQTT Bridge from a config entry."""
    _LOGGER.info("Setting up Awtrix MQTT Bridge integration for entry %s", entry.entry_id)
    
    try:
        coordinator = AwtrixMqttCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()
        
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = coordinator
        
        # Setup platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        _LOGGER.debug("Platforms setup completed: %s", PLATFORMS)
        
        # Register frontend resources
        hass.http.register_static_path(
            "/awtrix_mqtt_bridge",
            hass.config.path("custom_components/awtrix_mqtt_bridge/www"),
            cache_headers=False
        )
        _LOGGER.debug("Frontend resources registered")
        
        # Setup services
        await async_setup_services(hass)
        _LOGGER.debug("Services setup completed")
        
        # Setup MQTT after everything else is ready
        await coordinator.async_setup()
        
        _LOGGER.info("Awtrix MQTT Bridge integration setup completed successfully")
        return True
        
    except Exception as exc:
        _LOGGER.error("Failed to setup Awtrix MQTT Bridge: %s", exc, exc_info=True)
        return False

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Awtrix MQTT Bridge integration for entry %s", entry.entry_id)
    
    try:
        # Unload platforms
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
        
        if unload_ok:
            # Clean up coordinator and MQTT connections
            coordinator = hass.data[DOMAIN].pop(entry.entry_id, None)
            if coordinator and coordinator.mqtt_client:
                try:
                    await hass.async_add_executor_job(coordinator.mqtt_client.loop_stop)
                    await hass.async_add_executor_job(coordinator.mqtt_client.disconnect)
                    _LOGGER.debug("MQTT client disconnected during unload")
                except Exception as exc:
                    _LOGGER.warning("Error disconnecting MQTT client during unload: %s", exc)
            
            _LOGGER.info("Awtrix MQTT Bridge integration unloaded successfully")
        else:
            _LOGGER.error("Failed to unload some platforms for Awtrix MQTT Bridge")
        
        return unload_ok
        
    except Exception as exc:
        _LOGGER.error("Error unloading Awtrix MQTT Bridge: %s", exc, exc_info=True)
        return False

"""Frontend for AWTRIX Control integration."""
import logging
from homeassistant.core import HomeAssistant
from homeassistant.components.frontend import add_to_frontend_storage

_LOGGER = logging.getLogger(__name__)

async def async_setup_frontend(hass: HomeAssistant) -> None:
    """Set up frontend for AWTRIX Control."""
    try:
        # Register custom card
        hass.http.register_static_path(
            "/awtrix-control-card",
            hass.config.path("custom_components", "awtrix_control", "www"),
            cache_headers=False
        )
        
        # Add custom card to frontend
        add_to_frontend_storage(
            hass,
            "awtrix-control-card",
            "/awtrix-control-card/awtrix-control-card.js"
        )
        
        _LOGGER.info("AWTRIX Control Custom Card erfolgreich registriert")
        
    except Exception as e:
        _LOGGER.error("Fehler beim Einrichten der Custom Card: %s", e)

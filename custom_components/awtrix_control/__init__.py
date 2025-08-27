"""The AWTRIX Control integration."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from . import services

_LOGGER = logging.getLogger(__name__)

# EXPLICIT: PLATFORMS is defined here, NOT imported from const.py
# This prevents any import errors
PLATFORMS = [Platform.SENSOR]

# CRITICAL: This file MUST NOT import PLATFORMS from const.py
# If you see this error, it means Home Assistant is loading a cached version
# Solution: Restart Home Assistant or reinstall the integration

# IMPORTANT: PLATFORMS is defined locally, not imported from const.py


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up AWTRIX Control component."""
    _LOGGER.info("AWTRIX Control Integration wird eingerichtet...")
    
    hass.data.setdefault(DOMAIN, {})
    
    # GUI Panel entfernt - nur Services werden eingerichtet
    _LOGGER.info("AWTRIX Control: GUI entfernt, Services werden eingerichtet")
    
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AWTRIX Control from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Set up services
    await services.async_setup_services(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove a config entry."""
    try:
        hass.data[DOMAIN].pop(entry.entry_id)
    except KeyError:
        pass

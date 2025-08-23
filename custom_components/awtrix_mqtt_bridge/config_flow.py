"""Config flow for Awtrix MQTT Bridge."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD

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
    DEFAULT_MQTT_PORT,
    DEFAULT_MQTT_BASE_TOPIC,
    DEFAULT_AWTRIX_PORT,
    DEFAULT_MQTT_CLIENT_ID,
)

import logging
_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_MQTT_HOST): cv.string,
    vol.Optional(CONF_MQTT_PORT, default=DEFAULT_MQTT_PORT): cv.port,
    vol.Optional(CONF_MQTT_USERNAME): cv.string,
    vol.Optional(CONF_MQTT_PASSWORD): cv.string,
    vol.Optional(CONF_MQTT_CLIENT_ID, default=DEFAULT_MQTT_CLIENT_ID): cv.string,
    vol.Optional(CONF_MQTT_BASE_TOPIC, default=DEFAULT_MQTT_BASE_TOPIC): cv.string,
    vol.Required(CONF_AWTRIX_HOST): cv.string,
    vol.Optional(CONF_AWTRIX_PORT, default=DEFAULT_AWTRIX_PORT): cv.port,
})

class AwtrixMqttBridgeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Awtrix MQTT Bridge."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Test MQTT connection
                await self._test_mqtt_connection(user_input)
                # Test Awtrix connection  
                await self._test_awtrix_connection(user_input)
                
                return self.async_create_entry(
                    title=f"Awtrix Bridge ({user_input[CONF_AWTRIX_HOST]})",
                    data=user_input
                )
            except Exception as exc:
                _LOGGER.error("Error setting up Awtrix MQTT Bridge: %s", exc)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user", 
            data_schema=STEP_USER_DATA_SCHEMA, 
            errors=errors
        )

    async def _test_mqtt_connection(self, config):
        """Test MQTT connection."""
        import paho.mqtt.client as mqtt
        import asyncio
        
        def on_connect(client, userdata, flags, rc):
            userdata['connected'] = rc == 0
            userdata['rc'] = rc
        
        client = mqtt.Client(config[CONF_MQTT_CLIENT_ID])
        if config.get(CONF_MQTT_USERNAME):
            client.username_pw_set(
                config[CONF_MQTT_USERNAME], 
                config.get(CONF_MQTT_PASSWORD)
            )
        
        userdata = {'connected': False, 'rc': None}
        client.user_data_set(userdata)
        client.on_connect = on_connect
        
        try:
            await self.hass.async_add_executor_job(
                client.connect,
                config[CONF_MQTT_HOST],
                config[CONF_MQTT_PORT],
                10
            )
            
            # Wait for connection callback
            for _ in range(50):  # 5 second timeout
                if userdata['rc'] is not None:
                    break
                await asyncio.sleep(0.1)
            
            if not userdata['connected']:
                raise Exception(f"MQTT connection failed with code {userdata['rc']}")
                
            await self.hass.async_add_executor_job(client.disconnect)
            return True
            
        except Exception as exc:
            _LOGGER.error("MQTT connection test failed: %s", exc)
            raise Exception(f"MQTT connection failed: {exc}")
        finally:
            try:
                await self.hass.async_add_executor_job(client.loop_stop)
            except Exception:
                pass

    async def _test_awtrix_connection(self, config):
        """Test Awtrix connection."""
        import aiohttp
        
        url = f"http://{config[CONF_AWTRIX_HOST]}:{config[CONF_AWTRIX_PORT]}/api/stats"
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        _LOGGER.debug("Awtrix connection successful: %s", data)
                        return True
                    else:
                        response_text = await response.text()
                        raise Exception(f"Awtrix returned HTTP {response.status}: {response_text}")
                        
        except aiohttp.ClientError as exc:
            _LOGGER.error("Awtrix connection failed: %s", exc)
            raise Exception(f"Cannot connect to Awtrix: {exc}")
        except Exception as exc:
            _LOGGER.error("Awtrix connection test failed: %s", exc)
            raise Exception(f"Awtrix connection failed: {exc}")

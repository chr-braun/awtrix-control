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
from .mqtt_connector import RobustMQTTConnector, AuthMethod

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
        description_placeholders = {}

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
                error_msg = str(exc)
                _LOGGER.error("Error setting up Awtrix MQTT Bridge: %s", error_msg)
                
                # Provide specific error categories for better user experience
                if "timeout" in error_msg.lower() or "no response" in error_msg.lower():
                    errors["base"] = "mqtt_timeout"
                    description_placeholders["error_details"] = (
                        "MQTT broker not responding. Common solutions:\n"
                        "• Check if Mosquitto add-on is running\n"
                        "• Try 'core-mosquitto' as hostname for HA add-on\n"
                        "• Verify MQTT broker IP address\n"
                        "• Check firewall settings on port 1883"
                    )
                elif "authentication" in error_msg.lower() or "password" in error_msg.lower() or "4" in str(exc) or "5" in str(exc):
                    errors["base"] = "mqtt_auth"
                    
                    # Enhanced authentication troubleshooting
                    host = user_input.get(CONF_MQTT_HOST, "unknown")
                    username = user_input.get(CONF_MQTT_USERNAME, "")
                    
                    if host == "192.168.178.29":
                        suggestion = (
                            "External MQTT broker (router) authentication failed:\n"
                            "• Check FritzBox MQTT settings at http://192.168.178.1\n"
                            "• Verify user 'biber' exists in router MQTT config\n"
                            "• Try anonymous connection (leave username/password empty)\n"
                            "• Consider using Home Assistant Mosquitto add-on instead"
                        )
                    elif "homeassistant" in host.lower():
                        suggestion = (
                            "Home Assistant MQTT authentication failed:\n"
                            "• Start Mosquitto add-on: Settings → Add-ons → Mosquitto\n"
                            "• Use host 'core-mosquitto' instead of 'homeassistant.local'\n"
                            "• Verify add-on user config matches your credentials\n"
                            "• Try anonymous connection first"
                        )
                    else:
                        suggestion = (
                            "MQTT authentication failed:\n"
                            "• Verify username and password are correct\n"
                            "• Check user permissions in MQTT broker\n"
                            "• Try anonymous connection (no credentials)\n"
                            "• Ensure MQTT broker allows the specified user"
                        )
                    
                    description_placeholders["error_details"] = suggestion
                elif "network" in error_msg.lower() or "not reachable" in error_msg.lower():
                    errors["base"] = "mqtt_network"
                    description_placeholders["error_details"] = (
                        "Cannot reach MQTT broker:\n"
                        "• Verify IP address or hostname\n"
                        "• Check if MQTT broker is running\n"
                        "• Ensure port 1883 is accessible\n"
                        "• Check network connectivity"
                    )
                elif "awtrix" in error_msg.lower():
                    errors["base"] = "awtrix_connection"
                    description_placeholders["error_details"] = (
                        "Cannot connect to Awtrix device:\n"
                        "• Check Awtrix IP address\n"
                        "• Verify Awtrix is powered on\n"
                        "• Ensure port 7000 is accessible\n"
                        "• Check network connectivity to device"
                    )
                else:
                    errors["base"] = "cannot_connect"
                    description_placeholders["error_details"] = error_msg

        return self.async_show_form(
            step_id="user", 
            data_schema=STEP_USER_DATA_SCHEMA, 
            errors=errors,
            description_placeholders=description_placeholders
        )

    async def _test_mqtt_connection(self, config):
        """Test MQTT connection using robust connector with automatic fallback."""
        _LOGGER.info("🔍 Testing MQTT connection with enhanced robust connector...")
        
        # Create robust MQTT connector
        mqtt_connector = RobustMQTTConnector(self.hass)
        
        # Prepare configuration for connector
        mqtt_config = {
            "host": config[CONF_MQTT_HOST],
            "port": config[CONF_MQTT_PORT],
            "username": config.get(CONF_MQTT_USERNAME),
            "password": config.get(CONF_MQTT_PASSWORD),
            "client_id": config[CONF_MQTT_CLIENT_ID]
        }
        
        # First, run specific credential testing for biber/2203801826 scenario
        _LOGGER.info("🔑 Running specific credential testing for your setup...")
        
        try:
            credential_test_results = await mqtt_connector.test_credentials_specifically(mqtt_config)
            
            if credential_test_results["success"]:
                _LOGGER.info("✅ Specific credential testing found working configuration!")
                
                # Find the working scenario and update config
                for result in credential_test_results["results"]:
                    if result["success"]:
                        if result["method"] == "anonymous":
                            _LOGGER.info("🔓 Using anonymous connection - clearing stored credentials")
                            config[CONF_MQTT_USERNAME] = ""
                            config[CONF_MQTT_PASSWORD] = ""
                        
                        _LOGGER.info(f"✨ Working configuration: {result['scenario']}")
                        return True
            else:
                _LOGGER.warning("⚠️ Specific credential testing failed, trying standard fallback...")
        
        except Exception as exc:
            _LOGGER.warning(f"⚠️ Credential testing error: {exc}, trying standard approach...")
        
        # Standard fallback testing
        result = await mqtt_connector.test_connection(mqtt_config)
        
        if result.success:
            _LOGGER.info(f"✅ MQTT connection successful using {result.method.value}")
            
            # Update config with working settings if different from input
            if result.host != config[CONF_MQTT_HOST]:
                _LOGGER.info(f"📝 Using working host {result.host} instead of {config[CONF_MQTT_HOST]}")
                config[CONF_MQTT_HOST] = result.host
            
            # If successful with anonymous, clear credentials to avoid confusion
            if result.method == AuthMethod.ANONYMOUS:
                _LOGGER.info("🔓 Using anonymous connection - clearing stored credentials")
                config[CONF_MQTT_USERNAME] = ""
                config[CONF_MQTT_PASSWORD] = ""
            
            return True
        
        # If primary failed, try to find working broker
        _LOGGER.warning(f"❌ Primary MQTT configuration failed: {result.error}")
        _LOGGER.info("🔍 Searching for alternative working brokers...")
        
        working_result = await mqtt_connector.find_working_broker(mqtt_config)
        
        if working_result and working_result.success:
            _LOGGER.info(f"✅ Found working broker: {working_result.host}:{working_result.port}")
            
            # Update config with working broker settings
            config[CONF_MQTT_HOST] = working_result.host
            config[CONF_MQTT_PORT] = working_result.port
            
            if working_result.method == AuthMethod.ANONYMOUS:
                config[CONF_MQTT_USERNAME] = ""
                config[CONF_MQTT_PASSWORD] = ""
            
            return True
        
        # All attempts failed - raise detailed error
        error_details = f"MQTT connection failed: {result.error}\n\nTroubleshooting steps:\n"
        error_details += "• Check if MQTT broker is running\n"
        error_details += "• Verify credentials (try anonymous if unsure)\n"
        error_details += "• For Home Assistant: use 'core-mosquitto' as host\n"
        error_details += "• Check network connectivity and firewall\n"
        
        # Add specific recommendations based on your setup
        host = config[CONF_MQTT_HOST]
        if host == "192.168.178.29":
            error_details += "\nFor FritzBox MQTT (192.168.178.29):\n"
            error_details += "• Try anonymous connection first (no username/password)\n"
            error_details += "• Check FritzBox Smart Home settings\n"
            error_details += "• Verify MQTT is enabled in router\n"
        elif "mosquitto" in host or "core-mosquitto" in host:
            error_details += "\nFor Home Assistant Mosquitto:\n"
            error_details += "• Start Mosquitto add-on in Home Assistant\n"
            error_details += "• Verify user 'biber' is configured\n"
            error_details += "• Check add-on logs for authentication errors\n"
        
        raise Exception(error_details)

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

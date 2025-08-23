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
from .mqtt_health_checker import MQTTHealthChecker

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
                elif "authentication" in error_msg.lower() or "password" in error_msg.lower():
                    errors["base"] = "mqtt_auth"
                    description_placeholders["error_details"] = (
                        "MQTT authentication failed:\n"
                        "• Check username and password\n"
                        "• Verify user permissions in MQTT broker\n"
                        "• Try without credentials for anonymous access"
                    )
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
        """Test MQTT connection with detailed debugging and automatic fallback configurations."""
        import paho.mqtt.client as mqtt
        import asyncio
        import socket
        
        _LOGGER.info("🔍 Testing MQTT connection to %s:%s", config[CONF_MQTT_HOST], config[CONF_MQTT_PORT])
        
        # First, test basic network connectivity with extended diagnostics
        try:
            _LOGGER.info("🌐 Testing network connectivity...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)  # Increased timeout
            result = sock.connect_ex((config[CONF_MQTT_HOST], config[CONF_MQTT_PORT]))
            sock.close()
            
            if result != 0:
                # Try common MQTT broker configurations automatically
                common_hosts = []
                if config[CONF_MQTT_HOST] in ['localhost', '127.0.0.1']:
                    common_hosts = ['core-mosquitto', 'mosquitto', 'homeassistant.local']
                
                for fallback_host in common_hosts:
                    _LOGGER.info("🔄 Trying fallback host: %s", fallback_host)
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(5)
                        result = sock.connect_ex((fallback_host, config[CONF_MQTT_PORT]))
                        sock.close()
                        if result == 0:
                            _LOGGER.info("✅ Found working MQTT broker at %s:%s", fallback_host, config[CONF_MQTT_PORT])
                            config = config.copy()
                            config[CONF_MQTT_HOST] = fallback_host
                            break
                    except Exception:
                        continue
                else:
                    raise Exception(f"❌ Network connection failed to {config[CONF_MQTT_HOST]}:{config[CONF_MQTT_PORT]} - Port not reachable. Tried fallback hosts: {common_hosts}")
            
            _LOGGER.info("✅ Network connectivity OK to %s:%s", config[CONF_MQTT_HOST], config[CONF_MQTT_PORT])
        except Exception as exc:
            _LOGGER.error("❌ Network test failed: %s", exc)
            # Provide specific troubleshooting guidance
            if "111" in str(exc) or "Connection refused" in str(exc):
                guidance = (
                    "MQTT broker is not running or not accessible. "
                    "Try these steps:\n"
                    "1. Check if Mosquitto add-on is installed and running\n"
                    "2. For Mosquitto add-on, try host 'core-mosquitto'\n"
                    "3. For external broker, verify IP address and firewall settings\n"
                    "4. Check if port 1883 is open and not blocked"
                )
                raise Exception(f"Cannot reach MQTT broker: {guidance}")
            raise Exception(f"Cannot reach {config[CONF_MQTT_HOST]}:{config[CONF_MQTT_PORT]} - {exc}")
        
        def on_connect(client, userdata, flags, rc):
            _LOGGER.info("📥 MQTT connect callback: rc=%s, flags=%s", rc, flags)
            userdata['connected'] = rc == 0
            userdata['rc'] = rc
            
            # Log specific error codes with emojis for better visibility
            error_messages = {
                0: "✅ Connection successful",
                1: "❌ Protocol version not supported by broker",
                2: "❌ Client ID rejected by broker",
                3: "❌ MQTT broker unavailable",
                4: "❌ Bad username or password",
                5: "❌ Authentication failed - not authorized"
            }
            _LOGGER.info("🔗 MQTT connection result: %s", error_messages.get(rc, f"❌ Unknown error code {rc}"))
        
        def on_disconnect(client, userdata, rc):
            _LOGGER.info("📤 MQTT disconnect callback: rc=%s", rc)
        
        def on_log(client, userdata, level, buf):
            _LOGGER.debug("📋 MQTT log: %s", buf)
        
        client = mqtt.Client(
            client_id=config[CONF_MQTT_CLIENT_ID],
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1
        )
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_log = on_log
        
        if config.get(CONF_MQTT_USERNAME):
            _LOGGER.info("🔐 Setting MQTT credentials for user: %s", config[CONF_MQTT_USERNAME])
            client.username_pw_set(
                config[CONF_MQTT_USERNAME], 
                config.get(CONF_MQTT_PASSWORD)
            )
        else:
            _LOGGER.info("🔓 No MQTT credentials provided - using anonymous connection")
        
        userdata = {'connected': False, 'rc': None}
        client.user_data_set(userdata)
        
        try:
            _LOGGER.info("🚀 Attempting MQTT connection...")
            await self.hass.async_add_executor_job(
                client.connect,
                config[CONF_MQTT_HOST],
                config[CONF_MQTT_PORT],
                15  # Increased keepalive timeout
            )
            
            # Wait for connection callback with longer timeout
            for i in range(100):  # 10 second timeout (increased from 5)
                if userdata['rc'] is not None:
                    break
                await asyncio.sleep(0.1)
                
                # Log progress every 2 seconds
                if i % 20 == 0 and i > 0:
                    _LOGGER.info("⏳ Still waiting for MQTT broker response... (%d seconds)", i // 10)
            
            if userdata['rc'] is None:
                raise Exception(
                    "⏰ MQTT connection timeout - no response from broker after 10 seconds. "
                    "This usually means:\n"
                    "1. MQTT broker is not running\n"
                    "2. Wrong host/IP address\n"
                    "3. Network firewall blocking connection\n"
                    "4. MQTT broker is overloaded or misconfigured"
                )
            
            if not userdata['connected']:
                error_messages = {
                    1: "Protocol version not supported - try updating MQTT broker",
                    2: "Client ID rejected - try changing the client ID", 
                    3: "MQTT broker unavailable - check broker status and logs",
                    4: "Invalid username or password - verify MQTT credentials",
                    5: "Authentication failed - check user permissions in MQTT broker"
                }
                error_msg = error_messages.get(userdata['rc'], f"Unknown MQTT error code {userdata['rc']}")
                raise Exception(f"🚫 MQTT connection failed: {error_msg}")
                
            _LOGGER.info("🎉 MQTT connection successful!")
            await self.hass.async_add_executor_job(client.disconnect)
            return True
            
        except Exception as exc:
            _LOGGER.error("💥 MQTT connection test failed: %s", exc)
            if "111" in str(exc) or "Connection refused" in str(exc):
                raise Exception(
                    f"🔌 MQTT broker not reachable at {config[CONF_MQTT_HOST]}:{config[CONF_MQTT_PORT]}. "
                    "Check if MQTT broker is running and accessible. "
                    "For Home Assistant Mosquitto add-on, try using 'core-mosquitto' as hostname."
                )
            elif "authentication" in str(exc).lower() or "4" in str(exc) or "5" in str(exc):
                raise Exception(
                    f"🔑 MQTT authentication failed. "
                    "Check username/password in MQTT broker settings."
                )
            elif "timeout" in str(exc).lower():
                raise Exception(
                    f"⏰ MQTT broker not responding. "
                    "This could be due to network issues, firewall, or broker being down. "
                    "Try restarting your MQTT broker."
                )
            else:
                raise Exception(f"🚨 MQTT connection failed: {exc}")
        finally:
            try:
                await self.hass.async_add_executor_job(client.loop_stop)
            except Exception:
                pass

    async def _comprehensive_mqtt_test(self, config):
        """Run comprehensive MQTT test using health checker."""
        _LOGGER.info("🏥 Running comprehensive MQTT health check...")
        
        # Create health checker
        health_checker = MQTTHealthChecker(self.hass)
        
        # Prepare config for health checker
        health_config = {
            "host": config[CONF_MQTT_HOST],
            "port": config[CONF_MQTT_PORT],
            "username": config.get(CONF_MQTT_USERNAME),
            "password": config.get(CONF_MQTT_PASSWORD),
            "client_id": config[CONF_MQTT_CLIENT_ID]
        }
        
        try:
            # Run health check
            results = await health_checker.comprehensive_mqtt_check(health_config)
            
            # Check overall status
            if results["overall_status"] == "passed":
                _LOGGER.info("✅ Comprehensive MQTT test passed")
                return True
            elif results["overall_status"] == "partial":
                _LOGGER.warning("⚠️ MQTT test passed with warnings")
                return True  # Still allow setup with warnings
            else:
                # Get specific error details
                failed_tests = [
                    test_name for test_name, test_result in results["tests"].items()
                    if not test_result.get("success", False)
                ]
                
                error_msg = f"MQTT health check failed: {', '.join(failed_tests)}"
                if results.get("recommendations"):
                    error_msg += f"\n\nRecommendations:\n" + "\n".join(f"• {rec}" for rec in results["recommendations"][:3])
                
                raise Exception(error_msg)
                
        except Exception as exc:
            _LOGGER.error("💥 Comprehensive MQTT test failed: %s", exc)
            raise

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

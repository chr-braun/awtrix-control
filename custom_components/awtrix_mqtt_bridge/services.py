"""Services for Awtrix MQTT Bridge."""
import logging
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.const import ATTR_ENTITY_ID

from .const import DOMAIN, CONF_MQTT_BASE_TOPIC
from .coordinator import AwtrixMqttCoordinator
from .mqtt_health_checker import MQTTHealthChecker

_LOGGER = logging.getLogger(__name__)

SERVICE_ADD_SENSOR_MAPPING = "add_sensor_mapping"
SERVICE_REMOVE_SENSOR_MAPPING = "remove_sensor_mapping" 
SERVICE_SEND_TO_AWTRIX = "send_to_awtrix"
SERVICE_CLEAR_ALL_MAPPINGS = "clear_all_mappings"
SERVICE_ADD_BULK_MAPPINGS = "add_bulk_mappings"
SERVICE_CREATE_TEMPLATE = "create_template"
SERVICE_MQTT_DIAGNOSTIC = "mqtt_diagnostic"
SERVICE_MQTT_HEALTH_CHECK = "mqtt_health_check"
SERVICE_GET_MQTT_LOGS = "get_mqtt_logs"

ADD_SENSOR_MAPPING_SCHEMA = vol.Schema({
    vol.Required("sensor_entity_id"): cv.entity_id,
    vol.Required("slot_id"): vol.Coerce(int),
    vol.Optional("display_name"): cv.string,
    vol.Optional("icon_id", default=1): vol.Coerce(int),
    vol.Optional("text_color", default="#ffffff"): cv.string,
    vol.Optional("text_effect", default="none"): vol.In(["none", "scroll", "fade", "blink", "rainbow"]),
    vol.Optional("display_duration", default=5): vol.Coerce(int),
    vol.Optional("text_format", default="{value}"): cv.string,
})

REMOVE_SENSOR_MAPPING_SCHEMA = vol.Schema({
    vol.Required("sensor_entity_id"): cv.entity_id,
})

BULK_MAPPING_SCHEMA = vol.Schema({
    vol.Required("template_name"): vol.In(["weather", "energy", "smart_home"]),
    vol.Optional("auto_discover", default=True): cv.boolean,
})

CREATE_TEMPLATE_SCHEMA = vol.Schema({
    vol.Required("template_name"): cv.string,
    vol.Required("mappings"): vol.All(cv.ensure_list, [vol.Schema({
        vol.Required("sensor_pattern"): cv.string,
        vol.Required("icon_id"): vol.Coerce(int),
        vol.Required("text_color"): cv.string,
        vol.Optional("text_effect", default="none"): vol.In(["none", "scroll", "fade", "blink", "rainbow"]),
        vol.Optional("text_format", default="{value}"): cv.string,
    })])
})

MQTT_DIAGNOSTIC_SCHEMA = vol.Schema({
    vol.Required("mqtt_host"): cv.string,
    vol.Optional("mqtt_port", default=1883): vol.Coerce(int),
    vol.Optional("mqtt_username"): cv.string,
    vol.Optional("mqtt_password"): cv.string,
})

MQTT_HEALTH_CHECK_SCHEMA = vol.Schema({
    vol.Required("mqtt_host"): cv.string,
    vol.Optional("mqtt_port", default=1883): vol.Coerce(int),
    vol.Optional("mqtt_username"): cv.string,
    vol.Optional("mqtt_password"): cv.string,
})

async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Awtrix MQTT Bridge."""
    
    async def add_sensor_mapping_service(call: ServiceCall) -> None:
        """Add sensor mapping service."""
        coordinators = [
            coordinator for coordinator in hass.data[DOMAIN].values()
            if isinstance(coordinator, AwtrixMqttCoordinator)
        ]
        
        if not coordinators:
            _LOGGER.error("No Awtrix coordinators found")
            return
            
        coordinator = coordinators[0]  # Use first coordinator
        
        sensor_entity_id = call.data["sensor_entity_id"]
        
        # Get sensor state to extract MQTT topic or construct it
        sensor_state = hass.states.get(sensor_entity_id)
        if not sensor_state:
            _LOGGER.error("Sensor %s not found", sensor_entity_id)
            return
        
        # Try to determine MQTT topic from sensor attributes or construct it
        mqtt_topic = sensor_state.attributes.get("mqtt_topic")
        if not mqtt_topic:
            # Construct MQTT topic for Home Assistant MQTT sensors
            # Format: homeassistant/sensor/sensor_name/state
            base_topic = coordinator.config.get(CONF_MQTT_BASE_TOPIC, "homeassistant")
            sensor_name = sensor_entity_id.replace("sensor.", "")
            mqtt_topic = f"{base_topic}/sensor/{sensor_name}/state"
            _LOGGER.debug("Constructed MQTT topic for %s: %s", sensor_entity_id, mqtt_topic)
            
        # Convert hex color to RGB list
        color_hex = call.data.get("text_color", "#ffffff")
        try:
            color_rgb = [
                int(color_hex[1:3], 16),
                int(color_hex[3:5], 16), 
                int(color_hex[5:7], 16)
            ]
        except ValueError:
            color_rgb = [255, 255, 255]  # Default white
        
        mapping = {
            "entity_id": sensor_entity_id,
            "slot_id": call.data["slot_id"],
            "display_name": call.data.get("display_name", sensor_state.name),
            "icon": call.data.get("icon_id", 1),
            "color": color_rgb,
            "effect": call.data.get("text_effect", "none"),
            "duration": call.data.get("display_duration", 5),
            "format": call.data.get("text_format", "{value}"),
            "mqtt_topic": sensor_state.attributes.get("mqtt_topic", ""),
        }
        
        await coordinator.add_sensor_mapping(sensor_entity_id, mapping)
    
    async def remove_sensor_mapping_service(call: ServiceCall) -> None:
        """Remove sensor mapping service."""
        coordinators = [
            coordinator for coordinator in hass.data[DOMAIN].values()
            if isinstance(coordinator, AwtrixMqttCoordinator)
        ]
        
        if coordinators:
            coordinator = coordinators[0]
            sensor_entity_id = call.data["sensor_entity_id"] 
            await coordinator.remove_sensor_mapping(sensor_entity_id)
    
    async def send_to_awtrix_service(call: ServiceCall) -> None:
        """Send all mappings to Awtrix service."""
        coordinators = [
            coordinator for coordinator in hass.data[DOMAIN].values()
            if isinstance(coordinator, AwtrixMqttCoordinator)
        ]
        
        if coordinators:
            coordinator = coordinators[0]
            # Trigger update of all sensor mappings
            for sensor_id, mapping in coordinator.sensor_mappings.items():
                sensor_state = hass.states.get(sensor_id)
                if sensor_state:
                    await coordinator._send_to_awtrix(sensor_id, sensor_state.state, mapping)
    
    async def clear_all_mappings_service(call: ServiceCall) -> None:
        """Clear all mappings service."""
        coordinators = [
            coordinator for coordinator in hass.data[DOMAIN].values()
            if isinstance(coordinator, AwtrixMqttCoordinator)
        ]
        
        if coordinators:
            coordinator = coordinators[0]
            coordinator.sensor_mappings.clear()
            _LOGGER.info("Cleared all sensor mappings")
    
    async def add_bulk_mappings_service(call: ServiceCall) -> None:
        """Add bulk mappings based on template."""
        coordinators = [
            coordinator for coordinator in hass.data[DOMAIN].values()
            if isinstance(coordinator, AwtrixMqttCoordinator)
        ]
        
        if not coordinators:
            _LOGGER.error("No Awtrix coordinators found")
            return
            
        coordinator = coordinators[0]
        template_name = call.data["template_name"]
        auto_discover = call.data.get("auto_discover", True)
        
        # Define templates
        templates = {
            "weather": [
                {"pattern": "temperature", "icon": 2109, "color": "#ff6b35", "effect": "none", "format": "{value}°C"},
                {"pattern": "humidity", "icon": 51658, "color": "#4a90e2", "effect": "none", "format": "{value}%"},
                {"pattern": "pressure", "icon": 888, "color": "#ffffff", "effect": "none", "format": "{value} hPa"}
            ],
            "energy": [
                {"pattern": "power", "icon": 2114, "color": "#f7ca18", "effect": "scroll", "format": "{value}W"},
                {"pattern": "solar", "icon": 2422, "color": "#2ecc71", "effect": "fade", "format": "{value}W"},
                {"pattern": "battery", "icon": 120, "color": "#e74c3c", "effect": "blink", "format": "{value}%"}
            ],
            "smart_home": [
                {"pattern": "motion", "icon": 1712, "color": "#9b59b6", "effect": "blink", "format": "{value}"},
                {"pattern": "door", "icon": 1465, "color": "#34495e", "effect": "none", "format": "{value}"},
                {"pattern": "light", "icon": 1762, "color": "#f39c12", "effect": "fade", "format": "{value}"}
            ]
        }
        
        template = templates.get(template_name)
        if not template:
            _LOGGER.error("Unknown template: %s", template_name)
            return
        
        if auto_discover:
            # Auto-discover sensors based on patterns
            available_sensors = [
                entity_id for entity_id in hass.states.async_entity_ids("sensor")
            ]
            
            slot_id = 1
            for sensor_template in template:
                # Find matching sensors
                matching_sensors = [
                    entity_id for entity_id in available_sensors
                    if sensor_template["pattern"].lower() in entity_id.lower()
                ]
                
                for sensor_id in matching_sensors[:1]:  # Take first match
                    if slot_id > 8:  # Max 8 slots
                        break
                        
                    # Add mapping
                    sensor_state = hass.states.get(sensor_id)
                    if sensor_state:
                        # Convert hex color to RGB
                        color_hex = sensor_template["color"]
                        try:
                            color_rgb = [
                                int(color_hex[1:3], 16),
                                int(color_hex[3:5], 16),
                                int(color_hex[5:7], 16)
                            ]
                        except ValueError:
                            color_rgb = [255, 255, 255]
                        
                        mapping = {
                            "entity_id": sensor_id,
                            "slot_id": slot_id,
                            "display_name": sensor_template["pattern"].capitalize(),
                            "icon": sensor_template["icon"],
                            "color": color_rgb,
                            "effect": sensor_template["effect"],
                            "duration": 5,
                            "format": sensor_template["format"],
                            "mqtt_topic": sensor_state.attributes.get("mqtt_topic", ""),
                        }
                        
                        await coordinator.add_sensor_mapping(sensor_id, mapping)
                        slot_id += 1
            
            _LOGGER.info("Applied template %s with %d mappings", template_name, slot_id - 1)
    
    async def create_template_service(call: ServiceCall) -> None:
        """Create custom template service."""
        # This would store custom templates - for now just log
        template_name = call.data["template_name"]
        mappings = call.data["mappings"]
        
        _LOGGER.info("Created custom template %s with %d mappings", template_name, len(mappings))
    async def mqtt_diagnostic_service(call: ServiceCall) -> None:
        """MQTT diagnostic service to test connection independently."""
        import paho.mqtt.client as mqtt
        import socket
        import asyncio
        
        host = call.data["mqtt_host"]
        port = call.data.get("mqtt_port", 1883)
        username = call.data.get("mqtt_username")
        password = call.data.get("mqtt_password")
        
        _LOGGER.info("🔍 MQTT Diagnostic Test Starting...")
        _LOGGER.info("Host: %s, Port: %s, Username: %s", host, port, username or "(none)")
        
        # Test 1: Network connectivity
        try:
            _LOGGER.info("🌐 Testing network connectivity...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                _LOGGER.info("✅ Network connectivity OK")
            else:
                _LOGGER.error("❌ Network connectivity FAILED - Port %s not reachable on %s", port, host)
                return
        except Exception as exc:
            _LOGGER.error("❌ Network test exception: %s", exc)
            return
        
        # Test 2: MQTT protocol test
        try:
            _LOGGER.info("🔗 Testing MQTT protocol...")
            
            connection_result = {"connected": False, "rc": None, "error": None}
            
            def on_connect(client, userdata, flags, rc):
                _LOGGER.info("📥 MQTT Connect callback: rc=%s", rc)
                userdata["connected"] = rc == 0
                userdata["rc"] = rc
                
                error_messages = {
                    0: "✅ Connection successful",
                    1: "❌ Protocol version not supported",
                    2: "❌ Client ID rejected",
                    3: "❌ Server unavailable",
                    4: "❌ Bad username/password",
                    5: "❌ Not authorized"
                }
                _LOGGER.info(error_messages.get(rc, f"❌ Unknown error {rc}"))
            
            def on_log(client, userdata, level, buf):
                _LOGGER.debug("MQTT Log: %s", buf)
            
            client = mqtt.Client(
                client_id="awtrix_diagnostic_test",
                callback_api_version=mqtt.CallbackAPIVersion.VERSION1
            )
            client.on_connect = on_connect
            client.on_log = on_log
            client.user_data_set(connection_result)
            
            if username:
                _LOGGER.info("🔐 Setting credentials...")
                client.username_pw_set(username, password)
            
            # Connect
            await hass.async_add_executor_job(client.connect, host, port, 10)
            
            # Wait for response
            for _ in range(50):  # 5 second timeout
                if connection_result["rc"] is not None:
                    break
                await asyncio.sleep(0.1)
            
            if connection_result["rc"] is None:
                _LOGGER.error("❌ MQTT connection timeout")
            elif connection_result["connected"]:
                _LOGGER.info("🎉 MQTT Diagnostic PASSED - Connection successful!")
                
                # Test publish
                try:
                    await hass.async_add_executor_job(
                        client.publish, "awtrix_test/diagnostic", "Hello from Awtrix Bridge!"
                    )
                    _LOGGER.info("📤 Test message published successfully")
                except Exception as pub_exc:
                    _LOGGER.error("❌ Publish test failed: %s", pub_exc)
            else:
                _LOGGER.error("❌ MQTT Diagnostic FAILED - Check the error above")
            
            # Cleanup
            try:
                await hass.async_add_executor_job(client.disconnect)
            except Exception:
                pass
                
        except Exception as exc:
            _LOGGER.error("❌ MQTT diagnostic exception: %s", exc)
    
    async def mqtt_health_check_service(call: ServiceCall) -> None:
        """Comprehensive MQTT health check service."""
        _LOGGER.info("🏥 Starting comprehensive MQTT health check...")
        
        # Create health checker instance
        health_checker = MQTTHealthChecker(hass)
        
        # Prepare configuration
        config = {
            "host": call.data["mqtt_host"],
            "port": call.data.get("mqtt_port", 1883),
            "username": call.data.get("mqtt_username"),
            "password": call.data.get("mqtt_password"),
            "client_id": "awtrix_health_check"
        }
        
        try:
            # Run comprehensive health check
            results = await health_checker.comprehensive_mqtt_check(config)
            
            # Log summary
            status = results["overall_status"]
            if status == "passed":
                _LOGGER.info("🎉 MQTT Health Check PASSED - All tests successful!")
            elif status == "partial":
                _LOGGER.warning("⚠️ MQTT Health Check PARTIAL - Some issues detected")
            else:
                _LOGGER.error("❌ MQTT Health Check FAILED - Critical issues found")
            
            # Log test results summary
            for test_name, test_result in results["tests"].items():
                success = test_result.get("success", False)
                duration = test_result.get("duration_seconds", 0)
                status_icon = "✅" if success else "❌"
                _LOGGER.info(f"{status_icon} {test_name.replace('_', ' ').title()}: {duration:.2f}s")
            
            # Log recommendations if any
            if results.get("recommendations"):
                _LOGGER.info("💡 Recommendations:")
                for rec in results["recommendations"]:
                    _LOGGER.info(f"  • {rec}")
            
            # Log file path for detailed results
            log_path = health_checker.get_log_file_path()
            _LOGGER.info(f"📄 Detailed results saved to: {log_path}")
            
        except Exception as exc:
            _LOGGER.error("💥 Health check failed with exception: %s", exc)
    
    async def get_mqtt_logs_service(call: ServiceCall) -> None:
        """Get MQTT diagnostic logs service."""
        health_checker = MQTTHealthChecker(hass)
        log_path = health_checker.get_log_file_path()
        
        try:
            # Get last results from storage
            last_results = await health_checker.get_last_results()
            
            if last_results:
                timestamp = last_results.get("timestamp", "Unknown")
                status = last_results.get("overall_status", "Unknown")
                _LOGGER.info(f"📊 Last health check: {timestamp} - Status: {status}")
                
                # Log summary of last results
                if "tests" in last_results:
                    for test_name, test_result in last_results["tests"].items():
                        success = test_result.get("success", False)
                        status_icon = "✅" if success else "❌"
                        _LOGGER.info(f"{status_icon} {test_name.replace('_', ' ').title()}")
            else:
                _LOGGER.info("ℹ️ No previous health check results found")
                
            _LOGGER.info(f"📄 Full diagnostic log available at: {log_path}")
            
            # Check if log file exists and show recent entries
            try:
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        _LOGGER.info("📋 Recent log entries (last 10 lines):")
                        for line in lines[-10:]:
                            _LOGGER.info(f"  {line.strip()}")
                    else:
                        _LOGGER.info("📄 Log file is empty")
            except FileNotFoundError:
                _LOGGER.info("📄 Log file not found - run health check first")
            except Exception as exc:
                _LOGGER.error(f"❌ Error reading log file: {exc}")
                
        except Exception as exc:
            _LOGGER.error(f"💥 Error retrieving logs: {exc}")
    
    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_SENSOR_MAPPING,
        add_sensor_mapping_service,
        schema=ADD_SENSOR_MAPPING_SCHEMA
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_SENSOR_MAPPING,
        remove_sensor_mapping_service,
        schema=REMOVE_SENSOR_MAPPING_SCHEMA
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_TO_AWTRIX,
        send_to_awtrix_service
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_ALL_MAPPINGS,
        clear_all_mappings_service
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_BULK_MAPPINGS,
        add_bulk_mappings_service,
        schema=BULK_MAPPING_SCHEMA
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_TEMPLATE,
        create_template_service,
        schema=CREATE_TEMPLATE_SCHEMA
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_MQTT_DIAGNOSTIC,
        mqtt_diagnostic_service,
        schema=MQTT_DIAGNOSTIC_SCHEMA
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_MQTT_HEALTH_CHECK,
        mqtt_health_check_service,
        schema=MQTT_HEALTH_CHECK_SCHEMA
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_MQTT_LOGS,
        get_mqtt_logs_service
    )

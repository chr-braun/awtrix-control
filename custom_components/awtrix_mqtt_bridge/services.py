"""Services for Awtrix MQTT Bridge."""
import logging
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.const import ATTR_ENTITY_ID

from .const import DOMAIN, CONF_MQTT_BASE_TOPIC
from .coordinator import AwtrixMqttCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_ADD_SENSOR_MAPPING = "add_sensor_mapping"
SERVICE_REMOVE_SENSOR_MAPPING = "remove_sensor_mapping" 
SERVICE_SEND_TO_AWTRIX = "send_to_awtrix"
SERVICE_CLEAR_ALL_MAPPINGS = "clear_all_mappings"
SERVICE_ADD_BULK_MAPPINGS = "add_bulk_mappings"
SERVICE_CREATE_TEMPLATE = "create_template"

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
        # In a real implementation, you'd store this in a file or database
    
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

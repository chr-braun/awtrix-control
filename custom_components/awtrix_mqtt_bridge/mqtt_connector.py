"""
Robust MQTT Connector for Awtrix MQTT Bridge
Handles multiple authentication scenarios with automatic fallback options.
"""

import logging
import asyncio
import socket
import time
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum

import paho.mqtt.client as mqtt
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

class AuthMethod(Enum):
    """MQTT Authentication methods."""
    CREDENTIALS = "credentials"
    ANONYMOUS = "anonymous"
    AUTO_DETECT = "auto_detect"

class MQTTConnectionResult:
    """Result of MQTT connection attempt."""
    
    def __init__(self, success: bool, method: AuthMethod, host: str, port: int, 
                 error: Optional[str] = None, return_code: Optional[int] = None,
                 duration: Optional[float] = None):
        self.success = success
        self.method = method
        self.host = host
        self.port = port
        self.error = error
        self.return_code = return_code
        self.duration = duration

class RobustMQTTConnector:
    """Robust MQTT connector with automatic fallback and authentication detection."""
    
    def __init__(self, hass: HomeAssistant):
        """Initialize the MQTT connector."""
        self.hass = hass
        self._test_timeout = 15
        self._connection_timeout = 10
        
    async def test_connection(self, config: Dict[str, Any]) -> MQTTConnectionResult:
        """
        Test MQTT connection with automatic fallback options.
        
        Args:
            config: Configuration dictionary with MQTT settings
            
        Returns:
            MQTTConnectionResult with detailed connection information
        """
        _LOGGER.info("🚀 Starting robust MQTT connection test...")
        
        # Step 1: Test network connectivity
        network_result = await self._test_network_connectivity(
            config["host"], config.get("port", 1883)
        )
        
        if not network_result:
            return MQTTConnectionResult(
                success=False, method=AuthMethod.AUTO_DETECT,
                host=config["host"], port=config.get("port", 1883),
                error="Network connectivity failed - broker unreachable"
            )
        
        # Step 2: Try different authentication methods
        auth_methods = self._determine_auth_methods(config)
        
        for method in auth_methods:
            _LOGGER.info(f"🔑 Trying authentication method: {method.value}")
            
            result = await self._test_auth_method(config, method)
            
            if result.success:
                _LOGGER.info(f"✅ Connection successful with {method.value}")
                return result
            else:
                _LOGGER.warning(f"❌ {method.value} failed: {result.error}")
        
        # If all methods failed, return the last result with recommendations
        return MQTTConnectionResult(
            success=False, method=AuthMethod.AUTO_DETECT,
            host=config["host"], port=config.get("port", 1883),
            error="All authentication methods failed - check broker configuration"
        )
    
    async def find_working_broker(self, primary_config: Dict[str, Any]) -> Optional[MQTTConnectionResult]:
        """
        Find a working MQTT broker by testing multiple endpoints.
        
        Args:
            primary_config: Primary configuration to test
            
        Returns:
            MQTTConnectionResult for working broker or None
        """
        _LOGGER.info("🔍 Searching for working MQTT broker...")
        
        # Generate broker candidates
        broker_candidates = self._generate_broker_candidates(primary_config)
        
        for candidate in broker_candidates:
            _LOGGER.info(f"🧪 Testing broker: {candidate['host']}:{candidate['port']}")
            
            # Test network connectivity first
            if not await self._test_network_connectivity(candidate["host"], candidate["port"]):
                _LOGGER.debug(f"❌ {candidate['host']}:{candidate['port']} not reachable")
                continue
            
            # Test MQTT connection
            result = await self.test_connection(candidate)
            
            if result.success:
                _LOGGER.info(f"✅ Found working broker: {candidate['host']}:{candidate['port']} ({result.method.value})")
                return result
        
        _LOGGER.error("❌ No working MQTT broker found")
        return None
    
    def _determine_auth_methods(self, config: Dict[str, Any]) -> List[AuthMethod]:
        """Determine which authentication methods to try in order."""
        methods = []
        
        # If credentials provided, try them first
        if config.get("username") and config.get("password"):
            methods.append(AuthMethod.CREDENTIALS)
        
        # Always try anonymous as fallback
        methods.append(AuthMethod.ANONYMOUS)
        
        return methods
    
    def _generate_broker_candidates(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate list of broker candidates to test."""
        candidates = []
        
        # Primary configuration
        primary = {
            "host": config["host"],
            "port": config.get("port", 1883),
            "username": config.get("username"),
            "password": config.get("password"),
            "client_id": config.get("client_id", "awtrix_mqtt_bridge"),
            "priority": 1,
            "description": f"Primary broker ({config['host']})"
        }
        candidates.append(primary)
        
        # If primary is localhost or 127.0.0.1, try HA add-on
        if config["host"] in ["localhost", "127.0.0.1"]:
            candidates.extend([
                {
                    "host": "core-mosquitto",
                    "port": 1883,
                    "username": config.get("username"),
                    "password": config.get("password"),
                    "client_id": config.get("client_id", "awtrix_mqtt_bridge"),
                    "priority": 2,
                    "description": "Home Assistant Mosquitto add-on"
                },
                {
                    "host": "homeassistant.local",
                    "port": 1883,
                    "username": config.get("username"),
                    "password": config.get("password"),
                    "client_id": config.get("client_id", "awtrix_mqtt_bridge"),
                    "priority": 3,
                    "description": "Home Assistant host"
                }
            ])
        
        # Sort by priority
        candidates.sort(key=lambda x: x["priority"])
        
        return candidates
    
    async def _test_network_connectivity(self, host: str, port: int) -> bool:
        """Test basic network connectivity to broker."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            return result == 0
        except Exception as exc:
            _LOGGER.debug(f"Network test failed for {host}:{port}: {exc}")
            return False
    
    async def _test_auth_method(self, config: Dict[str, Any], method: AuthMethod) -> MQTTConnectionResult:
        """Test specific authentication method."""
        start_time = time.time()
        
        # Prepare connection parameters based on method
        if method == AuthMethod.CREDENTIALS:
            username = config.get("username")
            password = config.get("password")
            if not username:
                return MQTTConnectionResult(
                    success=False, method=method,
                    host=config["host"], port=config.get("port", 1883),
                    error="No credentials provided"
                )
        else:  # ANONYMOUS
            username = None
            password = None
        
        connection_result = {"connected": False, "rc": None, "flags": None}
        
        def on_connect(client, userdata, flags, rc):
            userdata["connected"] = rc == 0
            userdata["rc"] = rc
            userdata["flags"] = flags
            
            error_messages = {
                0: "Connection successful",
                1: "Protocol version not supported",
                2: "Client ID rejected",
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized"
            }
            _LOGGER.debug(f"MQTT connect result: {error_messages.get(rc, f'Unknown error {rc}')}")
        
        try:
            # Create MQTT client
            client_id = config.get("client_id", f"awtrix_test_{int(time.time())}")
            
            try:
                client = mqtt.Client(
                    client_id=client_id,
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION1
                )
            except (AttributeError, TypeError):
                # Fallback for older paho-mqtt versions
                client = mqtt.Client(client_id=client_id)
            
            client.on_connect = on_connect
            client.user_data_set(connection_result)
            
            # Set credentials if using credential method
            if method == AuthMethod.CREDENTIALS and username:
                client.username_pw_set(username, password)
                _LOGGER.debug(f"Set credentials for user: {username}")
            else:
                _LOGGER.debug("Using anonymous connection")
            
            # Attempt connection
            await self.hass.async_add_executor_job(
                client.connect,
                config["host"],
                config.get("port", 1883),
                self._connection_timeout
            )
            
            # Wait for connection result
            for i in range(self._test_timeout * 10):
                if connection_result["rc"] is not None:
                    break
                await asyncio.sleep(0.1)
            
            duration = time.time() - start_time
            
            # Clean up
            try:
                await self.hass.async_add_executor_job(client.disconnect)
            except Exception:
                pass
            
            # Evaluate result
            if connection_result["rc"] is None:
                return MQTTConnectionResult(
                    success=False, method=method,
                    host=config["host"], port=config.get("port", 1883),
                    error="Connection timeout - no response from broker",
                    duration=duration
                )
            
            if connection_result["connected"]:
                return MQTTConnectionResult(
                    success=True, method=method,
                    host=config["host"], port=config.get("port", 1883),
                    return_code=connection_result["rc"],
                    duration=duration
                )
            else:
                error_descriptions = {
                    1: "Protocol version not supported by broker",
                    2: "Client identifier rejected by broker",
                    3: "MQTT service unavailable",
                    4: "Bad username or password",
                    5: "Not authorized to connect"
                }
                error_desc = error_descriptions.get(
                    connection_result["rc"], 
                    f"Unknown error code {connection_result['rc']}"
                )
                
                return MQTTConnectionResult(
                    success=False, method=method,
                    host=config["host"], port=config.get("port", 1883),
                    error=error_desc,
                    return_code=connection_result["rc"],
                    duration=duration
                )
                
        except Exception as exc:
            duration = time.time() - start_time
            return MQTTConnectionResult(
                success=False, method=method,
                host=config["host"], port=config.get("port", 1883),
                error=str(exc),
                duration=duration
            )
    
    def get_connection_recommendations(self, config: Dict[str, Any], results: List[MQTTConnectionResult]) -> List[str]:
        """Generate recommendations based on connection test results."""
        recommendations = []
        
        # Analyze failed attempts
        has_auth_failure = any(r.return_code in [4, 5] for r in results if not r.success)
        has_network_failure = any("network" in (r.error or "").lower() for r in results if not r.success)
        has_timeout = any("timeout" in (r.error or "").lower() for r in results if not r.success)
        
        if has_auth_failure:
            recommendations.extend([
                "Check MQTT broker user configuration",
                "Verify username and password are correct",
                "Try enabling anonymous access in broker settings",
                "Check user permissions and ACL settings"
            ])
        
        if has_network_failure:
            recommendations.extend([
                "Verify MQTT broker is running and accessible",
                "Check firewall settings on port 1883",
                "Ensure correct IP address or hostname",
                "Test network connectivity with ping/telnet"
            ])
        
        if has_timeout:
            recommendations.extend([
                "Check if MQTT broker service is running",
                "Verify broker is not overloaded",
                "Check network latency and stability",
                "Increase connection timeout if needed"
            ])
        
        # Host-specific recommendations
        if config["host"] in ["localhost", "127.0.0.1"]:
            recommendations.extend([
                "Start Home Assistant Mosquitto add-on",
                "Use 'core-mosquitto' as hostname for HA add-on",
                "Check add-on configuration and logs"
            ])
        
        return list(set(recommendations))  # Remove duplicates
        
    async def detect_broker_type(self, host: str, port: int = 1883) -> str:
        """Detect the type of MQTT broker for tailored authentication."""
        try:
            # Check if it's a Home Assistant Mosquitto add-on
            if host in ["core-mosquitto", "mosquitto"]:
                return "ha_mosquitto"
            
            # Check if it's a local/localhost broker
            if host in ["localhost", "127.0.0.1"]:
                return "local_mosquitto"
            
            # Check if it's a router/external broker (like FritzBox)
            if host.startswith("192.168.") or host.startswith("10.") or host.startswith("172."):
                return "router_mqtt"
                
            return "unknown"
        except Exception:
            return "unknown"
    
    async def test_credentials_specifically(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test specific credential scenarios based on user's setup."""
        _LOGGER.info("🧪 Testing specific credential scenarios for biber/2203801826...")
        
        broker_type = await self.detect_broker_type(config["host"], config.get("port", 1883))
        _LOGGER.info(f"🏠 Detected broker type: {broker_type}")
        
        test_scenarios = []
        
        if broker_type == "ha_mosquitto":
            # Home Assistant Mosquitto scenarios - test both common credentials
            test_scenarios = [
                {"method": "credentials", "username": "biber", "password": "2203801826", "description": "HA Mosquitto with biber user"},
                {"method": "credentials", "username": config.get("username"), "password": config.get("password"), "description": f"HA Mosquitto with {config.get('username', 'provided')} user"},
                {"method": "anonymous", "username": None, "password": None, "description": "HA Mosquitto anonymous"},
            ]
            # Remove duplicate scenarios if user provided biber credentials
            if config.get("username") == "biber":
                test_scenarios = test_scenarios[:1] + test_scenarios[2:]
        elif broker_type == "router_mqtt":
            # Router MQTT scenarios
            test_scenarios = [
                {"method": "anonymous", "username": None, "password": None, "description": "Router MQTT anonymous (most likely)"},
                {"method": "credentials", "username": "biber", "password": "2203801826", "description": "Router MQTT with credentials"},
                {"method": "credentials", "username": "admin", "password": "2203801826", "description": "Router MQTT with admin user"},
            ]
        else:
            # Generic scenarios
            test_scenarios = [
                {"method": "credentials", "username": "biber", "password": "2203801826", "description": "Provided credentials"},
                {"method": "anonymous", "username": None, "password": None, "description": "Anonymous connection"},
            ]
        
        results = []
        
        for scenario in test_scenarios:
            _LOGGER.info(f"🧪 Testing: {scenario['description']}")
            
            test_config = config.copy()
            test_config["username"] = scenario["username"]
            test_config["password"] = scenario["password"]
            
            method = AuthMethod.CREDENTIALS if scenario["method"] == "credentials" else AuthMethod.ANONYMOUS
            result = await self._test_auth_method(test_config, method)
            
            results.append({
                "scenario": scenario["description"],
                "method": scenario["method"],
                "success": result.success,
                "error": result.error,
                "return_code": result.return_code,
                "duration": result.duration
            })
            
            if result.success:
                _LOGGER.info(f"✅ SUCCESS: {scenario['description']} worked!")
                break
            else:
                _LOGGER.warning(f"❌ FAILED: {scenario['description']} - {result.error}")
        
        return {
            "broker_type": broker_type,
            "scenarios_tested": len(test_scenarios),
            "results": results,
            "success": any(r["success"] for r in results)
        }
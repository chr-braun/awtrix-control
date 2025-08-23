"""
MQTT Health Check and Diagnostic Service for Awtrix MQTT Bridge
This module provides comprehensive MQTT connectivity testing and logging.
"""

import logging
import asyncio
import socket
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import paho.mqtt.client as mqtt
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class MQTTHealthChecker:
    """Comprehensive MQTT health checker with detailed logging."""
    
    def __init__(self, hass: HomeAssistant):
        """Initialize the MQTT health checker."""
        self.hass = hass
        self.store = Store(hass, 1, f"{DOMAIN}_mqtt_diagnostics")
        self.log_file_path = Path(hass.config.config_dir) / "custom_components" / "awtrix_mqtt_bridge" / "mqtt_diagnostics.log"
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup dedicated logger for MQTT diagnostics
        self.mqtt_logger = logging.getLogger(f"{DOMAIN}.mqtt_diagnostics")
        self.mqtt_logger.setLevel(logging.DEBUG)
        
        # Create file handler if not exists
        if not self.mqtt_logger.handlers:
            file_handler = logging.FileHandler(self.log_file_path)
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - [MQTT Diagnostic] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            self.mqtt_logger.addHandler(file_handler)
            
        self.mqtt_logger.info("🚀 MQTT Health Checker initialized")
    
    async def comprehensive_mqtt_check(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive MQTT connectivity check.
        
        Args:
            config: MQTT configuration dictionary
            
        Returns:
            Dictionary with detailed check results
        """
        self.mqtt_logger.info("=" * 60)
        self.mqtt_logger.info("🔍 Starting comprehensive MQTT health check")
        self.mqtt_logger.info(f"Target: {config.get('host')}:{config.get('port', 1883)}")
        self.mqtt_logger.info(f"Username: {config.get('username', 'anonymous')}")
        self.mqtt_logger.info("=" * 60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "host": config.get("host"),
                "port": config.get("port", 1883),
                "username": config.get("username"),
                "has_password": bool(config.get("password")),
                "client_id": config.get("client_id", "awtrix_health_check")
            },
            "tests": {},
            "overall_status": "unknown",
            "recommendations": []
        }
        
        # Test 1: Network Connectivity
        network_result = await self._test_network_connectivity(config)
        results["tests"]["network"] = network_result
        
        if not network_result["success"]:
            results["overall_status"] = "failed"
            results["recommendations"].extend(network_result.get("recommendations", []))
            await self._save_results(results)
            return results
        
        # Test 2: MQTT Protocol Connection
        mqtt_result = await self._test_mqtt_protocol(config)
        results["tests"]["mqtt_protocol"] = mqtt_result
        
        if not mqtt_result["success"]:
            results["overall_status"] = "failed"
            results["recommendations"].extend(mqtt_result.get("recommendations", []))
            await self._save_results(results)
            return results
        
        # Test 3: Authentication
        auth_result = await self._test_authentication(config)
        results["tests"]["authentication"] = auth_result
        
        # Test 4: Publish/Subscribe Test
        pubsub_result = await self._test_publish_subscribe(config)
        results["tests"]["publish_subscribe"] = pubsub_result
        
        # Test 5: Connection Stability
        stability_result = await self._test_connection_stability(config)
        results["tests"]["stability"] = stability_result
        
        # Determine overall status
        all_tests_passed = all(
            test["success"] for test in results["tests"].values()
        )
        results["overall_status"] = "passed" if all_tests_passed else "partial"
        
        # Generate recommendations
        if results["overall_status"] != "passed":
            results["recommendations"] = self._generate_recommendations(results)
        
        self.mqtt_logger.info(f"✅ Health check completed - Status: {results['overall_status']}")
        await self._save_results(results)
        
        return results
    
    async def _test_network_connectivity(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test basic network connectivity to MQTT broker."""
        self.mqtt_logger.info("🌐 Testing network connectivity...")
        
        host = config.get("host")
        port = config.get("port", 1883)
        
        start_time = time.time()
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((host, port))
            sock.close()
            
            duration = time.time() - start_time
            
            if result == 0:
                self.mqtt_logger.info(f"✅ Network connectivity OK ({duration:.2f}s)")
                return {
                    "success": True,
                    "duration_seconds": duration,
                    "message": f"Successfully connected to {host}:{port}",
                    "details": {
                        "host_resolved": True,
                        "port_accessible": True,
                        "response_time": duration
                    }
                }
            else:
                self.mqtt_logger.error(f"❌ Network connectivity failed - Connection refused (code: {result})")
                return {
                    "success": False,
                    "duration_seconds": duration,
                    "error": f"Connection refused to {host}:{port}",
                    "error_code": result,
                    "recommendations": [
                        "Check if MQTT broker is running",
                        "Verify the IP address and port",
                        "Check firewall settings",
                        "Ensure network connectivity between devices"
                    ]
                }
                
        except socket.gaierror as exc:
            duration = time.time() - start_time
            self.mqtt_logger.error(f"❌ DNS resolution failed: {exc}")
            return {
                "success": False,
                "duration_seconds": duration,
                "error": f"DNS resolution failed: {exc}",
                "recommendations": [
                    "Check if hostname is correct",
                    "Try using IP address instead of hostname",
                    "Check DNS settings"
                ]
            }
        except Exception as exc:
            duration = time.time() - start_time
            self.mqtt_logger.error(f"❌ Network test failed: {exc}")
            return {
                "success": False,
                "duration_seconds": duration,
                "error": str(exc),
                "recommendations": [
                    "Check network connectivity",
                    "Verify firewall settings",
                    "Ensure correct host and port"
                ]
            }
    
    async def _test_mqtt_protocol(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test MQTT protocol connection."""
        self.mqtt_logger.info("🔗 Testing MQTT protocol connection...")
        
        connection_result = {"connected": False, "rc": None, "flags": None}
        start_time = time.time()
        
        def on_connect(client, userdata, flags, rc):
            self.mqtt_logger.info(f"📥 MQTT connect callback: rc={rc}, flags={flags}")
            userdata["connected"] = rc == 0
            userdata["rc"] = rc
            userdata["flags"] = flags
            
            error_messages = {
                0: "✅ Connection successful",
                1: "❌ Protocol version not supported",
                2: "❌ Client ID rejected",
                3: "❌ Server unavailable", 
                4: "❌ Bad username or password",
                5: "❌ Not authorized"
            }
            self.mqtt_logger.info(error_messages.get(rc, f"❌ Unknown error {rc}"))
        
        def on_disconnect(client, userdata, rc):
            self.mqtt_logger.info(f"📤 MQTT disconnect: rc={rc}")
        
        try:
            client = mqtt.Client(
                client_id=config.get("client_id", "awtrix_health_check"),
                callback_api_version=mqtt.CallbackAPIVersion.VERSION1
            )
            client.on_connect = on_connect
            client.on_disconnect = on_disconnect
            client.user_data_set(connection_result)
            
            # Set credentials if provided
            if config.get("username"):
                client.username_pw_set(config["username"], config.get("password"))
                self.mqtt_logger.info(f"🔐 Credentials set for user: {config['username']}")
            else:
                self.mqtt_logger.info("🔓 Using anonymous connection")
            
            # Attempt connection
            await self.hass.async_add_executor_job(
                client.connect,
                config["host"],
                config.get("port", 1883),
                15
            )
            
            # Wait for connection result
            timeout_seconds = 15
            for i in range(timeout_seconds * 10):
                if connection_result["rc"] is not None:
                    break
                await asyncio.sleep(0.1)
                
                if i % 20 == 0 and i > 0:
                    self.mqtt_logger.info(f"⏳ Still waiting for MQTT response... ({i // 10}s)")
            
            duration = time.time() - start_time
            
            if connection_result["rc"] is None:
                self.mqtt_logger.error("⏰ MQTT protocol test timeout")
                return {
                    "success": False,
                    "duration_seconds": duration,
                    "error": "Connection timeout - no response from broker",
                    "recommendations": [
                        "Check if MQTT broker is running",
                        "Verify broker configuration",
                        "Check for network issues"
                    ]
                }
            
            if connection_result["connected"]:
                self.mqtt_logger.info(f"🎉 MQTT protocol test successful ({duration:.2f}s)")
                await self.hass.async_add_executor_job(client.disconnect)
                return {
                    "success": True,
                    "duration_seconds": duration,
                    "message": "MQTT protocol connection successful",
                    "details": {
                        "return_code": connection_result["rc"],
                        "flags": connection_result["flags"]
                    }
                }
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
                
                self.mqtt_logger.error(f"❌ MQTT protocol test failed: {error_desc}")
                return {
                    "success": False,
                    "duration_seconds": duration,
                    "error": error_desc,
                    "error_code": connection_result["rc"],
                    "recommendations": self._get_error_recommendations(connection_result["rc"])
                }
                
        except Exception as exc:
            duration = time.time() - start_time
            self.mqtt_logger.error(f"💥 MQTT protocol test exception: {exc}")
            return {
                "success": False,
                "duration_seconds": duration,
                "error": str(exc),
                "recommendations": [
                    "Check MQTT broker configuration",
                    "Verify network connectivity",
                    "Check for firewall blocking"
                ]
            }
        finally:
            try:
                await self.hass.async_add_executor_job(client.loop_stop)
            except Exception:
                pass
    
    async def _test_authentication(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test MQTT authentication specifically."""
        self.mqtt_logger.info("🔐 Testing MQTT authentication...")
        
        if not config.get("username"):
            self.mqtt_logger.info("ℹ️ No credentials provided - skipping auth test")
            return {
                "success": True,
                "message": "Anonymous connection - no authentication required",
                "skipped": True
            }
        
        # Test with correct credentials
        correct_result = await self._test_credentials(
            config, 
            config["username"], 
            config.get("password")
        )
        
        if not correct_result["success"]:
            return correct_result
        
        # Test with wrong password to verify auth is working
        wrong_result = await self._test_credentials(
            config,
            config["username"],
            "wrong_password_12345"
        )
        
        # If wrong credentials succeed, auth might not be properly configured
        if wrong_result["success"]:
            self.mqtt_logger.warning("⚠️ Wrong credentials succeeded - auth might not be enforced")
            return {
                "success": True,
                "message": "Authentication might not be enforced",
                "warning": "Wrong credentials were accepted",
                "recommendations": [
                    "Check MQTT broker authentication settings",
                    "Verify user permissions are properly configured"
                ]
            }
        
        self.mqtt_logger.info("✅ Authentication working correctly")
        return {
            "success": True,
            "message": "Authentication verified - correct credentials work, wrong ones rejected"
        }
    
    async def _test_credentials(self, config: Dict[str, Any], username: str, password: str) -> Dict[str, Any]:
        """Test specific credentials."""
        connection_result = {"connected": False, "rc": None}
        
        def on_connect(client, userdata, flags, rc):
            userdata["connected"] = rc == 0
            userdata["rc"] = rc
        
        try:
            client = mqtt.Client(
                client_id=f"auth_test_{int(time.time())}",
                callback_api_version=mqtt.CallbackAPIVersion.VERSION1
            )
            client.on_connect = on_connect
            client.user_data_set(connection_result)
            client.username_pw_set(username, password)
            
            await self.hass.async_add_executor_job(
                client.connect,
                config["host"],
                config.get("port", 1883),
                10
            )
            
            # Wait for result
            for _ in range(50):
                if connection_result["rc"] is not None:
                    break
                await asyncio.sleep(0.1)
            
            await self.hass.async_add_executor_job(client.disconnect)
            
            return {
                "success": connection_result["connected"],
                "return_code": connection_result["rc"]
            }
            
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc)
            }
        finally:
            try:
                await self.hass.async_add_executor_job(client.loop_stop)
            except Exception:
                pass
    
    async def _test_publish_subscribe(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test MQTT publish/subscribe functionality."""
        self.mqtt_logger.info("📤📥 Testing publish/subscribe functionality...")
        
        test_topic = f"awtrix_test/{int(time.time())}"
        test_message = f"Health check at {datetime.now().isoformat()}"
        received_messages = []
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                client.subscribe(test_topic)
                self.mqtt_logger.info(f"📥 Subscribed to {test_topic}")
        
        def on_message(client, userdata, msg):
            received_msg = msg.payload.decode('utf-8')
            received_messages.append(received_msg)
            self.mqtt_logger.info(f"📨 Received: {received_msg}")
        
        try:
            client = mqtt.Client(
                client_id=f"pubsub_test_{int(time.time())}",
                callback_api_version=mqtt.CallbackAPIVersion.VERSION1
            )
            client.on_connect = on_connect
            client.on_message = on_message
            
            if config.get("username"):
                client.username_pw_set(config["username"], config.get("password"))
            
            await self.hass.async_add_executor_job(
                client.connect,
                config["host"],
                config.get("port", 1883),
                10
            )
            
            # Start loop
            client.loop_start()
            
            # Wait a bit for subscription
            await asyncio.sleep(1)
            
            # Publish test message
            await self.hass.async_add_executor_job(
                client.publish,
                test_topic,
                test_message
            )
            self.mqtt_logger.info(f"📤 Published: {test_message}")
            
            # Wait for message
            await asyncio.sleep(2)
            
            client.loop_stop()
            await self.hass.async_add_executor_job(client.disconnect)
            
            if received_messages and test_message in received_messages:
                self.mqtt_logger.info("✅ Publish/Subscribe test successful")
                return {
                    "success": True,
                    "message": "Successfully published and received test message",
                    "details": {
                        "test_topic": test_topic,
                        "sent_message": test_message,
                        "received_messages": len(received_messages)
                    }
                }
            else:
                self.mqtt_logger.error("❌ Published message not received")
                return {
                    "success": False,
                    "error": "Published message was not received",
                    "recommendations": [
                        "Check MQTT broker message routing",
                        "Verify topic permissions",
                        "Check for message filtering"
                    ]
                }
                
        except Exception as exc:
            self.mqtt_logger.error(f"💥 Publish/Subscribe test failed: {exc}")
            return {
                "success": False,
                "error": str(exc),
                "recommendations": [
                    "Check MQTT broker publish/subscribe permissions",
                    "Verify client has necessary access rights"
                ]
            }
        finally:
            try:
                client.loop_stop()
                await self.hass.async_add_executor_job(client.disconnect)
            except Exception:
                pass
    
    async def _test_connection_stability(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test MQTT connection stability with multiple connections."""
        self.mqtt_logger.info("🔄 Testing connection stability...")
        
        successful_connections = 0
        total_attempts = 3
        connection_times = []
        
        for attempt in range(total_attempts):
            self.mqtt_logger.info(f"Attempt {attempt + 1}/{total_attempts}")
            
            start_time = time.time()
            connection_result = {"connected": False, "rc": None}
            
            def on_connect(client, userdata, flags, rc):
                userdata["connected"] = rc == 0
                userdata["rc"] = rc
            
            try:
                client = mqtt.Client(
                    client_id=f"stability_test_{attempt}_{int(time.time())}",
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION1
                )
                client.on_connect = on_connect
                client.user_data_set(connection_result)
                
                if config.get("username"):
                    client.username_pw_set(config["username"], config.get("password"))
                
                await self.hass.async_add_executor_job(
                    client.connect,
                    config["host"],
                    config.get("port", 1883),
                    10
                )
                
                # Wait for connection
                for _ in range(50):
                    if connection_result["rc"] is not None:
                        break
                    await asyncio.sleep(0.1)
                
                connection_time = time.time() - start_time
                connection_times.append(connection_time)
                
                if connection_result["connected"]:
                    successful_connections += 1
                    self.mqtt_logger.info(f"✅ Connection {attempt + 1} successful ({connection_time:.2f}s)")
                else:
                    self.mqtt_logger.error(f"❌ Connection {attempt + 1} failed")
                
                await self.hass.async_add_executor_job(client.disconnect)
                await asyncio.sleep(0.5)  # Brief pause between attempts
                
            except Exception as exc:
                self.mqtt_logger.error(f"❌ Connection {attempt + 1} exception: {exc}")
            finally:
                try:
                    await self.hass.async_add_executor_job(client.loop_stop)
                except Exception:
                    pass
        
        success_rate = successful_connections / total_attempts
        avg_connection_time = sum(connection_times) / len(connection_times) if connection_times else 0
        
        if success_rate >= 1.0:
            self.mqtt_logger.info(f"✅ Stability test passed: {successful_connections}/{total_attempts} connections successful")
            return {
                "success": True,
                "message": f"All {total_attempts} connection attempts successful",
                "details": {
                    "success_rate": success_rate,
                    "successful_connections": successful_connections,
                    "total_attempts": total_attempts,
                    "average_connection_time": avg_connection_time,
                    "connection_times": connection_times
                }
            }
        elif success_rate >= 0.7:
            self.mqtt_logger.warning(f"⚠️ Stability test partial: {successful_connections}/{total_attempts} connections successful")
            return {
                "success": True,
                "warning": f"Intermittent connection issues detected",
                "details": {
                    "success_rate": success_rate,
                    "successful_connections": successful_connections,
                    "total_attempts": total_attempts,
                    "average_connection_time": avg_connection_time
                },
                "recommendations": [
                    "Monitor MQTT broker performance",
                    "Check for network instability",
                    "Consider increasing connection timeouts"
                ]
            }
        else:
            self.mqtt_logger.error(f"❌ Stability test failed: {successful_connections}/{total_attempts} connections successful")
            return {
                "success": False,
                "error": f"Poor connection stability: {successful_connections}/{total_attempts} successful",
                "details": {
                    "success_rate": success_rate,
                    "successful_connections": successful_connections,
                    "total_attempts": total_attempts
                },
                "recommendations": [
                    "Check MQTT broker stability",
                    "Verify network connection quality",
                    "Check for resource constraints on broker"
                ]
            }
    
    def _get_error_recommendations(self, return_code: int) -> list:
        """Get specific recommendations based on MQTT return code."""
        recommendations = {
            1: [
                "Update MQTT broker to support newer protocol versions",
                "Check broker configuration for protocol version settings"
            ],
            2: [
                "Change the MQTT client ID to something unique",
                "Check if client ID length restrictions apply"
            ],
            3: [
                "Check if MQTT broker service is running",
                "Verify broker configuration and logs",
                "Check for resource constraints on broker server"
            ],
            4: [
                "Verify username and password are correct",
                "Check user account exists in MQTT broker",
                "Ensure password hasn't expired"
            ],
            5: [
                "Check user permissions in MQTT broker configuration",
                "Verify user account is enabled",
                "Check ACL (Access Control List) settings"
            ]
        }
        return recommendations.get(return_code, ["Check MQTT broker logs for specific error details"])
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> list:
        """Generate overall recommendations based on all test results."""
        recommendations = []
        
        for test_name, test_result in results["tests"].items():
            if not test_result.get("success", False):
                test_recommendations = test_result.get("recommendations", [])
                recommendations.extend(test_recommendations)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations
    
    async def _save_results(self, results: Dict[str, Any]) -> None:
        """Save health check results to storage."""
        try:
            await self.store.async_save(results)
            self.mqtt_logger.info("💾 Health check results saved to storage")
        except Exception as exc:
            self.mqtt_logger.error(f"❌ Failed to save results: {exc}")
    
    async def get_last_results(self) -> Optional[Dict[str, Any]]:
        """Get the last health check results."""
        try:
            return await self.store.async_load()
        except Exception:
            return None
    
    def get_log_file_path(self) -> str:
        """Get the path to the MQTT diagnostics log file."""
        return str(self.log_file_path)
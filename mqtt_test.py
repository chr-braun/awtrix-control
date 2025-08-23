#!/usr/bin/env python3
"""
Standalone MQTT Connection Test Tool for Awtrix MQTT Bridge
This script helps diagnose MQTT connectivity issues outside of Home Assistant.

Usage:
python3 mqtt_test.py [host] [port] [username] [password]

Examples:
python3 mqtt_test.py localhost 1883
python3 mqtt_test.py 192.168.1.100 1883 myuser mypass
python3 mqtt_test.py core-mosquitto 1883
"""

import sys
import socket
import time
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_network_connectivity(host, port):
    """Test basic network connectivity to MQTT broker."""
    logger.info(f"🌐 Testing network connectivity to {host}:{port}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            logger.info("✅ Network connectivity OK")
            return True
        else:
            logger.error(f"❌ Cannot reach {host}:{port} - Connection refused")
            return False
    except Exception as exc:
        logger.error(f"❌ Network error: {exc}")
        return False

def test_mqtt_protocol(host, port, username=None, password=None):
    """Test MQTT protocol connection."""
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        logger.error("❌ paho-mqtt library not installed. Install with: pip install paho-mqtt")
        return False
    
    logger.info(f"🔗 Testing MQTT protocol connection...")
    
    connection_result = {"connected": False, "rc": None}
    
    def on_connect(client, userdata, flags, rc):
        logger.info(f"📥 MQTT Connect callback: rc={rc}")
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
        logger.info(error_messages.get(rc, f"❌ Unknown error {rc}"))
    
    def on_disconnect(client, userdata, rc):
        logger.info(f"📤 MQTT Disconnect: rc={rc}")
    
    def on_log(client, userdata, level, buf):
        logger.debug(f"MQTT Log: {buf}")
    
    try:
        client = mqtt.Client(
            client_id="awtrix_test_tool",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1
        )
    except AttributeError:
        # Fallback for older paho-mqtt versions
        client = mqtt.Client(client_id="awtrix_test_tool")
    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_log = on_log
    client.user_data_set(connection_result)
    
    if username:
        logger.info(f"🔐 Setting credentials for user: {username}")
        client.username_pw_set(username, password)
    else:
        logger.info("🔓 Using anonymous connection")
    
    try:
        logger.info("🚀 Attempting MQTT connection...")
        client.connect(host, port, 15)
        
        # Wait for connection result
        timeout = 10
        for i in range(timeout * 10):
            if connection_result["rc"] is not None:
                break
            time.sleep(0.1)
            
            if i % 20 == 0 and i > 0:
                logger.info(f"⏳ Still waiting... ({i // 10} seconds)")
        
        if connection_result["rc"] is None:
            logger.error("⏰ Connection timeout - no response from broker")
            return False
        
        if connection_result["connected"]:
            logger.info("🎉 MQTT connection successful!")
            
            # Test publish
            try:
                client.publish("awtrix_test/diagnostic", "Hello from test tool!")
                logger.info("📤 Test message published successfully")
            except Exception as pub_exc:
                logger.error(f"❌ Publish test failed: {pub_exc}")
            
            client.disconnect()
            return True
        else:
            logger.error("❌ MQTT connection failed")
            return False
            
    except Exception as exc:
        logger.error(f"💥 MQTT connection exception: {exc}")
        return False

def print_common_solutions():
    """Print common MQTT troubleshooting solutions."""
    print("\n" + "="*60)
    print("🔧 COMMON MQTT TROUBLESHOOTING SOLUTIONS")
    print("="*60)
    print("""
1. 🏠 HOME ASSISTANT MOSQUITTO ADD-ON:
   - Host: core-mosquitto (not localhost)
   - Port: 1883
   - Check add-on is running in Supervisor

2. 🐳 EXTERNAL MOSQUITTO DOCKER:
   - Host: IP address of Docker host
   - Port: 1883 (check port mapping)
   - Check container is running: docker ps

3. 🖥️ STANDALONE MOSQUITTO:
   - Host: IP address of MQTT server
   - Port: 1883 (default)
   - Check service: systemctl status mosquitto

4. 🔒 AUTHENTICATION ISSUES:
   - Verify username/password in MQTT broker
   - Check user permissions
   - Try without credentials first

5. 🌐 NETWORK ISSUES:
   - Check firewall on port 1883
   - Verify IP address is correct
   - Test with ping/telnet first

6. 🚪 FIREWALL/PORT ISSUES:
   - Open port 1883 in firewall
   - Check router port forwarding
   - Verify no other service using port 1883
""")

def main():
    """Main test function."""
    print("🔍 AWTRIX MQTT BRIDGE - CONNECTIVITY TEST TOOL")
    print("=" * 50)
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python3 mqtt_test.py <host> [port] [username] [password]")
        print("\nExamples:")
        print("  python3 mqtt_test.py localhost")
        print("  python3 mqtt_test.py core-mosquitto 1883")
        print("  python3 mqtt_test.py 192.168.1.100 1883 myuser mypass")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 1883
    username = sys.argv[3] if len(sys.argv) > 3 else None
    password = sys.argv[4] if len(sys.argv) > 4 else None
    
    logger.info(f"Testing MQTT connection to {host}:{port}")
    if username:
        logger.info(f"Using credentials: {username}/{'*' * len(password or '')}")
    
    # Test network connectivity first
    if not test_network_connectivity(host, port):
        print("\n❌ Network connectivity test FAILED")
        print_common_solutions()
        sys.exit(1)
    
    # Test MQTT protocol
    if not test_mqtt_protocol(host, port, username, password):
        print("\n❌ MQTT protocol test FAILED")
        print_common_solutions()
        sys.exit(1)
    
    print("\n✅ ALL TESTS PASSED!")
    print("Your MQTT broker is working correctly.")
    print("You can now use these settings in the Awtrix MQTT Bridge integration.")

if __name__ == "__main__":
    main()
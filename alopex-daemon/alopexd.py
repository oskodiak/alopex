#!/usr/bin/env python3
"""
ALOPEX Network Management Daemon
Enterprise-grade networking that makes NetworkManager obsolete
Onyx Digital Intelligence Development LLC
"""

import sys
import os
import signal
import asyncio
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import asdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "alopex-qt"))

from network.discovery import NetworkDiscovery, NetworkInterface
from network.system_integration import NetworkControl
from network.wifi import WiFiManager  
from network.vpn import VpnManager
from network.connection_manager import ConnectionManager

class AlopexDaemon:
    """Enterprise network management daemon"""
    
    def __init__(self):
        self.discovery = NetworkDiscovery()
        self.connection_manager = ConnectionManager()
        self.running = False
        self.config_path = Path("/etc/alopex")
        self.state_path = Path("/var/lib/alopex")
        
        # Enterprise configuration
        self.enterprise_config = self._load_enterprise_config()
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Configure enterprise-grade logging"""
        log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        
        # Console logging
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        
        # File logging
        log_file = Path("/var/log/alopex/alopexd.log")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            handlers=[console_handler, file_handler]
        )
        
        self.logger = logging.getLogger("alopexd")
        
    def _load_enterprise_config(self) -> dict:
        """Load enterprise configuration"""
        config_file = self.config_path / "enterprise.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load enterprise config: {e}")
        
        # Default enterprise configuration
        return {
            "auto_connect": True,
            "preferred_networks": [],
            "enterprise_policies": {
                "require_encryption": True,
                "allow_adhoc": False,
                "vpn_required": []
            },
            "monitoring": {
                "telemetry_enabled": True,
                "syslog_integration": True,
                "metrics_port": 9090
            }
        }
    
    def _load_saved_connections(self) -> Dict[str, dict]:
        """Load saved network connections"""
        connections_file = self.state_path / "connections.json"
        if connections_file.exists():
            try:
                with open(connections_file) as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load saved connections: {e}")
        return {}
    
    def _save_connections(self):
        """Save network connections to persistent storage"""
        connections_file = self.state_path / "connections.json"
        connections_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(connections_file, 'w') as f:
                json.dump(self.saved_connections, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save connections: {e}")
    
    async def auto_connect_networks(self):
        """Auto-connect to saved networks with enterprise priority"""
        if not self.enterprise_config.get("auto_connect", True):
            return
        
        # Use the new connection manager for auto-connection
        await self.connection_manager.auto_connect_all()
    
    async def _auto_connect_wifi(self, interface: str):
        """Auto-connect WiFi based on enterprise preferences"""
        try:
            # Scan for available networks
            networks = await self.wifi.scan_networks(interface)
            
            # Priority order: enterprise preferred -> saved connections -> open networks
            preferred = self.enterprise_config.get("preferred_networks", [])
            
            for network_ssid in preferred:
                for network in networks:
                    if network.ssid == network_ssid and network_ssid in self.saved_connections:
                        connection = self.saved_connections[network_ssid]
                        success = await self.wifi.connect_to_network(
                            interface, network_ssid, connection.get("password")
                        )
                        if success:
                            self.logger.info(f"Auto-connected to preferred network: {network_ssid}")
                            return
            
            # Try saved connections
            for network in networks:
                if network.ssid in self.saved_connections:
                    connection = self.saved_connections[network.ssid]
                    success = await self.wifi.connect_to_network(
                        interface, network.ssid, connection.get("password")
                    )
                    if success:
                        self.logger.info(f"Auto-connected to saved network: {network.ssid}")
                        return
                        
        except Exception as e:
            self.logger.error(f"WiFi auto-connect failed: {e}")
    
    async def _auto_connect_ethernet(self, interface: str):
        """Auto-configure Ethernet interface"""
        try:
            # Check for saved static configuration
            if interface in self.saved_connections:
                connection = self.saved_connections[interface]
                if connection.get("method") == "static":
                    success = await NetworkControl.configure_static_ip(
                        interface,
                        connection.get("ip"),
                        connection.get("gateway"),
                        connection.get("dns", [])
                    )
                    if success:
                        self.logger.info(f"Configured static IP for {interface}")
                        return
            
            # Default to DHCP
            success = await NetworkControl.configure_dhcp(interface)
            if success:
                self.logger.info(f"Configured DHCP for {interface}")
                
        except Exception as e:
            self.logger.error(f"Ethernet auto-connect failed: {e}")
    
    async def monitor_network_changes(self):
        """Monitor for network interface changes"""
        previous_interfaces = {}
        
        while self.running:
            try:
                current_interfaces = {
                    iface.name: iface for iface in self.discovery.discover_interfaces()
                }
                
                # Detect new interfaces
                for name, interface in current_interfaces.items():
                    if name not in previous_interfaces:
                        self.logger.info(f"New interface detected: {name} ({interface.interface_type})")
                        # Attempt auto-connection for new interfaces
                        if interface.interface_type in ["WiFi", "Ethernet"]:
                            await self.auto_connect_networks()
                    
                    # Detect status changes
                    elif previous_interfaces[name].status != interface.status:
                        self.logger.info(f"Interface {name} status: {previous_interfaces[name].status} -> {interface.status}")
                        
                        # Reconnect if disconnected unexpectedly
                        if interface.status == "Disconnected" and previous_interfaces[name].status == "Connected":
                            self.logger.warning(f"Interface {name} disconnected, attempting reconnection")
                            await self.auto_connect_networks()
                
                previous_interfaces = current_interfaces
                await asyncio.sleep(5)  # Monitor every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Network monitoring error: {e}")
                await asyncio.sleep(10)  # Back off on errors
    
    async def export_telemetry(self):
        """Export network telemetry for enterprise monitoring"""
        if not self.enterprise_config.get("monitoring", {}).get("telemetry_enabled", True):
            return
            
        while self.running:
            try:
                interfaces = self.discovery.discover_interfaces()
                telemetry_data = {
                    "timestamp": time.time(),
                    "interfaces": [asdict(iface) for iface in interfaces],
                    "daemon_status": "running",
                    "connections_count": len(self.saved_connections)
                }
                
                # Write to telemetry file for collection
                telemetry_file = Path("/var/lib/alopex/telemetry.json")
                with open(telemetry_file, 'w') as f:
                    json.dump(telemetry_data, f)
                
                await asyncio.sleep(30)  # Export every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Telemetry export failed: {e}")
                await asyncio.sleep(60)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def run(self):
        """Main daemon execution loop"""
        self.logger.info("Starting ALOPEX Network Management Daemon")
        self.logger.info("Enterprise-grade networking initialized")
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        self.running = True
        
        # Initial network auto-connection
        await self.auto_connect_networks()
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self.monitor_network_changes()),
            asyncio.create_task(self.export_telemetry()),
            asyncio.create_task(self.connection_manager.monitor_connections()),
        ]
        
        # Main event loop
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        finally:
            # Cleanup
            self.logger.info("Shutting down ALOPEX daemon")
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Save state
            self._save_connections()

def main():
    """Main entry point"""
    # Ensure we're running as root for network management
    if os.getuid() != 0:
        print("ALOPEX daemon must be run as root", file=sys.stderr)
        sys.exit(1)
    
    # Create daemon and run
    daemon = AlopexDaemon()
    asyncio.run(daemon.run())

if __name__ == "__main__":
    main()
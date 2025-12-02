#!/usr/bin/env python3
"""
ALOPEX Early Network Configuration
Critical system service for early boot network setup
Onyx Digital Intelligence Development LLC
"""

import sys
import os
import subprocess
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

class EarlyNetworkConfig:
    """Early boot network configuration for enterprise environments"""
    
    def __init__(self):
        self.config_path = Path("/etc/alopex")
        self.state_path = Path("/var/lib/alopex")
        
        # Setup minimal logging for early boot
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] alopex-early: %(message)s"
        )
        self.logger = logging.getLogger("alopex-early")
    
    def load_critical_networks(self) -> List[Dict]:
        """Load critical networks that must be available at boot"""
        critical_file = self.config_path / "critical-networks.json"
        if not critical_file.exists():
            return []
        
        try:
            with open(critical_file) as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load critical networks: {e}")
            return []
    
    def discover_interfaces(self) -> List[str]:
        """Discover available network interfaces"""
        try:
            net_path = Path("/sys/class/net")
            interfaces = []
            
            for iface_path in net_path.iterdir():
                if iface_path.is_dir():
                    name = iface_path.name
                    # Skip loopback and virtual interfaces in early boot
                    if not name.startswith(('lo', 'docker', 'br-', 'veth')):
                        interfaces.append(name)
            
            return interfaces
        except Exception as e:
            self.logger.error(f"Interface discovery failed: {e}")
            return []
    
    def bring_interface_up(self, interface: str) -> bool:
        """Bring network interface up"""
        try:
            result = subprocess.run(
                ['ip', 'link', 'set', interface, 'up'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                self.logger.info(f"Brought interface {interface} up")
                return True
            else:
                self.logger.error(f"Failed to bring {interface} up: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Exception bringing {interface} up: {e}")
            return False
    
    def configure_dhcp(self, interface: str) -> bool:
        """Configure DHCP for interface"""
        try:
            # Try dhcpcd first (more reliable in early boot)
            result = subprocess.run(
                ['dhcpcd', '-b', interface],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                self.logger.info(f"DHCP configured for {interface}")
                return True
            
            # Fallback to dhclient
            result = subprocess.run(
                ['dhclient', interface],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                self.logger.info(f"DHCP configured for {interface} (dhclient)")
                return True
            
            self.logger.error(f"DHCP configuration failed for {interface}")
            return False
            
        except subprocess.TimeoutExpired:
            self.logger.warning(f"DHCP timeout for {interface}")
            return False
        except Exception as e:
            self.logger.error(f"DHCP configuration error for {interface}: {e}")
            return False
    
    def configure_static_ip(self, interface: str, config: Dict) -> bool:
        """Configure static IP for interface"""
        try:
            ip_addr = config.get("ip")
            gateway = config.get("gateway")
            dns = config.get("dns", [])
            
            if not ip_addr:
                return False
            
            # Set IP address
            result = subprocess.run(
                ['ip', 'addr', 'add', f"{ip_addr}/24", 'dev', interface],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                self.logger.error(f"Failed to set IP {ip_addr} on {interface}")
                return False
            
            # Set gateway
            if gateway:
                subprocess.run(
                    ['ip', 'route', 'add', 'default', 'via', gateway],
                    capture_output=True, text=True
                )
            
            # Set DNS
            if dns:
                resolv_conf = "/etc/resolv.conf"
                with open(resolv_conf, 'w') as f:
                    for dns_server in dns:
                        f.write(f"nameserver {dns_server}\n")
            
            self.logger.info(f"Static IP configured for {interface}: {ip_addr}")
            return True
            
        except Exception as e:
            self.logger.error(f"Static IP configuration failed for {interface}: {e}")
            return False
    
    def test_connectivity(self, interface: str) -> bool:
        """Test network connectivity"""
        try:
            # Test local connectivity first
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '5', '-I', interface, '8.8.8.8'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                self.logger.info(f"Connectivity verified for {interface}")
                return True
            else:
                self.logger.warning(f"No connectivity on {interface}")
                return False
        except Exception as e:
            self.logger.error(f"Connectivity test failed for {interface}: {e}")
            return False
    
    def configure_critical_networks(self):
        """Configure critical networks for early boot"""
        critical_networks = self.load_critical_networks()
        
        if not critical_networks:
            self.logger.info("No critical networks configured")
            return
        
        interfaces = self.discover_interfaces()
        self.logger.info(f"Discovered interfaces: {', '.join(interfaces)}")
        
        configured_count = 0
        
        for interface in interfaces:
            # Bring interface up first
            if not self.bring_interface_up(interface):
                continue
            
            # Check for interface-specific configuration
            interface_config = None
            for config in critical_networks:
                if config.get("interface") == interface:
                    interface_config = config
                    break
            
            if interface_config:
                # Configure based on specified method
                method = interface_config.get("method", "dhcp")
                
                if method == "static":
                    success = self.configure_static_ip(interface, interface_config)
                else:
                    success = self.configure_dhcp(interface)
                
                if success:
                    configured_count += 1
                    # Test connectivity
                    self.test_connectivity(interface)
            else:
                # Default to DHCP for ethernet interfaces
                if interface.startswith(('eth', 'eno', 'enp', 'ens')):
                    if self.configure_dhcp(interface):
                        configured_count += 1
                        self.test_connectivity(interface)
        
        self.logger.info(f"Early network configuration complete: {configured_count} interfaces configured")
        
        # Create state file to indicate early network is ready
        state_file = self.state_path / "early-network-ready"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(f"Early network configured at boot\nInterfaces: {configured_count}\n")

def main():
    """Main entry point for early network configuration"""
    if os.getuid() != 0:
        print("ALOPEX early network configuration must be run as root", file=sys.stderr)
        sys.exit(1)
    
    early_config = EarlyNetworkConfig()
    early_config.configure_critical_networks()

if __name__ == "__main__":
    main()
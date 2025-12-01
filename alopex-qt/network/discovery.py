"""
Network Interface Discovery and Monitoring
Port of our Rust network logic to Python
"""

import os
import subprocess
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class NetworkMetrics:
    """Comprehensive network metrics"""
    bytes_tx: int = 0
    bytes_rx: int = 0
    packets_tx: int = 0
    packets_rx: int = 0
    errors_tx: int = 0
    errors_rx: int = 0
    dropped_tx: int = 0
    dropped_rx: int = 0
    speed_up: float = 0.0      # KB/s
    speed_down: float = 0.0    # KB/s
    packets_per_sec_tx: float = 0.0
    packets_per_sec_rx: float = 0.0
    link_speed: Optional[int] = None  # Mbps
    duplex: Optional[str] = None
    mtu: Optional[int] = None
    uptime: Optional[float] = None

@dataclass 
class NetworkInterface:
    """Network interface representation"""
    name: str
    interface_type: str
    status: str
    ip: Optional[str] = None
    gateway: Optional[str] = None
    dns: List[str] = None
    metrics: NetworkMetrics = None
    
    def __post_init__(self):
        if self.dns is None:
            self.dns = []
        if self.metrics is None:
            self.metrics = NetworkMetrics()

class NetworkDiscovery:
    """Network interface discovery and monitoring"""
    
    def __init__(self):
        self.previous_metrics: Dict[str, NetworkMetrics] = {}
        self.last_update = time.time()
    
    @staticmethod
    def discover_interfaces() -> List[NetworkInterface]:
        """Discover all network interfaces"""
        interfaces = []
        net_path = Path("/sys/class/net")
        
        if not net_path.exists():
            return interfaces
            
        for interface_dir in net_path.iterdir():
            if interface_dir.is_dir() and interface_dir.name != "lo":
                interface = NetworkDiscovery._get_interface_info(interface_dir.name)
                if interface:
                    interfaces.append(interface)
        
        # Sort by type and name for consistent ordering
        interfaces.sort(key=lambda x: (NetworkDiscovery._type_priority(x.interface_type), x.name))
        return interfaces
    
    @staticmethod
    def _type_priority(interface_type: str) -> int:
        """Get sorting priority for interface type"""
        priorities = {"Ethernet": 0, "WiFi": 1, "VPN": 2}
        return priorities.get(interface_type, 3)
    
    @staticmethod
    def _get_interface_info(name: str) -> Optional[NetworkInterface]:
        """Get detailed information for a network interface"""
        try:
            interface_type = NetworkDiscovery._detect_interface_type(name)
            status = NetworkDiscovery._get_interface_status(name)
            ip = NetworkDiscovery._get_interface_ip(name)
            gateway = NetworkDiscovery._get_default_gateway()
            dns = NetworkDiscovery._get_dns_servers()
            metrics = NetworkDiscovery._get_interface_metrics(name)
            
            return NetworkInterface(
                name=name,
                interface_type=interface_type,
                status=status,
                ip=ip,
                gateway=gateway,
                dns=dns,
                metrics=metrics
            )
        except Exception as e:
            print(f"Error getting info for {name}: {e}")
            return None
    
    @staticmethod
    def _detect_interface_type(name: str) -> str:
        """Detect interface type from name and sysfs"""
        if name.startswith(("eth", "en")):
            return "Ethernet"
        elif name.startswith(("wlan", "wl")):
            return "WiFi"
        elif name.startswith(("tun", "wg")):
            return "VPN"
        else:
            return "Unknown"
    
    @staticmethod
    def _get_interface_status(name: str) -> str:
        """Get interface operational status"""
        try:
            operstate_path = f"/sys/class/net/{name}/operstate"
            with open(operstate_path) as f:
                state = f.read().strip()
                status_map = {
                    "up": "Connected",
                    "down": "Disconnected", 
                    "dormant": "Connecting"
                }
                return status_map.get(state, "Unknown")
        except:
            return "Unknown"
    
    @staticmethod
    def _get_interface_ip(name: str) -> Optional[str]:
        """Get interface IP address"""
        try:
            result = subprocess.run(
                ["ip", "addr", "show", name], 
                capture_output=True, text=True, check=True
            )
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.startswith("inet ") and "127.0.0.1" not in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        ip_cidr = parts[1]
                        return ip_cidr.split('/')[0]
            return None
        except:
            return None
    
    @staticmethod
    def _get_default_gateway() -> Optional[str]:
        """Get default gateway"""
        try:
            result = subprocess.run(
                ["ip", "route", "show", "default"],
                capture_output=True, text=True, check=True
            )
            
            for line in result.stdout.split('\n'):
                if "default via" in line:
                    parts = line.split()
                    via_index = parts.index("via")
                    if via_index + 1 < len(parts):
                        return parts[via_index + 1]
            return None
        except:
            return None
    
    @staticmethod
    def _get_dns_servers() -> List[str]:
        """Get DNS servers from resolv.conf"""
        try:
            with open("/etc/resolv.conf") as f:
                dns_servers = []
                for line in f:
                    line = line.strip()
                    if line.startswith("nameserver "):
                        parts = line.split()
                        if len(parts) >= 2:
                            dns_servers.append(parts[1])
                return dns_servers
        except:
            return ["8.8.8.8"]  # Fallback
    
    @staticmethod
    def _get_interface_metrics(name: str) -> NetworkMetrics:
        """Get comprehensive interface metrics from /proc/net/dev"""
        try:
            with open("/proc/net/dev") as f:
                for line in f:
                    if f"{name}:" in line:
                        parts = line.split()
                        if len(parts) >= 17:
                            # Parse all fields from /proc/net/dev
                            bytes_rx = int(parts[1])
                            packets_rx = int(parts[2])
                            errors_rx = int(parts[3])
                            dropped_rx = int(parts[4])
                            
                            bytes_tx = int(parts[9])
                            packets_tx = int(parts[10])
                            errors_tx = int(parts[11])
                            dropped_tx = int(parts[12])
                            
                            # Get interface capabilities
                            link_speed = NetworkDiscovery._get_link_speed(name)
                            duplex = NetworkDiscovery._get_duplex(name)
                            mtu = NetworkDiscovery._get_mtu(name)
                            
                            return NetworkMetrics(
                                bytes_tx=bytes_tx,
                                bytes_rx=bytes_rx,
                                packets_tx=packets_tx,
                                packets_rx=packets_rx,
                                errors_tx=errors_tx,
                                errors_rx=errors_rx,
                                dropped_tx=dropped_tx,
                                dropped_rx=dropped_rx,
                                link_speed=link_speed,
                                duplex=duplex,
                                mtu=mtu
                            )
        except Exception as e:
            print(f"Error getting metrics for {name}: {e}")
        
        return NetworkMetrics()
    
    @staticmethod
    def _get_link_speed(name: str) -> Optional[int]:
        """Get link speed from sysfs"""
        try:
            with open(f"/sys/class/net/{name}/speed") as f:
                return int(f.read().strip())
        except:
            return None
    
    @staticmethod
    def _get_duplex(name: str) -> Optional[str]:
        """Get duplex mode from sysfs"""
        try:
            with open(f"/sys/class/net/{name}/duplex") as f:
                duplex = f.read().strip()
                return duplex if duplex != "unknown" else None
        except:
            return None
    
    @staticmethod
    def _get_mtu(name: str) -> Optional[int]:
        """Get MTU from sysfs"""
        try:
            with open(f"/sys/class/net/{name}/mtu") as f:
                return int(f.read().strip())
        except:
            return None
    
    def update_speeds(self, interfaces: List[NetworkInterface]) -> None:
        """Calculate real-time speed metrics"""
        now = time.time()
        time_diff = now - self.last_update
        
        if time_diff < 0.1:  # Too frequent
            return
            
        for interface in interfaces:
            name = interface.name
            current = interface.metrics
            
            if name in self.previous_metrics:
                prev = self.previous_metrics[name]
                
                # Calculate differences
                bytes_tx_diff = current.bytes_tx - prev.bytes_tx
                bytes_rx_diff = current.bytes_rx - prev.bytes_rx
                packets_tx_diff = current.packets_tx - prev.packets_tx
                packets_rx_diff = current.packets_rx - prev.packets_rx
                
                # Calculate speeds (KB/s and packets/s)
                current.speed_up = bytes_tx_diff / time_diff / 1024.0
                current.speed_down = bytes_rx_diff / time_diff / 1024.0
                current.packets_per_sec_tx = packets_tx_diff / time_diff
                current.packets_per_sec_rx = packets_rx_diff / time_diff
            
            # Store for next calculation
            self.previous_metrics[name] = NetworkMetrics(
                bytes_tx=current.bytes_tx,
                bytes_rx=current.bytes_rx,
                packets_tx=current.packets_tx,
                packets_rx=current.packets_rx,
                errors_tx=current.errors_tx,
                errors_rx=current.errors_rx,
                dropped_tx=current.dropped_tx,
                dropped_rx=current.dropped_rx
            )
        
        self.last_update = now
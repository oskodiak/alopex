"""
VPN Management - Enterprise WireGuard and OpenVPN Integration
Ported from Aurora WG for seamless VPN control
Onyx Digital Intelligence Development
"""

import subprocess
import asyncio
import logging
import re
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass, field
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

class VpnStatus(Enum):
    """VPN connection status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"
    UNKNOWN = "unknown"

@dataclass
class VpnConfig:
    """Enterprise VPN configuration profile"""
    name: str
    path: Path
    config_type: str = "wireguard"  # wireguard, openvpn
    location: Optional[str] = None
    last_used: Optional[str] = None
    status: VpnStatus = VpnStatus.DISCONNECTED
    interface_name: Optional[str] = None
    endpoint: Optional[str] = None
    public_key: Optional[str] = None
    allowed_ips: Optional[str] = None
    connection_metrics: Dict = field(default_factory=dict)

class VpnManager:
    """WireGuard and OpenVPN management"""
    
    @staticmethod
    def discover_configs() -> List[VpnConfig]:
        """Discover WireGuard configurations"""
        configs = []
        
        # Common WireGuard config locations
        search_paths = [
            Path.home() / ".config" / "wireguard",
            Path("/etc/wireguard"),
            Path.home() / "wireguard",
        ]
        
        for search_path in search_paths:
            if search_path.exists():
                for config_file in search_path.glob("*.conf"):
                    config = VpnManager._parse_wireguard_config(config_file)
                    if config:
                        configs.append(config)
        
        return sorted(configs, key=lambda x: x.name)
    
    @staticmethod
    def _parse_wireguard_config(config_path: Path) -> Optional[VpnConfig]:
        """Parse WireGuard config file"""
        try:
            name = config_path.stem
            location = VpnManager._extract_location_from_config(config_path)
            
            return VpnConfig(
                name=name,
                path=config_path,
                config_type="wireguard",
                location=location
            )
        except Exception as e:
            print(f"Error parsing WireGuard config {config_path}: {e}")
            return None
    
    @staticmethod
    def _extract_location_from_config(config_path: Path) -> Optional[str]:
        """Extract location/server info from config"""
        try:
            with open(config_path) as f:
                content = f.read()
                
            # Look for common location indicators
            for line in content.split('\n'):
                line = line.strip().lower()
                if 'endpoint' in line and '=' in line:
                    endpoint = line.split('=')[1].strip()
                    # Extract country/location from hostname if possible
                    if any(country in endpoint for country in ['us', 'uk', 'de', 'jp', 'ca']):
                        parts = endpoint.split('.')
                        for part in parts:
                            if any(country in part for country in ['us', 'uk', 'de', 'jp', 'ca']):
                                return part.upper()
                                
            return "Unknown"
        except:
            return "Unknown"
    
    @staticmethod
    async def connect_wireguard(config_path: Path) -> tuple[bool, str]:
        """Connect WireGuard VPN with enterprise monitoring"""
        try:
            interface_name = config_path.stem
            logger.info(f"Connecting WireGuard: {interface_name}")
            
            # Check if already connected
            if VpnManager.is_wireguard_active(interface_name):
                logger.warning(f"WireGuard interface {interface_name} already active")
                return True, f"Interface {interface_name} already connected"
            
            # Use wg-quick to bring up the interface
            process = await asyncio.create_subprocess_exec(
                'sudo', 'wg-quick', 'up', str(config_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"WireGuard connected: {interface_name}")
                
                # Verify connection and get status
                await asyncio.sleep(2)  # Allow time for interface to come up
                if VpnManager.is_wireguard_active(interface_name):
                    status = VpnManager.get_wireguard_status(interface_name)
                    logger.debug(f"WireGuard status: {status}")
                    return True, f"Connected to {interface_name}"
                else:
                    logger.error(f"WireGuard interface {interface_name} failed to come up")
                    return False, "Interface failed to activate"
            else:
                error_msg = stderr.decode().strip()
                logger.error(f"WireGuard connection failed: {error_msg}")
                return False, f"Connection failed: {error_msg}"
                
        except Exception as e:
            logger.exception(f"Error connecting WireGuard: {e}")
            return False, f"Exception: {str(e)}"
    
    @staticmethod
    async def disconnect_wireguard(interface_name: str) -> bool:
        """Disconnect WireGuard VPN"""
        try:
            result = await asyncio.create_subprocess_exec(
                'sudo', 'wg-quick', 'down', interface_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                print(f"WireGuard disconnected: {interface_name}")
                return True
            else:
                print(f"WireGuard disconnect failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"Error disconnecting WireGuard: {e}")
            return False
    
    @staticmethod
    def is_wireguard_active(interface_name: str = None) -> bool:
        """Check if WireGuard is currently active"""
        try:
            result = subprocess.run(['wg', 'show'], capture_output=True, text=True)
            if result.returncode == 0:
                if interface_name:
                    return interface_name in result.stdout
                else:
                    return len(result.stdout.strip()) > 0
            return False
        except:
            return False
    
    @staticmethod
    def get_wireguard_status(interface_name: str = None) -> dict:
        """Get detailed WireGuard status"""
        try:
            cmd = ['wg', 'show']
            if interface_name:
                cmd.append(interface_name)
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return VpnManager._parse_wg_status(result.stdout)
            return {}
        except:
            return {}
    
    @staticmethod
    def _parse_wg_status(output: str) -> dict:
        """Parse wg show output"""
        status = {}
        current_interface = None
        
        for line in output.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('interface:'):
                current_interface = line.split(':')[1].strip()
                status[current_interface] = {
                    'peers': [],
                    'public_key': None,
                    'listening_port': None
                }
            elif current_interface and ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if key == 'public key':
                    status[current_interface]['public_key'] = value
                elif key == 'listening port':
                    status[current_interface]['listening_port'] = value
                elif key == 'peer':
                    status[current_interface]['peers'].append({
                        'public_key': value,
                        'endpoint': None,
                        'allowed_ips': None,
                        'latest_handshake': None,
                        'transfer': None
                    })
                elif key in ['endpoint', 'allowed ips', 'latest handshake', 'transfer']:
                    if status[current_interface]['peers']:
                        peer = status[current_interface]['peers'][-1]
                        peer[key.replace(' ', '_')] = value
        
        return status
    
    @staticmethod
    def get_connection_health(interface_name: str) -> Dict:
        """Get comprehensive VPN connection health metrics"""
        health = {
            'status': VpnStatus.DISCONNECTED,
            'latency': None,
            'bandwidth_up': 0,
            'bandwidth_down': 0,
            'handshake_age': None,
            'endpoint_reachable': False,
            'dns_working': False
        }
        
        try:
            # Check if interface is active
            if not VpnManager.is_wireguard_active(interface_name):
                return health
                
            health['status'] = VpnStatus.CONNECTED
            
            # Get WireGuard status for handshake info
            wg_status = VpnManager.get_wireguard_status(interface_name)
            if interface_name in wg_status and wg_status[interface_name]['peers']:
                peer = wg_status[interface_name]['peers'][0]
                
                # Parse handshake time
                if peer.get('latest_handshake'):
                    handshake_str = peer['latest_handshake']
                    if 'ago' in handshake_str:
                        health['handshake_age'] = handshake_str
                
                # Parse transfer data
                if peer.get('transfer'):
                    transfer_str = peer['transfer']
                    # Extract received/sent bytes (simplified parsing)
                    if 'received' in transfer_str and 'sent' in transfer_str:
                        health['bandwidth_down'] = "Available"
                        health['bandwidth_up'] = "Available"
                
                # Test endpoint reachability
                endpoint = peer.get('endpoint')
                if endpoint:
                    try:
                        ping_result = subprocess.run([
                            'ping', '-c', '1', '-W', '2', endpoint.split(':')[0]
                        ], capture_output=True, timeout=5)
                        health['endpoint_reachable'] = ping_result.returncode == 0
                        
                        if health['endpoint_reachable']:
                            # Extract latency from ping
                            ping_output = ping_result.stdout.decode()
                            latency_match = re.search(r'time=([\d.]+)', ping_output)
                            if latency_match:
                                health['latency'] = f"{latency_match.group(1)}ms"
                    except:
                        pass
            
            # Test DNS resolution through VPN
            try:
                dns_result = subprocess.run([
                    'nslookup', 'google.com', '8.8.8.8'
                ], capture_output=True, timeout=5)
                health['dns_working'] = dns_result.returncode == 0
            except:
                pass
                
        except Exception as e:
            logger.exception(f"Error getting VPN health for {interface_name}: {e}")
            health['status'] = VpnStatus.UNKNOWN
            
        return health
    
    @staticmethod  
    def get_all_active_connections() -> List[Dict]:
        """Get status of all active VPN connections"""
        connections = []
        
        try:
            wg_status = VpnManager.get_wireguard_status()
            for interface_name in wg_status.keys():
                health = VpnManager.get_connection_health(interface_name)
                connections.append({
                    'interface': interface_name,
                    'type': 'wireguard',
                    'health': health,
                    'details': wg_status[interface_name]
                })
        except Exception as e:
            logger.exception(f"Error getting active connections: {e}")
            
        return connections
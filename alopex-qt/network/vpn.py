"""
VPN Management - WireGuard Integration
Ported from Aurora WG for seamless VPN control
"""

import subprocess
import asyncio
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class VpnConfig:
    """VPN configuration profile"""
    name: str
    path: Path
    config_type: str = "wireguard"  # wireguard, openvpn
    location: Optional[str] = None
    last_used: Optional[str] = None

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
    async def connect_wireguard(config_path: Path) -> bool:
        """Connect WireGuard VPN"""
        try:
            # Use wg-quick to bring up the interface
            result = await asyncio.create_subprocess_exec(
                'sudo', 'wg-quick', 'up', str(config_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                print(f"WireGuard connected: {config_path.name}")
                return True
            else:
                print(f"WireGuard connection failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"Error connecting WireGuard: {e}")
            return False
    
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
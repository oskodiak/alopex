"""
Connection State Management - Persistent network configuration
Enterprise-grade connection handling that NetworkManager wishes it had
"""

import json
import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

from .discovery import NetworkInterface, NetworkDiscovery
from .system_integration import NetworkControl
from .wifi import WiFiManager

@dataclass
class ConnectionProfile:
    """Persistent connection configuration"""
    name: str
    interface: str
    connection_type: str  # ethernet, wifi, vpn
    method: str  # dhcp, static, manual
    
    # Static IP configuration
    ip_address: Optional[str] = None
    netmask: Optional[str] = None
    gateway: Optional[str] = None
    dns_servers: List[str] = None
    
    # WiFi configuration
    ssid: Optional[str] = None
    password: Optional[str] = None
    security: Optional[str] = None
    
    # Connection metadata
    auto_connect: bool = True
    priority: int = 0
    last_connected: Optional[float] = None
    connection_attempts: int = 0
    last_error: Optional[str] = None
    
    def __post_init__(self):
        if self.dns_servers is None:
            self.dns_servers = []

@dataclass 
class ConnectionState:
    """Current interface connection state"""
    interface: str
    profile_name: Optional[str] = None
    status: str = "disconnected"  # disconnected, connecting, connected, failed
    ip_address: Optional[str] = None
    gateway: Optional[str] = None
    dns_servers: List[str] = None
    connected_at: Optional[float] = None
    last_seen: Optional[float] = None
    error_count: int = 0
    
    def __post_init__(self):
        if self.dns_servers is None:
            self.dns_servers = []

class ConnectionManager:
    """Enterprise connection state management"""
    
    def __init__(self):
        self.config_path = Path("/var/lib/alopex")
        self.profiles_file = self.config_path / "connection-profiles.json"
        self.state_file = self.config_path / "connection-state.json"
        
        self.discovery = NetworkDiscovery()
        self.wifi = WiFiManager()
        
        # In-memory state
        self.profiles: Dict[str, ConnectionProfile] = {}
        self.interface_states: Dict[str, ConnectionState] = {}
        
        # Monitoring
        self.monitoring = True
        self.reconnect_interval = 30  # seconds
        
        # Setup logging
        self.logger = logging.getLogger("connection_manager")
        
        # Load existing configuration
        self._load_profiles()
        self._load_states()
    
    def _load_profiles(self):
        """Load connection profiles from persistent storage"""
        if self.profiles_file.exists():
            try:
                with open(self.profiles_file) as f:
                    data = json.load(f)
                    
                for name, profile_data in data.items():
                    self.profiles[name] = ConnectionProfile(**profile_data)
                    
                self.logger.info(f"Loaded {len(self.profiles)} connection profiles")
            except Exception as e:
                self.logger.error(f"Failed to load profiles: {e}")
    
    def _save_profiles(self):
        """Save connection profiles to persistent storage"""
        self.config_path.mkdir(parents=True, exist_ok=True)
        
        try:
            data = {name: asdict(profile) for name, profile in self.profiles.items()}
            with open(self.profiles_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save profiles: {e}")
    
    def _load_states(self):
        """Load connection states"""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    data = json.load(f)
                    
                for interface, state_data in data.items():
                    self.interface_states[interface] = ConnectionState(**state_data)
                    
            except Exception as e:
                self.logger.error(f"Failed to load states: {e}")
    
    def _save_states(self):
        """Save connection states"""
        self.config_path.mkdir(parents=True, exist_ok=True)
        
        try:
            data = {iface: asdict(state) for iface, state in self.interface_states.items()}
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save states: {e}")
    
    def create_profile(self, name: str, interface: str, connection_type: str, 
                      method: str = "dhcp", **kwargs) -> ConnectionProfile:
        """Create a new connection profile"""
        profile = ConnectionProfile(
            name=name,
            interface=interface,
            connection_type=connection_type,
            method=method,
            **kwargs
        )
        
        self.profiles[name] = profile
        self._save_profiles()
        
        self.logger.info(f"Created connection profile: {name}")
        return profile
    
    def get_profile(self, name: str) -> Optional[ConnectionProfile]:
        """Get connection profile by name"""
        return self.profiles.get(name)
    
    def list_profiles(self, interface: str = None) -> List[ConnectionProfile]:
        """List all connection profiles, optionally filtered by interface"""
        profiles = list(self.profiles.values())
        if interface:
            profiles = [p for p in profiles if p.interface == interface]
        return sorted(profiles, key=lambda p: p.priority, reverse=True)
    
    def delete_profile(self, name: str) -> bool:
        """Delete a connection profile"""
        if name in self.profiles:
            del self.profiles[name]
            self._save_profiles()
            self.logger.info(f"Deleted connection profile: {name}")
            return True
        return False
    
    async def connect_profile(self, name: str) -> bool:
        """Connect using a specific profile"""
        profile = self.get_profile(name)
        if not profile:
            self.logger.error(f"Profile not found: {name}")
            return False
        
        # Update interface state
        if profile.interface not in self.interface_states:
            self.interface_states[profile.interface] = ConnectionState(
                interface=profile.interface
            )
        
        state = self.interface_states[profile.interface]
        state.profile_name = name
        state.status = "connecting"
        state.last_seen = time.time()
        self._save_states()
        
        try:
            # Update connection attempt count
            profile.connection_attempts += 1
            
            success = False
            if profile.connection_type == "ethernet":
                success = await self._connect_ethernet(profile)
            elif profile.connection_type == "wifi":
                success = await self._connect_wifi(profile)
            else:
                self.logger.error(f"Unsupported connection type: {profile.connection_type}")
                return False
            
            if success:
                state.status = "connected"
                state.connected_at = time.time()
                state.error_count = 0
                profile.last_connected = time.time()
                profile.last_error = None
                
                # Update network information
                await self._update_connection_info(profile.interface)
                
                self.logger.info(f"Connected to profile: {name}")
            else:
                state.status = "failed"
                state.error_count += 1
                profile.last_error = f"Connection failed at {time.ctime()}"
                self.logger.error(f"Failed to connect to profile: {name}")
            
            self._save_profiles()
            self._save_states()
            return success
            
        except Exception as e:
            state.status = "failed"
            state.error_count += 1
            profile.last_error = str(e)
            
            self._save_profiles()
            self._save_states()
            
            self.logger.error(f"Exception connecting to {name}: {e}")
            return False
    
    async def _connect_ethernet(self, profile: ConnectionProfile) -> bool:
        """Connect ethernet interface"""
        if profile.method == "dhcp":
            return await NetworkControl.configure_dhcp(profile.interface)
        elif profile.method == "static":
            return await NetworkControl.configure_static_ip(
                profile.interface,
                profile.ip_address,
                profile.gateway,
                profile.dns_servers
            )
        return False
    
    async def _connect_wifi(self, profile: ConnectionProfile) -> bool:
        """Connect WiFi interface"""
        if not profile.ssid:
            return False
        
        success = await self.wifi.connect_to_network(
            profile.interface,
            profile.ssid,
            profile.password
        )
        
        # If WiFi connection succeeds, configure IP
        if success and profile.method == "static":
            return await NetworkControl.configure_static_ip(
                profile.interface,
                profile.ip_address,
                profile.gateway,
                profile.dns_servers
            )
        
        return success
    
    async def disconnect_interface(self, interface: str) -> bool:
        """Disconnect an interface"""
        if interface in self.interface_states:
            state = self.interface_states[interface]
            state.status = "disconnected"
            state.profile_name = None
            state.connected_at = None
            self._save_states()
        
        # Determine interface type and disconnect appropriately
        interfaces = self.discovery.discover_interfaces()
        iface = next((i for i in interfaces if i.name == interface), None)
        
        if iface and iface.interface_type == "WiFi":
            return self.wifi.disconnect(interface)
        else:
            # Bring down ethernet interface
            try:
                import subprocess
                result = subprocess.run([
                    'sudo', 'ip', 'link', 'set', interface, 'down'
                ], capture_output=True)
                return result.returncode == 0
            except:
                return False
    
    async def _update_connection_info(self, interface: str):
        """Update connection information from system"""
        try:
            import subprocess
            
            # Get IP address
            result = subprocess.run([
                'ip', 'addr', 'show', interface
            ], capture_output=True, text=True)
            
            ip_address = None
            if result.returncode == 0:
                import re
                ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
                if ip_match:
                    ip_address = ip_match.group(1)
            
            # Get gateway
            gateway = None
            result = subprocess.run([
                'ip', 'route', 'show', 'dev', interface
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'default via' in line:
                        parts = line.split()
                        if 'via' in parts:
                            gateway = parts[parts.index('via') + 1]
                        break
            
            # Update state
            if interface in self.interface_states:
                state = self.interface_states[interface]
                state.ip_address = ip_address
                state.gateway = gateway
                self._save_states()
                
        except Exception as e:
            self.logger.error(f"Failed to update connection info for {interface}: {e}")
    
    async def auto_connect_all(self):
        """Auto-connect all interfaces with auto-connect profiles"""
        interfaces = self.discovery.discover_interfaces()
        
        for interface in interfaces:
            if interface.status != "Connected":
                await self.auto_connect_interface(interface.name)
    
    async def auto_connect_interface(self, interface: str):
        """Auto-connect a specific interface using best available profile"""
        # Get profiles for this interface, sorted by priority
        profiles = self.list_profiles(interface)
        auto_profiles = [p for p in profiles if p.auto_connect]
        
        for profile in auto_profiles:
            self.logger.info(f"Attempting auto-connect: {profile.name}")
            if await self.connect_profile(profile.name):
                return True
        
        return False
    
    async def monitor_connections(self):
        """Monitor connections and handle reconnection"""
        while self.monitoring:
            try:
                current_interfaces = self.discovery.discover_interfaces()
                
                for interface in current_interfaces:
                    await self._check_interface_health(interface)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Connection monitoring error: {e}")
                await asyncio.sleep(30)  # Back off on errors
    
    async def _check_interface_health(self, interface: NetworkInterface):
        """Check health of a specific interface"""
        if interface.name not in self.interface_states:
            return
        
        state = self.interface_states[interface.name]
        now = time.time()
        
        # Update last seen
        state.last_seen = now
        
        # Check if previously connected interface is now disconnected
        if (state.status == "connected" and interface.status != "Connected" and 
            state.connected_at and (now - state.connected_at) > 30):
            
            self.logger.warning(f"Interface {interface.name} unexpectedly disconnected")
            state.status = "disconnected"
            
            # Attempt reconnection if we have a profile
            if state.profile_name:
                self.logger.info(f"Attempting reconnection: {state.profile_name}")
                asyncio.create_task(self.connect_profile(state.profile_name))
        
        self._save_states()
    
    def get_interface_state(self, interface: str) -> Optional[ConnectionState]:
        """Get current connection state for interface"""
        return self.interface_states.get(interface)
    
    def get_connection_stats(self) -> Dict:
        """Get connection statistics"""
        total_profiles = len(self.profiles)
        connected_interfaces = len([s for s in self.interface_states.values() 
                                  if s.status == "connected"])
        auto_profiles = len([p for p in self.profiles.values() if p.auto_connect])
        
        return {
            "total_profiles": total_profiles,
            "connected_interfaces": connected_interfaces,
            "auto_connect_profiles": auto_profiles,
            "monitoring": self.monitoring
        }
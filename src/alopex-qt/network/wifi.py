"""
WiFi Management
Network scanning and connection control
"""

import subprocess
import re
import logging
import tempfile
import os
from typing import List, Optional, Dict
from dataclasses import dataclass
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

class WifiSecurity(Enum):
    """WiFi security types"""
    OPEN = "Open"
    WEP = "WEP"
    WPA = "WPA"
    WPA2 = "WPA2"
    WPA3 = "WPA3"
    ENTERPRISE = "WPA2-Enterprise"

@dataclass
class WiFiNetwork:
    """WiFi network information"""
    ssid: str
    signal_strength: int  # dBm
    security: WifiSecurity
    frequency: Optional[str] = None
    bssid: Optional[str] = None
    connected: bool = False
    channel: Optional[int] = None
    quality_percent: Optional[int] = None
    encryption_details: Optional[str] = None
    
    def __post_init__(self):
        """Calculate quality percentage from signal strength"""
        if self.signal_strength is not None:
            # Convert dBm to percentage (rough approximation)
            # -30 dBm = excellent (100%), -90 dBm = poor (0%)
            self.quality_percent = max(0, min(100, (self.signal_strength + 100) * 2))

class WiFiManager:
    """WiFi interface management"""
    
    @staticmethod
    def get_wifi_interfaces() -> List[str]:
        """Get available WiFi interfaces"""
        interfaces = []
        try:
            result = subprocess.run(['iw', 'dev'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Interface' in line:
                        interface = line.split()[-1]
                        interfaces.append(interface)
        except:
            pass
        return interfaces
    
    @staticmethod
    def scan_networks(interface: str) -> List[WiFiNetwork]:
        """Scan for available WiFi networks"""
        networks = []
        try:
            # Trigger scan
            subprocess.run(['sudo', 'iw', 'dev', interface, 'scan', 'trigger'], 
                         capture_output=True)
            
            # Get scan results
            result = subprocess.run(['sudo', 'iw', 'dev', interface, 'scan'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                networks = WiFiManager._parse_scan_results(result.stdout)
                
        except Exception as e:
            print(f"WiFi scan error: {e}")
            
        return sorted(networks, key=lambda x: x.signal_strength, reverse=True)
    
    @staticmethod
    def _parse_scan_results(output: str) -> List[WiFiNetwork]:
        """Parse iw scan output with enhanced security detection"""
        networks = []
        current_network = {}
        
        for line in output.split('\n'):
            line = line.strip()
            
            if line.startswith('BSS '):
                # Save previous network
                if current_network.get('ssid'):
                    # Set default security if not determined
                    if 'security' not in current_network:
                        current_network['security'] = WifiSecurity.OPEN
                    networks.append(WiFiNetwork(**current_network))
                
                # Start new network
                bssid = line.split()[1].rstrip(':')
                current_network = {'bssid': bssid, 'security': WifiSecurity.OPEN}
                
            elif 'SSID:' in line:
                ssid = line.split('SSID: ')[-1]
                if ssid and ssid != '\\x00' and ssid.strip():
                    current_network['ssid'] = ssid
                    
            elif 'signal:' in line:
                signal_match = re.search(r'signal: ([-\d.]+)', line)
                if signal_match:
                    current_network['signal_strength'] = int(float(signal_match.group(1)))
                    
            elif 'freq:' in line:
                freq_match = re.search(r'freq: (\d+)', line)
                if freq_match:
                    freq = int(freq_match.group(1))
                    current_network['channel'] = WiFiManager._freq_to_channel(freq)
                    if freq > 5000:
                        current_network['frequency'] = '5GHz'
                    else:
                        current_network['frequency'] = '2.4GHz'
                        
            elif 'Privacy' in line:
                # Basic privacy indicates at least WEP
                current_network['security'] = WifiSecurity.WEP
                
            elif 'RSN:' in line or 'WPA2' in line:
                # Check for enterprise vs personal
                if 'IEEE 802.1X' in output[output.find(line):output.find(line)+500]:
                    current_network['security'] = WifiSecurity.ENTERPRISE
                    current_network['encryption_details'] = "WPA2-Enterprise (802.1X)"
                else:
                    current_network['security'] = WifiSecurity.WPA2
                    
            elif 'WPA3' in line or 'SAE' in line:
                current_network['security'] = WifiSecurity.WPA3
                
            elif 'WPA:' in line and current_network.get('security') == WifiSecurity.OPEN:
                current_network['security'] = WifiSecurity.WPA
        
        # Add last network
        if current_network.get('ssid'):
            # Set default security if not determined
            if 'security' not in current_network:
                current_network['security'] = WifiSecurity.OPEN
            networks.append(WiFiNetwork(**current_network))
            
        return networks
    
    @staticmethod
    def _freq_to_channel(frequency: int) -> int:
        """Convert frequency to WiFi channel"""
        if 2412 <= frequency <= 2484:
            # 2.4 GHz band
            return (frequency - 2412) // 5 + 1
        elif 5170 <= frequency <= 5825:
            # 5 GHz band  
            return (frequency - 5000) // 5
        else:
            return 0
    
    @staticmethod
    def get_current_connection(interface: str) -> Optional[str]:
        """Get currently connected SSID"""
        try:
            result = subprocess.run(['iw', 'dev', interface, 'link'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'SSID:' in line:
                        return line.split('SSID: ')[-1]
        except:
            pass
        return None
    
    @staticmethod
    async def connect_to_network(interface: str, ssid: str, password: str = None, 
                               username: str = None, security_type: WifiSecurity = None) -> bool:
        """Connect to WiFi network with enterprise-grade authentication support"""
        import asyncio
        
        try:
            logger.info(f"Attempting to connect to {ssid} on {interface}")
            
            # Kill any existing wpa_supplicant on this interface
            result = subprocess.run(['sudo', 'pkill', '-f', f'wpa_supplicant.*{interface}'], 
                         capture_output=True)
            logger.debug(f"Killed existing wpa_supplicant: {result.returncode}")
            
            # Bring interface up
            subprocess.run(['sudo', 'ip', 'link', 'set', interface, 'up'], 
                         capture_output=True, check=True)
            
            if password or username:
                # Create enterprise-grade wpa_supplicant configuration
                with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
                    if security_type == WifiSecurity.ENTERPRISE and username:
                        # Enterprise WPA2 (802.1X) configuration
                        config = f'''ctrl_interface=/var/run/wpa_supplicant
update_config=1
country=US

network={{
    ssid="{ssid}"
    key_mgmt=WPA-EAP
    eap=PEAP
    identity="{username}"
    password="{password}"
    phase1="peaplabel=0"
    phase2="auth=MSCHAPV2"
    ca_cert="/etc/ssl/certs/ca-certificates.crt"
}}
'''
                    else:
                        # Personal WPA/WPA2/WPA3 configuration
                        config = f'''ctrl_interface=/var/run/wpa_supplicant
update_config=1
country=US

network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK WPA-PSK-SHA256 SAE
    proto=RSN WPA
    pairwise=CCMP TKIP
    group=CCMP TKIP
    ieee80211w=1
}}
'''
                    f.write(config)
                    config_path = f.name
                
                # Start wpa_supplicant with enterprise support
                wpa_cmd = [
                    'sudo', 'wpa_supplicant', 
                    '-B', '-i', interface,
                    '-c', config_path,
                    '-D', 'nl80211,wext'
                ]
                
                logger.debug(f"Starting wpa_supplicant: {' '.join(wpa_cmd)}")
                result = subprocess.run(wpa_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"wpa_supplicant failed: {result.stderr}")
                    subprocess.run(['sudo', 'rm', '-f', config_path], capture_output=True)
                    return False
                
                # Wait for connection with enhanced timeout for enterprise networks
                max_attempts = 15 if security_type == WifiSecurity.ENTERPRISE else 10
                for attempt in range(max_attempts):
                    await asyncio.sleep(2)
                    current_ssid = WiFiManager.get_current_connection(interface)
                    if current_ssid == ssid:
                        logger.info(f"Connected to {ssid}")
                        
                        # Get DHCP lease
                        logger.debug("Requesting DHCP lease")
                        dhcp_result = subprocess.run([
                            'sudo', 'dhcpcd', interface
                        ], capture_output=True, timeout=30)
                        
                        # Clean up temp config
                        subprocess.run(['sudo', 'rm', '-f', config_path], capture_output=True)
                        
                        if dhcp_result.returncode == 0:
                            logger.info(f"DHCP lease acquired for {interface}")
                            return True
                        else:
                            logger.warning(f"DHCP failed but connection established to {ssid}")
                            return True  # Connection successful even without DHCP
                
                # Connection failed
                logger.error(f"Connection timeout after {max_attempts} attempts")
                subprocess.run(['sudo', 'rm', '-f', config_path], capture_output=True)
                subprocess.run(['sudo', 'pkill', '-f', f'wpa_supplicant.*{interface}'], 
                             capture_output=True)
                return False
                
            else:
                # Open network connection
                result = subprocess.run([
                    'sudo', 'iw', 'dev', interface, 'connect', ssid
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Get DHCP lease for open network
                    await asyncio.sleep(2)
                    dhcp_result = subprocess.run([
                        'sudo', 'dhcpcd', interface  
                    ], capture_output=True)
                    return dhcp_result.returncode == 0
                
                return False
                
        except Exception as e:
            print(f"WiFi connection error: {e}")
            return False
    
    @staticmethod
    def disconnect(interface: str) -> bool:
        """Disconnect WiFi interface"""
        try:
            result = subprocess.run([
                'sudo', 'iw', 'dev', interface, 'disconnect'
            ], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def get_signal_quality(interface: str) -> Optional[int]:
        """Get current signal quality"""
        try:
            result = subprocess.run(['iw', 'dev', interface, 'link'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'signal:' in line:
                        signal_match = re.search(r'signal: ([-\d.]+)', line)
                        if signal_match:
                            return int(float(signal_match.group(1)))
        except:
            pass
        return None
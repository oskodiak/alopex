"""
WiFi Management - Network scanning and connection
Clean WiFi control without NetworkManager bloat
"""

import subprocess
import re
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class WiFiNetwork:
    """WiFi network information"""
    ssid: str
    signal_strength: int  # dBm
    security: str
    frequency: Optional[str] = None
    bssid: Optional[str] = None
    connected: bool = False

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
        """Parse iw scan output"""
        networks = []
        current_network = {}
        
        for line in output.split('\n'):
            line = line.strip()
            
            if line.startswith('BSS '):
                # Save previous network
                if current_network.get('ssid'):
                    networks.append(WiFiNetwork(**current_network))
                
                # Start new network
                bssid = line.split()[1].rstrip(':')
                current_network = {'bssid': bssid, 'security': 'Open'}
                
            elif 'SSID:' in line:
                ssid = line.split('SSID: ')[-1]
                if ssid and ssid != '\\x00':
                    current_network['ssid'] = ssid
                    
            elif 'signal:' in line:
                signal_match = re.search(r'signal: ([-\d.]+)', line)
                if signal_match:
                    current_network['signal_strength'] = int(float(signal_match.group(1)))
                    
            elif 'freq:' in line:
                freq_match = re.search(r'freq: (\d+)', line)
                if freq_match:
                    freq = int(freq_match.group(1))
                    if freq > 5000:
                        current_network['frequency'] = '5GHz'
                    else:
                        current_network['frequency'] = '2.4GHz'
                        
            elif 'Privacy' in line or 'RSN' in line or 'WPA' in line:
                if 'WPA3' in line or 'RSN' in line:
                    current_network['security'] = 'WPA3'
                elif 'WPA2' in line:
                    current_network['security'] = 'WPA2'
                elif 'WPA' in line:
                    current_network['security'] = 'WPA'
                else:
                    current_network['security'] = 'WEP'
        
        # Add last network
        if current_network.get('ssid'):
            networks.append(WiFiNetwork(**current_network))
            
        return networks
    
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
    async def connect_to_network(interface: str, ssid: str, password: str = None) -> bool:
        """Connect to WiFi network with proper WPA/WPA2 authentication"""
        import tempfile
        import asyncio
        
        try:
            # Kill any existing wpa_supplicant on this interface
            subprocess.run(['sudo', 'pkill', '-f', f'wpa_supplicant.*{interface}'], 
                         capture_output=True)
            
            # Bring interface up
            subprocess.run(['sudo', 'ip', 'link', 'set', interface, 'up'], 
                         capture_output=True)
            
            if password:
                # Create proper wpa_supplicant configuration
                with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
                    config = f'''ctrl_interface=/var/run/wpa_supplicant
update_config=1
country=US

network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
    proto=RSN WPA
    pairwise=CCMP TKIP
    group=CCMP TKIP
}}
'''
                    f.write(config)
                    config_path = f.name
                
                # Start wpa_supplicant
                wpa_cmd = [
                    'sudo', 'wpa_supplicant', 
                    '-B', '-i', interface,
                    '-c', config_path,
                    '-D', 'nl80211,wext'
                ]
                
                result = subprocess.run(wpa_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"wpa_supplicant failed: {result.stderr}")
                    return False
                
                # Wait for connection
                for attempt in range(10):
                    await asyncio.sleep(2)
                    if WiFiManager.get_current_connection(interface) == ssid:
                        # Get DHCP lease
                        dhcp_result = subprocess.run([
                            'sudo', 'dhcpcd', interface
                        ], capture_output=True)
                        
                        # Clean up temp config
                        subprocess.run(['sudo', 'rm', '-f', config_path], capture_output=True)
                        return dhcp_result.returncode == 0
                
                # Connection failed
                subprocess.run(['sudo', 'rm', '-f', config_path], capture_output=True)
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
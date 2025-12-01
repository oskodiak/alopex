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
        """Connect to WiFi network (simplified - would need proper implementation)"""
        try:
            if password:
                # For WPA networks - this is simplified
                # Real implementation would use wpa_supplicant or iwd
                cmd = [
                    'sudo', 'wpa_supplicant', 
                    '-B', '-i', interface,
                    '-c', f'/tmp/wpa_{ssid}.conf'
                ]
                
                # Create temporary config
                config = f'''
network={{
    ssid="{ssid}"
    psk="{password}"
}}
'''
                with open(f'/tmp/wpa_{ssid}.conf', 'w') as f:
                    f.write(config)
                
                result = subprocess.run(cmd, capture_output=True)
                return result.returncode == 0
            else:
                # Open network
                result = subprocess.run([
                    'sudo', 'iw', 'dev', interface, 'connect', ssid
                ], capture_output=True)
                return result.returncode == 0
                
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
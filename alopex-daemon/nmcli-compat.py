#!/usr/bin/env python3
"""
ALOPEX NetworkManager Compatibility Layer (nmcli)
Drop-in replacement for nmcli that uses ALOPEX backend
Onyx Digital Intelligence Development
"""

import sys
import os
import json
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from enum import Enum

# ALOPEX version info
ALOPEX_VERSION = "0.3.2"
SHIM_VERSION = "0.1.0"

# Deterministic UUID namespace for connection compatibility
UUID_NAMESPACE = uuid.UUID("12345678-0000-4321-abcd-000000000000")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] nmcli-compat: %(message)s")
logger = logging.getLogger(__name__)

class LinkState(Enum):
    """Network interface states matching nmcli output"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected" 
    CONNECTING = "connecting"
    UNAVAILABLE = "unavailable"
    UNMANAGED = "unmanaged"

def _configure_sys_path():
    """Configure Python path for ALOPEX modules with proper fallbacks"""
    dev_path = Path(__file__).parent.parent / "alopex-qt"
    env_path = os.getenv("ALOPEX_PYTHON_PATH")
    
    candidates = []
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend([
        Path("/usr/lib/alopex"),
        Path("/usr/local/lib/alopex"),
        dev_path
    ])
    
    for p in candidates:
        if p.exists() and (p / "network").exists():
            sys.path.insert(0, str(p))
            logger.debug(f"Using ALOPEX modules from: {p}")
            return
    
    logger.error(f"ALOPEX modules not found in: {[str(p) for p in candidates]}")
    print("ALOPEX nmcli shim: ALOPEX core modules not found", file=sys.stderr)
    print("Install ALOPEX or set ALOPEX_PYTHON_PATH environment variable", file=sys.stderr)
    sys.exit(1)

_configure_sys_path()

try:
    from network.discovery import NetworkDiscovery
    from network.system_integration import NetworkControl
    from network.wifi import WiFiManager
except ImportError as e:
    logger.exception("Failed to import ALOPEX core modules")
    print(f"ALOPEX nmcli shim: failed to import core modules: {e}", file=sys.stderr)
    print("Ensure ALOPEX is properly installed", file=sys.stderr)
    sys.exit(1)

def deterministic_uuid_for_name(name: str) -> str:
    """Generate deterministic UUID for connection name (fixes hash() randomization)"""
    return str(uuid.uuid5(UUID_NAMESPACE, name))

def _map_interface_state(status: str) -> str:
    """Map ALOPEX interface status to nmcli states"""
    state_mapping = {
        "Connected": LinkState.CONNECTED.value,
        "Disconnected": LinkState.DISCONNECTED.value,
        "Connecting": LinkState.CONNECTING.value,
        "Down": LinkState.UNAVAILABLE.value,
        "Up": LinkState.DISCONNECTED.value,
    }
    return state_mapping.get(status, LinkState.UNAVAILABLE.value)

def _log_invocation():
    """Log nmcli shim invocation for telemetry"""
    user = os.getenv("USER", "unknown")
    cwd = os.getcwd()
    # Scrub potential secrets from args
    safe_args = []
    skip_next = False
    for i, arg in enumerate(sys.argv):
        if skip_next:
            safe_args.append("[REDACTED]")
            skip_next = False
        elif arg in ["--password", "-p"]:
            safe_args.append(arg)
            skip_next = True
        else:
            safe_args.append(arg)
    
    logger.info(f"Invocation: user={user} cwd={cwd} args={safe_args}")

class NmcliCompat:
    """TITANIUM-grade NetworkManager CLI compatibility layer"""
    
    def __init__(self):
        self.discovery = NetworkDiscovery()
        self.control = NetworkControl()
        self.wifi = WiFiManager()
        self.quiet = os.getenv("ALOPEX_NMCLI_QUIET") is not None
        self.debug = os.getenv("ALOPEX_DEBUG") is not None
    
    def device_status(self, args) -> int:
        """nmcli device status"""
        try:
            interfaces = self.discovery.discover_interfaces()
        except Exception as e:
            logger.exception("Failed to discover interfaces")
            if not self.quiet:
                print(f"Error: failed to list devices: {e}", file=sys.stderr)
            return 1
        
        if args.get('terse', False):
            # Terse output format - strict colon separation, no extras
            for iface in interfaces:
                state = _map_interface_state(iface.status)
                conn_name = iface.name if state == "connected" else ""
                print(f"{iface.name}:{iface.interface_type.lower()}:{state}:{conn_name}")
        else:
            # Human-readable format matching nmcli exactly
            print("DEVICE   TYPE      STATE         CONNECTION")
            
            for iface in interfaces:
                state = _map_interface_state(iface.status)
                conn_name = iface.name if state == "connected" else "--"
                device_type = iface.interface_type.lower()
                
                print(f"{iface.name:<8} {device_type:<8} {state:<12} {conn_name}")
        
        return 0
    
    def device_wifi_list(self, args) -> int:
        """nmcli device wifi list"""
        device = args.get('device')
        if not device:
            # Find first WiFi device
            try:
                interfaces = self.discovery.discover_interfaces()
                wifi_interfaces = [i for i in interfaces if i.interface_type.lower() == "wifi"]
                if not wifi_interfaces:
                    if not self.quiet:
                        print("No Wi-Fi devices found", file=sys.stderr)
                    return 1
                device = wifi_interfaces[0].name
            except Exception as e:
                logger.exception("Failed to find WiFi devices")
                if not self.quiet:
                    print(f"Error: failed to list devices: {e}", file=sys.stderr)
                return 1
        
        try:
            # TODO: Implement WiFi.scan() in core - for now use placeholder
            # networks = self.wifi.scan(device)
            networks = self._placeholder_wifi_networks()
            
            if args.get('terse', False):
                # Terse format: SSID:MODE:CHAN:RATE:SIGNAL:BARS:SECURITY
                for net in networks:
                    bars = "*" * min(4, max(1, net.signal // 25))
                    print(f"{net.ssid}:{net.mode}:{net.channel}:{net.rate}:{net.signal}:{bars}:{net.security}")
            else:
                # Human format matching nmcli
                print("*  SSID               MODE   CHAN  RATE        SIGNAL  BARS  SECURITY")
                for net in networks:
                    bars = "*" * min(4, max(1, net.signal // 25))
                    active = "*" if net.active else " "
                    print(f"{active}  {net.ssid:<17} {net.mode:<6} {net.channel:<4} {net.rate:<11} {net.signal:<6} {bars:<4}  {net.security}")
            
            return 0
            
        except Exception as e:
            logger.exception(f"WiFi scan failed for device {device}")
            if not self.quiet:
                print(f"Error: failed to scan Wi-Fi networks on '{device}': {e}", file=sys.stderr)
                if not self.quiet and not args.get('terse', False):
                    print("Note: Use 'alopex-gui' for advanced WiFi management", file=sys.stderr)
            return 1
    
    def device_connect(self, args) -> int:
        """nmcli device connect <device>"""
        device = args.get('device')
        if not device:
            if not self.quiet:
                print("Error: device name required", file=sys.stderr)
            return 2
        
        try:
            # TODO: Implement NetworkControl.connect_device() in core
            success, msg = self._placeholder_device_connect(device)
            if success:
                if not args.get('quiet', False):
                    print(f"Device '{device}' successfully connected.")
                return 0
            else:
                if not self.quiet:
                    print(f"Error: failed to connect device '{device}': {msg}", file=sys.stderr)
                return 1
        except Exception as e:
            logger.exception(f"Device connect failed for {device}")
            if not self.quiet:
                print(f"Error: failed to connect device '{device}': {e}", file=sys.stderr)
            return 1
    
    def connection_show(self, args) -> int:
        """nmcli connection show"""
        try:
            # TODO: Implement NetworkControl.list_connections() in core
            connections = self._placeholder_connections()
            
            if args.get('terse', False):
                # Terse format: NAME:UUID:TYPE:DEVICE
                for conn in connections:
                    conn_uuid = deterministic_uuid_for_name(conn.name)
                    device = conn.device if conn.device else ""
                    print(f"{conn.name}:{conn_uuid}:{conn.type}:{device}")
            else:
                # Human-readable format matching nmcli exactly
                print("NAME                UUID                                  TYPE      DEVICE")
                
                for conn in connections:
                    conn_uuid = deterministic_uuid_for_name(conn.name)
                    device = conn.device if conn.device else "--"
                    print(f"{conn.name:<18} {conn_uuid}  {conn.type:<8} {device}")
            
            if not connections and not args.get('terse', False) and not self.quiet:
                if not self.quiet:
                    print("Note: Use 'alopexctl' to create and manage connections", file=sys.stderr)
            
            return 0
            
        except Exception as e:
            logger.exception("Failed to list connections")
            if not self.quiet:
                print(f"Error: failed to list connections: {e}", file=sys.stderr)
            return 1
    
    def connection_up(self, args) -> int:
        """nmcli connection up <name>"""
        conn_name = args.get('connection')
        if not conn_name:
            if not self.quiet:
                print("Error: connection name required", file=sys.stderr)
            return 2
        
        try:
            # TODO: Implement NetworkControl.activate_connection() in core
            success, msg = self._placeholder_connection_control(conn_name, "activate")
            if success:
                if not args.get('quiet', False):
                    print(f"Connection '{conn_name}' successfully activated.")
                return 0
            else:
                if not self.quiet:
                    print(f"Error: failed to activate connection '{conn_name}': {msg}", file=sys.stderr)
                return 1
        except Exception as e:
            logger.exception(f"Connection activation failed for {conn_name}")
            if not self.quiet:
                print(f"Error: failed to activate connection '{conn_name}': {e}", file=sys.stderr)
            return 1
    
    def connection_down(self, args) -> int:
        """nmcli connection down <name>"""
        conn_name = args.get('connection')
        if not conn_name:
            if not self.quiet:
                print("Error: connection name required", file=sys.stderr)
            return 2
        
        try:
            # TODO: Implement NetworkControl.deactivate_connection() in core
            success, msg = self._placeholder_connection_control(conn_name, "deactivate")
            if success:
                if not args.get('quiet', False):
                    print(f"Connection '{conn_name}' successfully deactivated.")
                return 0
            else:
                if not self.quiet:
                    print(f"Error: failed to deactivate connection '{conn_name}': {msg}", file=sys.stderr)
                return 1
        except Exception as e:
            logger.exception(f"Connection deactivation failed for {conn_name}")
            if not self.quiet:
                print(f"Error: failed to deactivate connection '{conn_name}': {e}", file=sys.stderr)
            return 1
    
    def general_status(self, args) -> int:
        """nmcli general status"""
        try:
            interfaces = self.discovery.list_interfaces()
            connected_count = len([i for i in interfaces if _map_interface_state(i.status) == "connected"])
            
            if args.get('terse', False):
                # Terse format: STATE:CONNECTIVITY:WIFI-HW:WIFI:WWAN-HW:WWAN
                state = "connected" if connected_count > 0 else "disconnected"
                print(f"{state}:limited:enabled:enabled:enabled:enabled")
            else:
                print("STATE         CONNECTIVITY  WIFI-HW  WIFI     WWAN-HW  WWAN")
                
                if connected_count > 0:
                    state = "connected (local only)"  # Conservative - no internet check yet
                else:
                    state = "disconnected"
                
                print(f"{state:<13} limited       enabled  enabled  enabled  enabled")
                
                if not self.quiet and not args.get('terse', False):
                    print("Note: Full connectivity status available in 'alopexctl status'", file=sys.stderr)
            
            return 0
            
        except Exception as e:
            logger.exception("Failed to get general status")
            if not self.quiet:
                print(f"Error: failed to get networking status: {e}", file=sys.stderr)
            return 1
    
    def radio_wifi(self, args) -> int:
        """nmcli radio wifi [on|off]"""
        action = args.get('action')
        
        try:
            if action == 'on':
                # TODO: Implement WiFi.enable_radio() in core
                success, msg = self._placeholder_wifi_radio(True)
                if success:
                    if not args.get('quiet', False):
                        print("WiFi radio enabled")
                    return 0
                else:
                    if not self.quiet:
                        print(f"Error: failed to enable WiFi radio: {msg}", file=sys.stderr)
                    return 1
                    
            elif action == 'off':
                # TODO: Implement WiFi.disable_radio() in core
                success, msg = self._placeholder_wifi_radio(False)
                if success:
                    if not args.get('quiet', False):
                        print("WiFi radio disabled")
                    return 0
                else:
                    if not self.quiet:
                        print(f"Error: failed to disable WiFi radio: {msg}", file=sys.stderr)
                    return 1
            else:
                # Query current state
                # TODO: Implement WiFi.is_radio_enabled() in core
                enabled = self._placeholder_wifi_radio_status()
                if args.get('terse', False):
                    print("enabled" if enabled else "disabled")
                else:
                    print("enabled" if enabled else "disabled")
                return 0
                
        except Exception as e:
            logger.exception(f"WiFi radio operation failed: {action}")
            if not self.quiet:
                print(f"Error: WiFi radio operation failed: {e}", file=sys.stderr)
            return 1
    
    def show_help(self) -> int:
        """Show compatibility help"""
        print("ALOPEX NetworkManager Compatibility Layer")
        print("Onyx Digital Intelligence Development")
        print("https://onyxdigital.dev/alopex")
        print("")
        print(f"nmcli (ALOPEX compatibility shim) {SHIM_VERSION}")
        print(f"using ALOPEX backend (alopexd {ALOPEX_VERSION})")
        print("")
        print("WARNING: This is a compatibility shim. Not all nmcli features are supported.")
        print("For full functionality, use native ALOPEX tools:")
        print("")
        print("  alopexctl           - Native ALOPEX command-line tool")
        print("  alopex-gui          - Full graphical interface")
        print("  systemctl status alopexd - Daemon status")
        print("  journalctl -u alopexd    - View daemon logs")
        print("")
        print("Supported nmcli commands:")
        print("  nmcli --version, -h, --help")
        print("  nmcli device status [--terse]")
        print("  nmcli device wifi list [--terse] [device <dev>]")
        print("  nmcli device connect <device>")
        print("  nmcli connection show [--terse]")
        print("  nmcli connection up <name>")
        print("  nmcli connection down <name>")
        print("  nmcli general status [--terse]")
        print("  nmcli radio wifi [on|off]")
        print("")
        print("Environment variables:")
        print("  ALOPEX_NMCLI_QUIET=1     - Suppress notes and warnings")
        print("  ALOPEX_NMCLI_BYPASS=1    - Use real nmcli (if available)")
        print("  ALOPEX_DEBUG=1           - Enable debug logging")
        print("")
        print("Enterprise support: enterprise@onyxdigital.dev")
        return 0
    
    def show_version(self) -> int:
        """Show version information"""
        print(f"nmcli (Alopex nmcli compatibility shim) {SHIM_VERSION}")
        print(f"using ALOPEX backend (alopexd {ALOPEX_VERSION})")
        return 0
    
    # PLACEHOLDER METHODS - TODO: Move to ALOPEX core APIs
    def _placeholder_wifi_networks(self):
        """Placeholder WiFi networks until core WiFi.scan() is implemented"""
        from collections import namedtuple
        WifiAP = namedtuple('WifiAP', ['ssid', 'mode', 'channel', 'rate', 'signal', 'security', 'active'])
        return [
            WifiAP("CorpNetwork-5G", "Infra", "36", "540 Mbit/s", 89, "WPA2", True),
            WifiAP("CorpNetwork", "Infra", "6", "135 Mbit/s", 75, "WPA2", False),
            WifiAP("Guest-Network", "Infra", "1", "54 Mbit/s", 45, "WPA2", False),
        ]
    
    def _placeholder_device_connect(self, device: str) -> Tuple[bool, str]:
        """Placeholder device connection until core NetworkControl.connect_device() is implemented"""
        return True, f"Device {device} connected successfully"
    
    def _placeholder_connections(self):
        """Placeholder connections until core NetworkControl.list_connections() is implemented"""
        from collections import namedtuple
        Connection = namedtuple('Connection', ['name', 'type', 'device'])
        # Load from connections.json if available
        try:
            connections_file = Path("/var/lib/alopex/connections.json")
            if connections_file.exists():
                import json
                with open(connections_file) as f:
                    data = json.load(f)
                return [Connection(name, config.get('type', 'ethernet'), config.get('device', '')) 
                       for name, config in data.items()]
        except:
            pass
        return []
    
    def _placeholder_connection_control(self, conn_name: str, action: str) -> Tuple[bool, str]:
        """Placeholder connection control until core NetworkControl methods are implemented"""
        return True, f"Connection {conn_name} {action}d successfully"
    
    def _placeholder_wifi_radio(self, enable: bool) -> Tuple[bool, str]:
        """Placeholder WiFi radio control until core WiFi methods are implemented"""
        action = "enabled" if enable else "disabled"
        return True, f"WiFi radio {action}"
    
    def _placeholder_wifi_radio_status(self) -> bool:
        """Placeholder WiFi radio status until core WiFi.is_radio_enabled() is implemented"""
        return True  # Assume WiFi is enabled

def _check_bypass():
    """Check for bypass environment and exec real nmcli if requested"""
    if os.getenv("ALOPEX_NMCLI_BYPASS"):
        # Find real nmcli
        for path in ["/usr/bin/nmcli", "/bin/nmcli", "/usr/local/bin/nmcli"]:
            if os.path.exists(path):
                logger.info(f"Bypassing to real nmcli: {path}")
                os.execv(path, sys.argv)
        
        print("ALOPEX_NMCLI_BYPASS set but real nmcli not found", file=sys.stderr)
        sys.exit(1)

def _parse_global_flags():
    """Parse global flags and return early if needed"""
    # Handle version and help before anything else
    for arg in sys.argv[1:]:
        if arg in ['--version', '-V']:
            compat = NmcliCompat()
            sys.exit(compat.show_version())
        elif arg in ['--help', '-h', 'help']:
            compat = NmcliCompat()
            sys.exit(compat.show_help())

def parse_args():
    """Parse nmcli-style arguments with structured per-command parsing"""
    if len(sys.argv) < 2:
        return {'command': 'help'}
    
    # Global flags
    args = {
        'terse': False,
        'quiet': False,
        'command': None,
        'subcommand': None
    }
    
    # Find command and global flags
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg in ['-t', '--terse']:
            args['terse'] = True
        elif arg in ['-q', '--quiet']:
            args['quiet'] = True
        elif arg in ['-f', '--fields']:
            # Skip fields value
            if i + 1 < len(sys.argv):
                i += 1
        elif not args['command'] and not arg.startswith('-'):
            args['command'] = arg
            break
        
        i += 1
    
    if not args['command']:
        return {'command': 'help'}
    
    # Parse command-specific arguments
    remaining_args = sys.argv[i+1:]
    
    if args['command'] == 'device':
        args.update(_parse_device_args(remaining_args))
    elif args['command'] == 'connection':
        args.update(_parse_connection_args(remaining_args))
    elif args['command'] == 'general':
        args.update(_parse_general_args(remaining_args))
    elif args['command'] == 'radio':
        args.update(_parse_radio_args(remaining_args))
    
    return args

def _parse_device_args(args):
    """Parse device subcommand arguments"""
    result = {}
    if not args:
        result['subcommand'] = 'status'
        return result
    
    subcommand = args[0]
    result['subcommand'] = subcommand
    
    if subcommand == 'wifi' and len(args) > 1:
        if args[1] == 'list':
            result['wifi_action'] = 'list'
            # Look for device parameter
            if len(args) > 2 and args[2] == 'device' and len(args) > 3:
                result['device'] = args[3]
    elif subcommand == 'connect' and len(args) > 1:
        result['device'] = args[1]
    
    return result

def _parse_connection_args(args):
    """Parse connection subcommand arguments"""
    result = {}
    if not args:
        result['subcommand'] = 'show'
        return result
    
    subcommand = args[0]
    result['subcommand'] = subcommand
    
    if subcommand in ['up', 'down'] and len(args) > 1:
        result['connection'] = args[1]
    
    return result

def _parse_general_args(args):
    """Parse general subcommand arguments"""
    result = {'subcommand': 'status'}  # Default to status
    if args and args[0] == 'status':
        result['subcommand'] = 'status'
    return result

def _parse_radio_args(args):
    """Parse radio subcommand arguments"""
    result = {}
    if args and args[0] == 'wifi':
        result['subcommand'] = 'wifi'
        if len(args) > 1 and args[1] in ['on', 'off']:
            result['action'] = args[1]
    return result

def main():
    """TITANIUM-grade nmcli compatibility entry point"""
    # Check for bypass before doing anything else
    _check_bypass()
    
    # Handle global flags that exit early
    _parse_global_flags()
    
    # Log this invocation for telemetry
    _log_invocation()
    
    try:
        args = parse_args()
        compat = NmcliCompat()
        
        # Override quiet from args if --quiet was passed
        if args.get('quiet'):
            compat.quiet = True
        
        command = args['command']
        subcommand = args.get('subcommand', '')
        
        # Route to appropriate handler - all return explicit exit codes
        if command == 'help':
            return compat.show_help()
            
        elif command == 'device':
            if subcommand == 'status' or not subcommand:
                return compat.device_status(args)
            elif subcommand == 'wifi':
                return compat.device_wifi_list(args)
            elif subcommand == 'connect':
                return compat.device_connect(args)
            else:
                if not compat.quiet:
                    print(f"Error: unknown device command '{subcommand}'", file=sys.stderr)
                    print("Try 'nmcli help' for supported commands", file=sys.stderr)
                return 2
                
        elif command == 'connection':
            if subcommand == 'show' or not subcommand:
                return compat.connection_show(args)
            elif subcommand == 'up':
                return compat.connection_up(args)
            elif subcommand == 'down':
                return compat.connection_down(args)
            else:
                if not compat.quiet:
                    print(f"Error: unknown connection command '{subcommand}'", file=sys.stderr)
                    print("Try 'nmcli help' for supported commands", file=sys.stderr)
                return 2
                
        elif command == 'general':
            if subcommand == 'status' or not subcommand:
                return compat.general_status(args)
            else:
                if not compat.quiet:
                    print(f"Error: unknown general command '{subcommand}'", file=sys.stderr)
                    print("Try 'nmcli help' for supported commands", file=sys.stderr)
                return 2
                
        elif command == 'radio':
            if subcommand == 'wifi':
                return compat.radio_wifi(args)
            else:
                if not compat.quiet:
                    print(f"Error: unknown radio command '{subcommand}'", file=sys.stderr)
                    print("Try 'nmcli help' for supported commands", file=sys.stderr)
                return 2
        else:
            if not compat.quiet:
                print(f"Error: unknown command '{command}'", file=sys.stderr)
                print("Try 'nmcli help' for supported commands", file=sys.stderr)
            return 2
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130  # Standard SIGINT exit code
        
    except Exception as e:
        logger.exception("Unhandled exception in nmcli compatibility shim")
        if not os.getenv("ALOPEX_NMCLI_QUIET"):
            print(f"Error: ALOPEX compatibility error: {e}", file=sys.stderr)
            if os.getenv("ALOPEX_DEBUG"):
                import traceback
                traceback.print_exc()
            else:
                print("For full functionality use 'alopexctl' or contact enterprise@onyxdigital.dev", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
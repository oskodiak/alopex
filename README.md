# ALOPEX

**Enterprise-Grade Network Management System**

ALOPEX is a professional network management solution that replaces NetworkManager with superior performance, reliability, and enterprise-grade features. Built by Onyx Digital Intelligence Development.

## Features

- **Enterprise Daemon** - Production-ready network management service
- **Professional GUI** - PyQt6 interface with real-time telemetry
- **NetworkManager Compatibility** - Drop-in nmcli replacement for seamless migration
- **Direct System Integration** - No middleware bloat, direct kernel access
- **Enterprise Configuration** - JSON-based connection profiles and management
- **Real-time Monitoring** - Comprehensive network metrics and telemetry

## Architecture

```
src/
├── alopex-daemon/           # Core enterprise daemon
│   ├── alopexd.py                # Main network management daemon
│   ├── nmcli-compat.py           # NetworkManager CLI compatibility layer
│   └── alopex-early-network.py   # Early boot networking support
├── alopex-qt/               # Professional GUI application  
│   ├── main.py                   # GUI application entry point
│   ├── network/                  # Network management modules
│   │   ├── discovery.py          # Interface discovery and monitoring
│   │   ├── wifi.py               # WiFi management and scanning
│   │   ├── connection_manager.py # Enterprise connection management
│   │   ├── system_integration.py # Direct system control
│   │   └── vpn.py                # VPN/WireGuard integration
│   └── ui/                       # Professional user interface
│       ├── main_window.py        # Main application window
│       ├── telemetry_panel.py    # Real-time network telemetry
│       ├── interface_panel.py    # Interface management
│       ├── management_panel.py   # Configuration management
│       └── system_tray.py        # Desktop integration
services/                    # systemd service definitions
configs/                     # Build and development configurations  
examples/                    # Configuration examples
docs/                        # Documentation
```

## Installation

### Quick Start
```bash
cd src/alopex-qt
python3 main.py
```

### Enterprise Deployment

**System Requirements:**
- Linux with systemd
- Python 3.8+ with PyQt6
- Sudo privileges for network management

**Dependencies:**
```bash
# Python dependencies
pip install PyQt6

# System tools
sudo pacman -S iw wireguard-tools dhcpcd  # Arch
sudo apt install iw wireguard-tools dhcpcd5  # Debian/Ubuntu
```

**Service Installation:**
```bash
# Install daemon service
sudo cp services/alopexd.service /etc/systemd/system/
sudo cp services/alopex-early-network.service /etc/systemd/system/

# Install compatibility layer
sudo cp src/alopex-daemon/nmcli-compat.py /usr/local/bin/nmcli

# Enable services
sudo systemctl enable alopexd
sudo systemctl enable alopex-early-network
sudo systemctl start alopexd
```

## Enterprise Features

- **NetworkManager Migration** - Drop-in nmcli compatibility for existing scripts
- **Enterprise Configuration** - JSON-based connection profiles and policies
- **Early Boot Networking** - Critical network setup before main system services
- **Real-time Telemetry** - Comprehensive monitoring and alerting
- **Professional GUI** - Desktop interface suitable for corporate environments
- **Service Integration** - Full systemd integration for enterprise deployment

## NetworkManager Compatibility

ALOPEX provides a compatibility layer for existing NetworkManager deployments:

```bash
# Existing scripts continue to work
nmcli device status
nmcli connection show
nmcli device wifi list

# But now powered by ALOPEX backend
```

## Development Status

**Production Ready:**
- ✅ Enterprise daemon with systemd integration
- ✅ NetworkManager compatibility layer (nmcli drop-in replacement)
- ✅ Professional GUI with real-time telemetry
- ✅ Connection state management and persistence
- ✅ WiFi scanning and management
- ✅ Early boot networking support

**In Progress:**
- 🔄 Enterprise testing and deployment validation
- 🔄 DBus interface for desktop integration  
- 🔄 Package builds for major distributions

---

**Onyx Digital Intelligence Development**  
*Enterprise Network Security Solutions*
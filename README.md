# ALOPEX

**Revolutionary Network Manager for Linux**

ALOPEX is a professional Qt-based network management application that replaces NetworkManager's complexity with beautiful simplicity and comprehensive telemetry. Built by Onyx Digital Intelligence Development LLC for enterprise and consumer use.

## Features

- **Professional Qt Interface** - Beautiful GUI with real-time network monitoring
- **Live Telemetry Hub** - Animated traffic graphs, comprehensive metrics, status indicators
- **Complete Network Control** - Ethernet, WiFi, VPN, and Bluetooth management
- **Direct System Integration** - No NetworkManager dependencies, direct hardware control
- **Enterprise Grade** - Professional aesthetics suitable for corporate environments
- **User-Friendly Design** - Intuitive for everyday users, powerful for network professionals

## Architecture

- **alopex-qt/** - Professional PyQt6 GUI application
  - Real-time network discovery and monitoring
  - Beautiful animated telemetry interface
  - System tray integration
  - Professional visual design
- **network/** - Comprehensive network management core
  - Direct `/sys/class/net/` and `/proc/net/dev` integration
  - WireGuard VPN support
  - WiFi scanning and management
  - Bluetooth device control

## Installation & Deployment

### Quick Start
```bash
cd ~/projects/alopex/alopex-qt
python3 main.py
```

### Enterprise Deployment

**System Requirements:**
- Linux distribution with X11 or Wayland support
- Python 3.8+ with PyQt6
- Sudo privileges for network management
- System tray support for desktop integration

**Dependencies:**
```bash
# Core dependencies
pip install PyQt6

# System tools (install via package manager)
sudo pacman -S iw wireguard-tools bluez bluez-utils dhcpcd
# or
sudo apt install iw wireguard-tools bluez bluetooth dhcpcd5
```

**System Permissions:**
ALOPEX requires sudo access for network management. For enterprise deployment:

```bash
# Add ALOPEX sudo rules
echo '%alopex ALL=(ALL) NOPASSWD: /usr/bin/ip, /usr/bin/iw, /usr/bin/wg-quick, /usr/bin/dhcpcd, /usr/bin/bluetoothctl' | sudo tee /etc/sudoers.d/alopex

# Create alopex group and add users
sudo groupadd alopex
sudo usermod -a -G alopex $USER
```

**Desktop Integration:**
- System tray icon provides seamless network monitoring
- Application minimizes to tray instead of closing
- Professional notifications for connection status changes
- Right-click context menu for quick network actions

## Network Management

ALOPEX provides enterprise-grade network control:

- **Real-time Traffic Monitoring** - Live graphs with gradient fills and animations
- **Comprehensive Metrics** - Bytes, packets, errors, link speed, duplex, MTU
- **Interface Organization** - Grouped by type (Ethernet, WiFi, VPN) with visual indicators
- **Professional Status Display** - Animated connection indicators with glow effects
- **Advanced Configuration** - DHCP/static IP switching, DNS management

## Development Status

**Completed:**
- Network interface discovery and real-time monitoring
- Professional Qt interface with telemetry hub
- VPN management (WireGuard integration)
- WiFi scanning and connection control
- System integration for direct network control

**Completed:**
- Management panel with configuration cards
- System tray integration for enterprise deployment 
- Professional Qt interface with real-time telemetry

**In Progress:**
- Final testing and deployment preparation
- Bluetooth device management UI completion

---

**Onyx Digital Intelligence Development LLC**  
*Professional Network Security Solutions*
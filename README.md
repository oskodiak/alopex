# ALOPEX

**Revolutionary Network Manager for Linux**

ALOPEX is a fast, lightweight, and comprehensive network management TUI that replaces NetworkManager's complexity with elegant simplicity. Built by Onyx Digital Intelligence Development LLC for enterprise and consumer use.

## Features

- **Telemetry Hub** - Real-time network monitoring with live traffic graphs
- **Complete Interface Management** - Ethernet, WiFi, VPN, and Bluetooth devices
- **Zero Bloat** - Direct hardware control without daemon dependencies
- **Professional Design** - Conservative aesthetics suitable for enterprise environments
- **Mom-Friendly UX** - Intuitive enough for everyday users, powerful enough for network professionals

## Architecture

- `alopex-daemon` - Lightweight systemd service for hardware management
- `alopex-tui` - Terminal interface with comprehensive telemetry
- **JSON IPC** - Clean communication between components
- **Direct Integration** - Replaces NetworkManager, iwd, BlueZ management

## Installation

```bash
cd ~/projects/alopex/alopex-tui
cargo run
```

## Controls

- `↑/↓` - Navigate interfaces
- `Enter` - Connect/disconnect
- `Tab` - Switch panels  
- `r` - Refresh data
- `q` - Quit

## Network Statistics

ALOPEX provides comprehensive metrics:

- Real-time traffic rates (bytes + packets)
- Error detection and monitoring
- Link speed and duplex information
- Connection quality analysis
- Session uptime tracking

## Enterprise Ready

- Systemd integration
- Multi-user support
- Security-focused design
- Professional documentation
- Enterprise deployment ready

---

**Onyx Digital Intelligence Development LLC**  
*Professional Network Security Solutions*
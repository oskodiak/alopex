# ALOPEX

**Network Management System**

ALOPEX is a network management daemon that provides an alternative to NetworkManager with focus on direct system control and minimal overhead.

## Features

- **System Daemon** - Background network management service
- **PyQt6 GUI** - Desktop interface for network configuration
- **NetworkManager Compatibility** - nmcli compatibility layer for migration
- **Direct System Control** - Uses kernel netlink interfaces directly
- **JSON Configuration** - File-based connection profiles
- **Network Monitoring** - Interface and connection status tracking

## Architecture

```
src/
├── alopex-daemon/           # Core daemon
│   ├── alopexd.py                # Main network management daemon
│   ├── nmcli-compat.py           # NetworkManager CLI compatibility layer
│   ├── ebpf_monitor.c            # eBPF monitoring code (requires compilation)
│   ├── security.py               # Security controls
│   └── alopex-early-network.py   # Early boot networking support
├── alopex-qt/               # GUI application  
│   ├── main.py                   # GUI application entry point
│   ├── network/                  # Network management modules
│   │   ├── discovery.py          # Interface discovery and monitoring
│   │   ├── wifi.py               # WiFi management and scanning
│   │   ├── connection_manager.py # Connection management
│   │   ├── system_integration.py # System control
│   │   └── vpn.py                # VPN/WireGuard integration
│   └── ui/                       # User interface
│       ├── main_window.py        # Main application window
│       ├── telemetry_panel.py    # Network telemetry
│       ├── interface_panel.py    # Interface management
│       ├── management_panel.py   # Configuration management
│       └── system_tray.py        # Desktop integration
services/                    # systemd service definitions
configs/                     # Development configurations  
examples/                    # Configuration examples
docs/                        # Documentation
```

## Installation

### Quick Start
```bash
cd src/alopex-qt
python3 main.py
```

### System Installation

**System Requirements:**
- Linux with systemd
- Python 3.8+ with PyQt6
- Root privileges for network management

### Package Requirements by Distribution

#### NixOS
Add to your `configuration.nix`:
```nix
environment.systemPackages = with pkgs; [
  python3
  (python3.withPackages (ps: with ps; [ pyqt6 psutil ]))
  iw
  wireguard-tools
  dhcpcd
  # eBPF tools (optional, for advanced monitoring)
  bpftools
  libbpf
  llvmPackages.clang
  llvmPackages.llvm
];
```

#### Arch Linux / Manjaro / EndeavourOS
```bash
# Core dependencies
sudo pacman -S python python-pyqt6 python-psutil iw dhcpcd wireguard-tools systemd

# eBPF tools (optional)
sudo pacman -S bpf clang llvm libbpf

# AUR packages (if needed)
yay -S bpftool
```

#### Debian / Ubuntu / Linux Mint
```bash
# Update package list
sudo apt update

# Core dependencies
sudo apt install python3 python3-pyqt6 python3-psutil iw dhcpcd5 wireguard systemd

# eBPF tools (optional)
sudo apt install bpftools libbpf-dev clang llvm

# For older Ubuntu versions, install via pip
pip3 install --user PyQt6 psutil
```

#### Fedora / CentOS Stream / RHEL
```bash
# Core dependencies
sudo dnf install python3 python3-PyQt6 python3-psutil iw dhcpcd wireguard-tools systemd

# eBPF tools (optional)
sudo dnf install bpftool libbpf-devel clang llvm

# Enable development tools
sudo dnf groupinstall "Development Tools"
```

#### openSUSE
```bash
# Core dependencies
sudo zypper install python3 python3-qt6 python3-psutil iw dhcpcd wireguard-tools systemd

# eBPF tools (optional)
sudo zypper install bpftool libbpf-devel clang llvm
```

#### Alpine Linux
```bash
# Core dependencies
sudo apk add python3 py3-pyqt6 py3-psutil iw dhcpcd wireguard-tools

# eBPF tools (optional)
sudo apk add bpftool libbpf-dev clang llvm
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

## Key Features

- **NetworkManager Migration** - nmcli compatibility layer for existing scripts
- **JSON Configuration** - File-based connection profiles
- **Early Boot Networking** - Network setup during early boot phase
- **Network Monitoring** - Interface and connection status tracking
- **Desktop GUI** - PyQt6 interface for configuration management
- **systemd Integration** - Service-based daemon architecture

## Security Features

ALOPEX includes security controls and monitoring capabilities:

### Security Controls
- **Privilege Separation** - Daemon runs with minimal required capabilities
- **eBPF Monitoring** - Optional kernel-space monitoring (requires compilation)
- **Input Validation** - Network message validation and rate limiting
- **Audit Logging** - Security event logging

### Monitoring
- **Interface Monitoring** - Network interface status tracking
- **Connection Logging** - Network connection audit trail
- **System Integration** - Integration with systemd logging

**Note:** eBPF monitoring requires additional setup and compilation. See `docs/SECURITY-ARCHITECTURE.md` for implementation details.

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

**Core Features:**
- System daemon with systemd integration
- NetworkManager compatibility layer (nmcli replacement)
- PyQt6 GUI interface
- Connection state management
- WiFi scanning and management
- Early boot networking support

**In Development:**
- eBPF monitoring compilation and integration
- DBus interface for desktop integration  
- Distribution packaging
- Advanced security features

---

**ALOPEX Network Management System**
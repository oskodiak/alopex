# ALOPEX Documentation

## Architecture Overview

ALOPEX is an enterprise-grade NetworkManager replacement with:

- **Daemon**: Enterprise network management service (`alopexd`)
- **GUI**: Professional PyQt6 interface 
- **Compatibility**: Drop-in nmcli replacement for migration

## Directory Structure

```
src/
├── alopex-daemon/     # Core daemon and compatibility layer
├── alopex-qt/         # GUI application
services/              # systemd service files
configs/               # Build configurations  
examples/              # Configuration examples
docs/                  # Documentation
```

## Installation

See main README.md for installation instructions.
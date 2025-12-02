# ALOPEX Enterprise Network Management System
# Onyx Digital Intelligence Development LLC
# https://onyxdigital.dev

PREFIX ?= /usr
SYSCONFDIR ?= /etc
SYSTEMD_SYSTEM_DIR ?= /usr/lib/systemd/system
LOCALSTATEDIR ?= /var

# Enterprise deployment targets
.PHONY: install install-daemon install-gui install-enterprise clean uninstall test

all: install

# Full enterprise installation
install: install-daemon install-gui install-enterprise
	@echo "ALOPEX Enterprise Network Management installed successfully"
	@echo "Documentation: https://onyxdigital.dev/alopex"
	@echo "Support: enterprise@onyxdigital.dev"

# Install core daemon only (for server deployments)
install-daemon:
	@echo "Installing ALOPEX daemon..."
	
	# Install daemon executables
	install -D -m 755 alopex-daemon/alopexd.py $(DESTDIR)$(PREFIX)/bin/alopexd
	install -D -m 755 alopex-daemon/alopex-early-network.py $(DESTDIR)$(PREFIX)/bin/alopex-early-network
	
	# Install core network modules
	mkdir -p $(DESTDIR)$(PREFIX)/lib/alopex
	cp -r alopex-qt/network $(DESTDIR)$(PREFIX)/lib/alopex/
	
	# Install systemd services
	install -D -m 644 alopexd.service $(DESTDIR)$(SYSTEMD_SYSTEM_DIR)/alopexd.service
	install -D -m 644 alopex-early-network.service $(DESTDIR)$(SYSTEMD_SYSTEM_DIR)/alopex-early-network.service
	
	# Create configuration directories
	mkdir -p $(DESTDIR)$(SYSCONFDIR)/alopex
	mkdir -p $(DESTDIR)$(LOCALSTATEDIR)/lib/alopex
	mkdir -p $(DESTDIR)$(LOCALSTATEDIR)/log/alopex
	
	# Install default configurations
	install -D -m 644 enterprise-config-example.json $(DESTDIR)$(SYSCONFDIR)/alopex/enterprise.json.example
	install -D -m 644 critical-networks-example.json $(DESTDIR)$(SYSCONFDIR)/alopex/critical-networks.json.example
	
	@echo "Daemon installation complete. Enable with:"
	@echo "  systemctl enable --now alopex-early-network"
	@echo "  systemctl enable --now alopexd"

# Install GUI application (desktop environments)
install-gui:
	@echo "Installing ALOPEX GUI..."
	
	# Install GUI application
	mkdir -p $(DESTDIR)$(PREFIX)/lib/alopex/gui
	cp -r alopex-qt/* $(DESTDIR)$(PREFIX)/lib/alopex/gui/
	
	# Create GUI launcher script
	mkdir -p $(DESTDIR)$(PREFIX)/bin
	echo '#!/bin/bash' > $(DESTDIR)$(PREFIX)/bin/alopex-gui
	echo 'cd $(PREFIX)/lib/alopex/gui' >> $(DESTDIR)$(PREFIX)/bin/alopex-gui
	echo 'python3 main.py "$$@"' >> $(DESTDIR)$(PREFIX)/bin/alopex-gui
	chmod +x $(DESTDIR)$(PREFIX)/bin/alopex-gui
	
	# Install desktop entry
	mkdir -p $(DESTDIR)$(PREFIX)/share/applications
	echo '[Desktop Entry]' > $(DESTDIR)$(PREFIX)/share/applications/alopex.desktop
	echo 'Name=ALOPEX Network Manager' >> $(DESTDIR)$(PREFIX)/share/applications/alopex.desktop
	echo 'Comment=Enterprise Network Management' >> $(DESTDIR)$(PREFIX)/share/applications/alopex.desktop
	echo 'Exec=$(PREFIX)/bin/alopex-gui' >> $(DESTDIR)$(PREFIX)/share/applications/alopex.desktop
	echo 'Icon=network-manager' >> $(DESTDIR)$(PREFIX)/share/applications/alopex.desktop
	echo 'Terminal=false' >> $(DESTDIR)$(PREFIX)/share/applications/alopex.desktop
	echo 'Type=Application' >> $(DESTDIR)$(PREFIX)/share/applications/alopex.desktop
	echo 'Categories=Network;System;' >> $(DESTDIR)$(PREFIX)/share/applications/alopex.desktop

# Enterprise features installation
install-enterprise:
	@echo "Installing ALOPEX enterprise features..."
	
	# DBus policy for enterprise integration
	mkdir -p $(DESTDIR)$(PREFIX)/share/dbus-1/system.d
	echo '<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-BUS Bus Configuration 1.0//EN"' > $(DESTDIR)$(PREFIX)/share/dbus-1/system.d/org.alopex.NetworkManager.conf
	echo ' "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">' >> $(DESTDIR)$(PREFIX)/share/dbus-1/system.d/org.alopex.NetworkManager.conf
	echo '<busconfig>' >> $(DESTDIR)$(PREFIX)/share/dbus-1/system.d/org.alopex.NetworkManager.conf
	echo '  <policy user="root">' >> $(DESTDIR)$(PREFIX)/share/dbus-1/system.d/org.alopex.NetworkManager.conf
	echo '    <allow own="org.alopex.NetworkManager"/>' >> $(DESTDIR)$(PREFIX)/share/dbus-1/system.d/org.alopex.NetworkManager.conf
	echo '  </policy>' >> $(DESTDIR)$(PREFIX)/share/dbus-1/system.d/org.alopex.NetworkManager.conf
	echo '  <policy context="default">' >> $(DESTDIR)$(PREFIX)/share/dbus-1/system.d/org.alopex.NetworkManager.conf
	echo '    <allow send_destination="org.alopex.NetworkManager"/>' >> $(DESTDIR)$(PREFIX)/share/dbus-1/system.d/org.alopex.NetworkManager.conf
	echo '  </policy>' >> $(DESTDIR)$(PREFIX)/share/dbus-1/system.d/org.alopex.NetworkManager.conf
	echo '</busconfig>' >> $(DESTDIR)$(PREFIX)/share/dbus-1/system.d/org.alopex.NetworkManager.conf
	
	# NetworkManager compatibility shims
	mkdir -p $(DESTDIR)$(PREFIX)/bin/compat
	echo '#!/bin/bash' > $(DESTDIR)$(PREFIX)/bin/compat/nmcli
	echo '# ALOPEX NetworkManager compatibility shim' >> $(DESTDIR)$(PREFIX)/bin/compat/nmcli
	echo 'echo "ALOPEX NetworkManager Compatibility Layer"' >> $(DESTDIR)$(PREFIX)/bin/compat/nmcli
	echo 'echo "Contact enterprise@onyxdigital.dev for migration support"' >> $(DESTDIR)$(PREFIX)/bin/compat/nmcli
	chmod +x $(DESTDIR)$(PREFIX)/bin/compat/nmcli
	
	@echo "Enterprise features installed"
	@echo "For enterprise support: enterprise@onyxdigital.dev"

# Development shell environment
shell.nix:
	@echo "Updating development environment..."
	@echo '{ pkgs ? import <nixpkgs> {} }:' > shell.nix
	@echo '' >> shell.nix
	@echo 'pkgs.mkShell {' >> shell.nix
	@echo '  buildInputs = with pkgs; [' >> shell.nix
	@echo '    python312' >> shell.nix
	@echo '    python312Packages.pyqt6' >> shell.nix
	@echo '    python312Packages.dbus-python' >> shell.nix
	@echo '    systemd' >> shell.nix
	@echo '    iproute2' >> shell.nix
	@echo '    wireless-tools' >> shell.nix
	@echo '    wpa_supplicant' >> shell.nix
	@echo '    dhcpcd' >> shell.nix
	@echo '  ];' >> shell.nix
	@echo '  ' >> shell.nix
	@echo '  shellHook = '\'''\'' >> shell.nix
	@echo '    echo "ALOPEX Development Environment"' >> shell.nix
	@echo '    echo "Enterprise Network Management System"' >> shell.nix
	@echo '    echo "Onyx Digital Intelligence Development LLC"' >> shell.nix
	@echo '    echo "https://onyxdigital.dev/alopex"' >> shell.nix
	@echo '    cd alopex-qt' >> shell.nix
	@echo '  '\'''\';' >> shell.nix
	@echo '}' >> shell.nix

# Test installation
test:
	@echo "Testing ALOPEX installation..."
	python3 -c "import sys; sys.path.append('alopex-qt'); from network.discovery import NetworkDiscovery; d = NetworkDiscovery(); print(f'Found {len(d.discover_interfaces())} interfaces')"
	@echo "Basic functionality test passed"

# Uninstall everything
uninstall:
	@echo "Uninstalling ALOPEX..."
	systemctl disable alopexd || true
	systemctl disable alopex-early-network || true
	rm -f $(SYSTEMD_SYSTEM_DIR)/alopexd.service
	rm -f $(SYSTEMD_SYSTEM_DIR)/alopex-early-network.service
	rm -f $(PREFIX)/bin/alopexd
	rm -f $(PREFIX)/bin/alopex-early-network
	rm -f $(PREFIX)/bin/alopex-gui
	rm -f $(PREFIX)/bin/compat/nmcli
	rm -rf $(PREFIX)/lib/alopex
	rm -f $(PREFIX)/share/applications/alopex.desktop
	rm -f $(PREFIX)/share/dbus-1/system.d/org.alopex.NetworkManager.conf
	@echo "ALOPEX uninstalled"

# Clean build artifacts
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -f shell.nix

# Enterprise deployment helpers
deploy-enterprise:
	@echo "Deploying ALOPEX for enterprise environment..."
	@echo "See https://onyxdigital.dev/alopex/enterprise for deployment guide"

# Package for distribution
package:
	@echo "Creating distribution packages..."
	@echo "Contact enterprise@onyxdigital.dev for packaging support"
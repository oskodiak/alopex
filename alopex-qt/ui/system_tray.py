"""
ALOPEX System Tray - Professional enterprise integration
Seamless desktop integration with network status monitoring
"""

from PyQt6.QtWidgets import (QSystemTrayIcon, QMenu, QApplication, 
                            QWidget, QVBoxLayout, QHBoxLayout, QLabel)
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor, QAction
import asyncio
from typing import Optional
from network.discovery import NetworkDiscovery

class AlopexSystemTray(QSystemTrayIcon):
    """Professional system tray integration for ALOPEX"""
    
    # Signals
    show_main_window = pyqtSignal()
    quit_application = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.discovery = NetworkDiscovery()
        self.network_status = "disconnected"
        self.active_connections = 0
        
        self._setup_tray_icon()
        self._setup_context_menu()
        self._setup_update_timer()
        
        # Connect signals
        self.activated.connect(self._on_tray_activated)
        
    def _setup_tray_icon(self):
        """Create dynamic tray icon based on network status"""
        self._update_tray_icon()
        self.setToolTip("ALOPEX Network Manager")
        
    def _setup_context_menu(self):
        """Create professional context menu"""
        self.menu = QMenu()
        
        # Network status section
        self.status_action = QAction("Network Status: Checking...", self.menu)
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)
        
        self.menu.addSeparator()
        
        # Quick actions
        self.show_action = QAction("Show ALOPEX", self.menu)
        self.show_action.triggered.connect(self.show_main_window.emit)
        self.menu.addAction(self.show_action)
        
        self.telemetry_action = QAction("Network Telemetry", self.menu)
        self.telemetry_action.triggered.connect(lambda: self._show_quick_telemetry())
        self.menu.addAction(self.telemetry_action)
        
        self.menu.addSeparator()
        
        # Network controls
        self.wifi_submenu = self.menu.addMenu("WiFi Control")
        self.ethernet_submenu = self.menu.addMenu("Ethernet Control") 
        self.vpn_submenu = self.menu.addMenu("VPN Control")
        
        self._populate_network_controls()
        
        self.menu.addSeparator()
        
        # Application controls
        self.quit_action = QAction("Quit ALOPEX", self.menu)
        self.quit_action.triggered.connect(self.quit_application.emit)
        self.menu.addAction(self.quit_action)
        
        self.setContextMenu(self.menu)
    
    def _setup_update_timer(self):
        """Setup timer for real-time status updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_network_status)
        self.update_timer.start(2000)  # Update every 2 seconds
    
    def _update_tray_icon(self):
        """Create dynamic icon based on network status"""
        # Create 16x16 icon with status indicator
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Base network icon (simplified router/network symbol)
        if self.network_status == "connected":
            painter.setBrush(QBrush(QColor(64, 224, 128)))  # Professional green
        elif self.network_status == "limited":
            painter.setBrush(QBrush(QColor(255, 165, 0)))   # Professional orange
        else:
            painter.setBrush(QBrush(QColor(169, 169, 169))) # Professional gray
        
        # Draw network symbol
        painter.drawRect(2, 6, 4, 4)   # Base box
        painter.drawRect(6, 4, 4, 8)   # Tower
        painter.drawRect(10, 2, 4, 12) # Antenna
        
        painter.end()
        
        icon = QIcon(pixmap)
        self.setIcon(icon)
    
    def _update_network_status(self):
        """Update network status and tray display"""
        try:
            interfaces = self.discovery.discover_interfaces()
            
            # Count active connections
            active_count = 0
            has_internet = False
            
            for interface in interfaces:
                if interface.status == "Connected" and interface.metrics.bytes_rx > 0:
                    active_count += 1
                    if interface.interface_type in ['ethernet', 'wifi']:
                        has_internet = True
            
            self.active_connections = active_count
            
            # Determine overall status
            if has_internet and active_count > 0:
                self.network_status = "connected"
                status_text = f"Connected - {active_count} active interface(s)"
            elif active_count > 0:
                self.network_status = "limited"
                status_text = f"Limited - {active_count} interface(s) up"
            else:
                self.network_status = "disconnected"
                status_text = "Disconnected - No active connections"
            
            # Update UI
            self.status_action.setText(f"Status: {status_text}")
            self._update_tray_icon()
            
            # Update tooltip with detailed info
            tooltip = f"ALOPEX Network Manager\n{status_text}"
            if active_count > 0:
                tooltip += f"\nActive interfaces: {active_count}"
            self.setToolTip(tooltip)
            
        except Exception as e:
            self.status_action.setText("Status: Error reading network")
            self.setToolTip("ALOPEX Network Manager - Error")
    
    def _populate_network_controls(self):
        """Populate network control submenus"""
        # WiFi controls
        self.wifi_submenu.clear()
        wifi_enable = QAction("Enable WiFi", self.wifi_submenu)
        wifi_disable = QAction("Disable WiFi", self.wifi_submenu)
        wifi_scan = QAction("Scan Networks", self.wifi_submenu)
        
        self.wifi_submenu.addAction(wifi_enable)
        self.wifi_submenu.addAction(wifi_disable)
        self.wifi_submenu.addAction(wifi_scan)
        
        # Ethernet controls  
        self.ethernet_submenu.clear()
        eth_dhcp = QAction("Configure DHCP", self.ethernet_submenu)
        eth_static = QAction("Configure Static IP", self.ethernet_submenu)
        
        self.ethernet_submenu.addAction(eth_dhcp)
        self.ethernet_submenu.addAction(eth_static)
        
        # VPN controls
        self.vpn_submenu.clear()
        vpn_connect = QAction("Connect VPN", self.vpn_submenu)
        vpn_disconnect = QAction("Disconnect VPN", self.vpn_submenu)
        vpn_status = QAction("VPN Status", self.vpn_submenu)
        
        self.vpn_submenu.addAction(vpn_connect)
        self.vpn_submenu.addAction(vpn_disconnect) 
        self.vpn_submenu.addAction(vpn_status)
    
    def _on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Single click - show main window
            self.show_main_window.emit()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # Double click - show telemetry
            self._show_quick_telemetry()
    
    def _show_quick_telemetry(self):
        """Show quick telemetry popup"""
        # For now, just show main window
        # TODO: Implement quick telemetry popup
        self.show_main_window.emit()
    
    def show_notification(self, title: str, message: str, icon_type=None):
        """Show system notification"""
        if icon_type is None:
            icon_type = QSystemTrayIcon.MessageIcon.Information
            
        self.showMessage(title, message, icon_type, 3000)
    
    def update_vpn_status(self, connected: bool, server: str = ""):
        """Update VPN status in tray"""
        if connected:
            self.show_notification(
                "VPN Connected", 
                f"Connected to {server}" if server else "VPN connection established"
            )
        else:
            self.show_notification(
                "VPN Disconnected",
                "VPN connection terminated"
            )
    
    def update_wifi_status(self, connected: bool, ssid: str = ""):
        """Update WiFi status in tray"""
        if connected:
            self.show_notification(
                "WiFi Connected",
                f"Connected to {ssid}" if ssid else "WiFi connection established"
            )
        else:
            self.show_notification(
                "WiFi Disconnected", 
                "WiFi connection lost"
            )
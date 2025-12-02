"""
ALOPEX Main Window - Professional Qt GUI
Beautiful network management interface with telemetry hub
"""

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QSystemTrayIcon, QMenu, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QAction

from .interface_panel import InterfacePanel
from .management_panel import ManagementPanel  
from .telemetry_panel import TelemetryPanel
from .system_tray import AlopexSystemTray
from network.discovery import NetworkDiscovery

class AlopexMainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.network_discovery = NetworkDiscovery()
        self.selected_interface = None
        
        self.setup_ui()
        self.setup_timers()
        self.setup_system_tray()
        self.refresh_interfaces()
        
    def setup_ui(self):
        """Setup the main UI layout"""
        self.setWindowTitle("ALOPEX Network Manager")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget with splitter layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create panels
        self.interface_panel = InterfacePanel()
        self.management_panel = ManagementPanel()
        self.telemetry_panel = TelemetryPanel()
        
        # Add panels to splitter
        splitter.addWidget(self.interface_panel)
        splitter.addWidget(self.management_panel)
        splitter.addWidget(self.telemetry_panel)
        
        # Set splitter proportions (25%, 40%, 35%)
        splitter.setSizes([300, 480, 420])
        
        # Connect signals
        self.interface_panel.interface_selected.connect(self.on_interface_selected)
        
        # Setup status bar
        self.statusBar().showMessage("ALOPEX Network Manager - Ready")
        
    def setup_timers(self):
        """Setup update timers"""
        # Interface refresh timer (every 5 seconds)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_interfaces)
        self.refresh_timer.start(5000)
        
        # Telemetry update timer (every 1 second)
        self.telemetry_timer = QTimer()
        self.telemetry_timer.timeout.connect(self.update_telemetry)
        self.telemetry_timer.start(1000)
        
    def setup_system_tray(self):
        """Setup system tray integration"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.system_tray = AlopexSystemTray(self)
            
            # Connect system tray signals
            self.system_tray.show_main_window.connect(self.show_and_raise)
            self.system_tray.quit_application.connect(self.quit_application)
            
            self.system_tray.show()
        else:
            self.statusBar().showMessage("System tray not available")
    
    def show_and_raise(self):
        """Show and raise main window"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def quit_application(self):
        """Quit the application completely"""
        if hasattr(self, 'system_tray'):
            self.system_tray.hide()
        QApplication.instance().quit()
    
    def refresh_interfaces(self):
        """Refresh network interface list"""
        try:
            interfaces = NetworkDiscovery.discover_interfaces()
            self.interface_panel.update_interfaces(interfaces)
            
            # Update telemetry if we have a selected interface
            if self.selected_interface:
                # Find updated version of selected interface
                updated_interface = next(
                    (i for i in interfaces if i.name == self.selected_interface.name), 
                    None
                )
                if updated_interface:
                    self.selected_interface = updated_interface
                    self.management_panel.update_interface(updated_interface)
                    
        except Exception as e:
            self.statusBar().showMessage(f"Error refreshing interfaces: {e}")
    
    def update_telemetry(self):
        """Update telemetry data"""
        if not self.selected_interface:
            return
            
        try:
            # Get fresh data for selected interface
            interfaces = NetworkDiscovery.discover_interfaces()
            updated_interface = next(
                (i for i in interfaces if i.name == self.selected_interface.name),
                None
            )
            
            if updated_interface:
                # Update speed calculations
                self.network_discovery.update_speeds([updated_interface])
                
                # Update telemetry panel
                self.telemetry_panel.update_metrics(updated_interface.metrics)
                self.selected_interface = updated_interface
                
        except Exception as e:
            print(f"Error updating telemetry: {e}")
    
    def on_interface_selected(self, interface):
        """Handle interface selection"""
        self.selected_interface = interface
        self.management_panel.update_interface(interface)
        self.telemetry_panel.set_active(interface.status == "Connected")
        
        if interface.status == "Connected":
            self.telemetry_panel.update_metrics(interface.metrics)
        
        self.statusBar().showMessage(f"Selected: {interface.name} ({interface.status})")
    
    def closeEvent(self, event):
        """Handle window close event"""
        if hasattr(self, 'system_tray') and self.system_tray.isVisible():
            # Hide to system tray instead of closing
            self.hide()
            self.system_tray.showMessage(
                "ALOPEX Network Manager",
                "Application minimized to system tray",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            event.ignore()
        else:
            event.accept()
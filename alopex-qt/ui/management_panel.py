"""
Management Panel - Network interface configuration and control
Professional interface management that NetworkManager wishes it had
"""

import asyncio
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QGroupBox, QFormLayout, QLineEdit, QComboBox, QCheckBox, QSpacerItem,
    QSizePolicy, QTextEdit, QTabWidget, QListWidget, QListWidgetItem,
    QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor

from network.discovery import NetworkInterface
from network.system_integration import NetworkControl, BluetoothControl
from network.wifi import WiFiManager, WiFiNetwork
from network.vpn import VpnManager, VpnConfig

class AsyncWorker(QThread):
    """Background worker for async operations"""
    finished = pyqtSignal(bool, str)
    
    def __init__(self, coro_func, *args, **kwargs):
        super().__init__()
        self.coro_func = coro_func
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.coro_func(*self.args, **self.kwargs))
            self.finished.emit(True, str(result))
        except Exception as e:
            self.finished.emit(False, str(e))
        finally:
            loop.close()

class ConfigurationCard(QFrame):
    """Beautiful configuration card for interface settings"""
    
    def __init__(self, title, icon_color=QColor(52, 152, 219)):
        super().__init__()
        self.title = title
        self.icon_color = icon_color
        self.setup_ui()
        
    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            ConfigurationCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34495e, stop:1 #2c3e50);
                border: 1px solid #4a6473;
                border-radius: 12px;
                padding: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            color: #3498db;
            font-size: 12pt;
            font-weight: bold;
            margin-bottom: 8px;
        """)
        layout.addWidget(title_label)
        
        # Content layout for subclasses
        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout)

class EthernetConfigCard(ConfigurationCard):
    """Ethernet interface configuration"""
    
    config_changed = pyqtSignal()
    
    def __init__(self, interface: NetworkInterface):
        super().__init__("Ethernet Configuration")
        self.interface = interface
        self.setup_ethernet_controls()
        
    def setup_ethernet_controls(self):
        form = QFormLayout()
        form.setSpacing(8)
        
        # DHCP/Static toggle
        self.dhcp_checkbox = QCheckBox("Use DHCP")
        self.dhcp_checkbox.setChecked(True)  # Default to DHCP
        self.dhcp_checkbox.stateChanged.connect(self.on_dhcp_toggled)
        form.addRow("Network Config:", self.dhcp_checkbox)
        
        # Static IP fields (initially disabled)
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("192.168.1.100")
        self.ip_input.setEnabled(False)
        form.addRow("IP Address:", self.ip_input)
        
        self.gateway_input = QLineEdit()
        self.gateway_input.setPlaceholderText("192.168.1.1")
        self.gateway_input.setEnabled(False)
        form.addRow("Gateway:", self.gateway_input)
        
        self.dns_input = QLineEdit()
        self.dns_input.setPlaceholderText("8.8.8.8, 1.1.1.1")
        self.dns_input.setEnabled(False)
        form.addRow("DNS Servers:", self.dns_input)
        
        # Style form inputs
        for i in range(form.count()):
            widget = form.itemAt(i).widget()
            if isinstance(widget, (QLineEdit, QCheckBox)):
                widget.setStyleSheet("""
                    QLineEdit {
                        background: #2c3e50;
                        color: #ecf0f1;
                        border: 1px solid #34495e;
                        border-radius: 6px;
                        padding: 8px;
                        font-size: 10pt;
                    }
                    QLineEdit:focus {
                        border: 1px solid #3498db;
                    }
                    QLineEdit:disabled {
                        background: #1a252f;
                        color: #7f8c8d;
                    }
                    QCheckBox {
                        color: #ecf0f1;
                        font-size: 10pt;
                    }
                    QCheckBox::indicator {
                        width: 16px;
                        height: 16px;
                    }
                    QCheckBox::indicator:unchecked {
                        background: #2c3e50;
                        border: 1px solid #34495e;
                        border-radius: 3px;
                    }
                    QCheckBox::indicator:checked {
                        background: #3498db;
                        border: 1px solid #2980b9;
                        border-radius: 3px;
                    }
                """)
        
        self.content_layout.addLayout(form)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        self.apply_button = QPushButton("Apply Configuration")
        self.apply_button.clicked.connect(self.apply_configuration)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_configuration)
        
        # Style buttons
        for button in [self.apply_button, self.reset_button]:
            button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #3498db, stop:1 #2980b9);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-weight: bold;
                    font-size: 10pt;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #2ecc71, stop:1 #27ae60);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #2980b9, stop:1 #21618c);
                }
            """)
        
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        
        self.content_layout.addLayout(button_layout)
        
    def on_dhcp_toggled(self, checked):
        """Enable/disable static IP fields based on DHCP setting"""
        enabled = not checked
        self.ip_input.setEnabled(enabled)
        self.gateway_input.setEnabled(enabled)
        self.dns_input.setEnabled(enabled)
        
    def apply_configuration(self):
        """Apply network configuration"""
        if self.dhcp_checkbox.isChecked():
            # Configure DHCP
            worker = AsyncWorker(NetworkControl.configure_dhcp, self.interface.name)
        else:
            # Configure static IP
            ip = self.ip_input.text().strip()
            gateway = self.gateway_input.text().strip()
            dns = [d.strip() for d in self.dns_input.text().split(',') if d.strip()]
            
            if not ip:
                QMessageBox.warning(self, "Invalid Configuration", "IP address is required for static configuration")
                return
                
            worker = AsyncWorker(NetworkControl.configure_static_ip, 
                                self.interface.name, ip, gateway, dns)
        
        worker.finished.connect(self.on_configuration_complete)
        worker.start()
        
        # Disable button during operation
        self.apply_button.setText("Applying...")
        self.apply_button.setEnabled(False)
        
    def on_configuration_complete(self, success, message):
        """Handle configuration completion"""
        self.apply_button.setText("Apply Configuration")
        self.apply_button.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Configuration Applied", "Network configuration updated successfully")
        else:
            QMessageBox.critical(self, "Configuration Failed", f"Failed to apply configuration: {message}")
        
        self.config_changed.emit()
        
    def reset_configuration(self):
        """Reset to current interface configuration"""
        self.dhcp_checkbox.setChecked(True)
        self.ip_input.clear()
        self.gateway_input.clear()
        self.dns_input.clear()

class WiFiConfigCard(ConfigurationCard):
    """WiFi interface configuration with network scanning"""
    
    def __init__(self, interface: NetworkInterface):
        super().__init__("WiFi Configuration")
        self.interface = interface
        self.networks = []
        self.setup_wifi_controls()
        self.refresh_networks()
        
    def setup_wifi_controls(self):
        # Network list
        self.network_list = QListWidget()
        self.network_list.setStyleSheet("""
            QListWidget {
                background: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 6px;
                font-size: 10pt;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #34495e;
            }
            QListWidget::item:selected {
                background: #3498db;
            }
            QListWidget::item:hover {
                background: #4a6473;
            }
        """)
        self.network_list.setMinimumHeight(150)
        
        self.content_layout.addWidget(QLabel("Available Networks:"))
        self.content_layout.addWidget(self.network_list)
        
        # Connection controls
        connection_layout = QHBoxLayout()
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Network password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.connect_button = QPushButton("Connect")
        self.refresh_button = QPushButton("Scan")
        
        # Style controls
        for widget in [self.password_input, self.connect_button, self.refresh_button]:
            widget.setStyleSheet("""
                QLineEdit {
                    background: #2c3e50;
                    color: #ecf0f1;
                    border: 1px solid #34495e;
                    border-radius: 6px;
                    padding: 8px;
                    font-size: 10pt;
                }
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #3498db, stop:1 #2980b9);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                    font-size: 10pt;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #2ecc71, stop:1 #27ae60);
                }
            """)
        
        connection_layout.addWidget(self.password_input, 2)
        connection_layout.addWidget(self.connect_button, 1)
        connection_layout.addWidget(self.refresh_button, 1)
        
        self.content_layout.addLayout(connection_layout)
        
        # Connect signals
        self.connect_button.clicked.connect(self.connect_to_network)
        self.refresh_button.clicked.connect(self.refresh_networks)
        
    def refresh_networks(self):
        """Scan for WiFi networks"""
        self.refresh_button.setText("Scanning...")
        self.refresh_button.setEnabled(False)
        
        # Simulate scan (real implementation would use WiFiManager)
        QTimer.singleShot(2000, self.on_scan_complete)
        
    def on_scan_complete(self):
        """Handle scan completion"""
        self.refresh_button.setText("Scan")
        self.refresh_button.setEnabled(True)
        
        # Mock networks for demo
        self.networks = [
            WiFiNetwork("HomeNetwork", -45, "WPA3", "5GHz"),
            WiFiNetwork("OfficeWiFi", -55, "WPA2", "2.4GHz"),
            WiFiNetwork("PublicHotspot", -70, "Open", "2.4GHz")
        ]
        
        self.update_network_list()
        
    def update_network_list(self):
        """Update the network list display"""
        self.network_list.clear()
        
        for network in self.networks:
            signal_strength = "Strong" if network.signal_strength > -50 else "Medium" if network.signal_strength > -70 else "Weak"
            security_icon = "🔒" if network.security != "Open" else "🔓"
            
            item_text = f"{security_icon} {network.ssid} ({signal_strength}, {network.frequency}, {network.security})"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, network)
            self.network_list.addItem(item)
            
    def connect_to_network(self):
        """Connect to selected WiFi network"""
        current_item = self.network_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a network to connect to")
            return
            
        network = current_item.data(Qt.ItemDataRole.UserRole)
        password = self.password_input.text()
        
        if network.security != "Open" and not password:
            QMessageBox.warning(self, "Password Required", "This network requires a password")
            return
            
        # TODO: Implement actual WiFi connection
        self.connect_button.setText("Connecting...")
        self.connect_button.setEnabled(False)
        
        QTimer.singleShot(3000, lambda: self.on_connection_complete(True, "Connected successfully"))
        
    def on_connection_complete(self, success, message):
        """Handle connection completion"""
        self.connect_button.setText("Connect")
        self.connect_button.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Connection Successful", message)
            self.password_input.clear()
        else:
            QMessageBox.critical(self, "Connection Failed", message)

class ManagementPanel(QWidget):
    """Professional network interface management panel"""
    
    def __init__(self):
        super().__init__()
        self.current_interface = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Panel header
        header = QLabel("Network Management")
        header.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34495e, stop:1 #2c3e50);
                color: #ecf0f1;
                font-size: 14pt;
                font-weight: bold;
                padding: 16px;
                border-bottom: 2px solid #f39c12;
            }
        """)
        layout.addWidget(header)
        
        # Content area
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("""
            QWidget {
                background: #2c3e50;
            }
        """)
        
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.content_layout.setSpacing(12)
        
        # Placeholder
        self.placeholder_label = QLabel("Select a network interface to manage")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_label.setStyleSheet("""
            color: #7f8c8d;
            font-size: 12pt;
            padding: 40px;
        """)
        self.content_layout.addWidget(self.placeholder_label)
        self.content_layout.addStretch()
        
        layout.addWidget(self.content_widget)
        
    def update_interface(self, interface: NetworkInterface):
        """Update panel for selected interface"""
        self.current_interface = interface
        
        # Clear existing content
        while self.content_layout.count() > 0:
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
        
        # Add interface-specific management
        if interface.interface_type == "Ethernet":
            config_card = EthernetConfigCard(interface)
            config_card.config_changed.connect(self.on_config_changed)
            self.content_layout.addWidget(config_card)
            
        elif interface.interface_type == "WiFi":
            config_card = WiFiConfigCard(interface)
            self.content_layout.addWidget(config_card)
            
        else:
            # Generic interface info
            info_label = QLabel(f"Interface: {interface.name}\nType: {interface.interface_type}\nStatus: {interface.status}")
            info_label.setStyleSheet("""
                color: #ecf0f1;
                font-size: 11pt;
                padding: 20px;
                background: #34495e;
                border-radius: 8px;
            """)
            self.content_layout.addWidget(info_label)
        
        self.content_layout.addStretch()
        
    def on_config_changed(self):
        """Handle configuration changes"""
        # Emit signal to refresh interface data
        pass
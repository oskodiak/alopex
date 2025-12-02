"""
Interface Panel - Beautiful interface selection with visual indicators
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QLabel, QFrame, QPushButton, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPalette, QBrush, QColor, QPainter, QPen

from network.discovery import NetworkInterface
from .arctic_theme import ArcticTheme, FontManager

class InterfaceStatusIndicator(QWidget):
    """Beautiful animated status indicator"""
    
    def __init__(self, status="Disconnected"):
        super().__init__()
        self.status = status
        self.setFixedSize(16, 16)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Arctic Terminal status colors
        colors = {
            "Connected": QColor(ArcticTheme.SUCCESS),      # Arctic green
            "Connecting": QColor(ArcticTheme.PRIMARY_ACCENT), # Arctic blue  
            "Disconnected": QColor(ArcticTheme.TEXT_MUTED)    # Arctic gray
        }
        
        color = colors.get(self.status, colors["Disconnected"])
        
        # Draw glowing circle
        painter.setPen(QPen(color.lighter(150), 1))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(2, 2, 12, 12)
        
        # Add inner glow for connected state
        if self.status == "Connected":
            painter.setPen(QPen(color.lighter(200), 0.5))
            painter.drawEllipse(4, 4, 8, 8)

class InterfaceTypeIcon(QWidget):
    """Interface type icon widget"""
    
    def __init__(self, interface_type="Unknown"):
        super().__init__()
        self.interface_type = interface_type
        self.setFixedSize(24, 24)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Icon colors
        color = QColor(108, 122, 137)  # Neutral gray
        
        painter.setPen(QPen(color, 2))
        
        # Draw different icons based on type
        if self.interface_type == "Ethernet":
            # Ethernet port icon
            painter.drawRect(4, 8, 16, 8)
            painter.drawLine(6, 10, 18, 10)
            painter.drawLine(6, 14, 18, 14)
            
        elif self.interface_type == "WiFi":
            # WiFi signal icon  
            painter.drawArc(8, 8, 8, 8, 0, 180 * 16)
            painter.drawArc(6, 6, 12, 12, 0, 180 * 16)
            painter.drawArc(4, 4, 16, 16, 0, 180 * 16)
            painter.fillRect(11, 15, 2, 2, color)
            
        elif self.interface_type == "VPN":
            # VPN shield icon
            painter.drawPath(self._get_shield_path())
            
        else:
            # Unknown - question mark
            font = painter.font()
            font.setPointSize(12)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "?")
    
    def _get_shield_path(self):
        from PyQt6.QtGui import QPainterPath
        path = QPainterPath()
        path.moveTo(12, 4)
        path.lineTo(20, 8)
        path.lineTo(20, 16)
        path.lineTo(12, 20)
        path.lineTo(4, 16)
        path.lineTo(4, 8)
        path.closeSubpath()
        return path

class InterfaceListItem(QWidget):
    """Custom beautiful interface list item"""
    
    clicked = pyqtSignal(NetworkInterface)
    
    def __init__(self, interface: NetworkInterface):
        super().__init__()
        self.interface = interface
        self.selected = False
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Status indicator
        self.status_indicator = InterfaceStatusIndicator(self.interface.status)
        layout.addWidget(self.status_indicator)
        
        # Interface type icon
        type_icon = InterfaceTypeIcon(self.interface.interface_type)
        layout.addWidget(type_icon)
        
        # Interface info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # Interface name
        name_label = QLabel(self.interface.name)
        name_label.setFont(FontManager.get_primary_font(11, 600))
        name_label.setStyleSheet(f"color: {ArcticTheme.TEXT_PRIMARY};")
        
        # Interface details
        details = []
        if self.interface.ip:
            details.append(self.interface.ip)
        if self.interface.metrics.link_speed:
            details.append(f"{self.interface.metrics.link_speed}Mbps")
            
        detail_text = " • ".join(details) if details else self.interface.interface_type
        detail_label = QLabel(detail_text)
        detail_label.setFont(FontManager.get_primary_font(9))
        detail_label.setStyleSheet(f"color: {ArcticTheme.TEXT_SECONDARY};")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(detail_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Speed indicator for active connections
        if self.interface.status == "Connected":
            speed_layout = QVBoxLayout()
            speed_layout.setSpacing(1)
            
            up_label = QLabel(f"↑ {self.interface.metrics.speed_up:.1f}K")
            up_label.setFont(FontManager.get_primary_font(8, 600))
            up_label.setStyleSheet(f"color: {ArcticTheme.SUCCESS};")
            up_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            down_label = QLabel(f"↓ {self.interface.metrics.speed_down:.1f}K")  
            down_label.setFont(FontManager.get_primary_font(8, 600))
            down_label.setStyleSheet(f"color: {ArcticTheme.PRIMARY_ACCENT};")
            down_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            speed_layout.addWidget(up_label)
            speed_layout.addWidget(down_label)
            layout.addLayout(speed_layout)
        
        self.setFixedHeight(64)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.interface)
            
    def set_selected(self, selected: bool):
        self.selected = selected
        self.update_style()
        
    def update_style(self):
        if self.selected:
            self.setStyleSheet(f"""
                InterfaceListItem {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {ArcticTheme.PRIMARY_ACCENT}, stop:1 #2E7DD2);
                    border-radius: 8px;
                    border: 1px solid {ArcticTheme.PRIMARY_ACCENT};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                InterfaceListItem:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {ArcticTheme.SURFACE_HOVER}, stop:1 {ArcticTheme.BACKGROUND_ELEVATED});
                    border-radius: 8px;
                }}
            """)

class InterfaceTypeHeader(QWidget):
    """Beautiful type section header"""
    
    def __init__(self, interface_type: str):
        super().__init__()
        self.interface_type = interface_type
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 8)
        
        # Left line
        left_line = QFrame()
        left_line.setFrameShape(QFrame.Shape.HLine)
        left_line.setStyleSheet("background: #34495e;")
        left_line.setFixedHeight(1)
        
        # Type label
        label = QLabel(self.interface_type.upper())
        label.setStyleSheet("""
            color: #3498db;
            font-weight: bold;
            font-size: 10pt;
            padding: 0 12px;
        """)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Right line  
        right_line = QFrame()
        right_line.setFrameShape(QFrame.Shape.HLine)
        right_line.setStyleSheet("background: #34495e;")
        right_line.setFixedHeight(1)
        
        layout.addWidget(left_line, 1)
        layout.addWidget(label, 0)
        layout.addWidget(right_line, 1)

class InterfacePanel(QWidget):
    """Beautiful interface selection panel"""
    
    interface_selected = pyqtSignal(NetworkInterface)
    
    def __init__(self):
        super().__init__()
        self.interfaces = []
        self.selected_item = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Panel header
        header = QLabel("Network Interfaces")
        header.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34495e, stop:1 #2c3e50);
                color: #ecf0f1;
                font-size: 14pt;
                font-weight: bold;
                padding: 16px;
                border-bottom: 2px solid #3498db;
            }
        """)
        layout.addWidget(header)
        
        # Scrollable interface list
        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #2c3e50;
            }
            QScrollBar:vertical {
                background: #34495e;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #3498db;
                border-radius: 6px;
                min-height: 20px;
            }
        """)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 8, 0, 8)
        self.content_layout.setSpacing(4)
        
        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)
        
        # Panel styling
        self.setStyleSheet("""
            InterfacePanel {
                background: #2c3e50;
                border-right: 1px solid #34495e;
            }
        """)
        
    def update_interfaces(self, interfaces):
        """Update interface list with beautiful organization"""
        # Clear existing items
        for i in reversed(range(self.content_layout.count())):
            self.content_layout.itemAt(i).widget().setParent(None)
            
        self.interfaces = interfaces
        
        # Group by interface type
        grouped = {}
        for interface in interfaces:
            interface_type = interface.interface_type
            if interface_type not in grouped:
                grouped[interface_type] = []
            grouped[interface_type].append(interface)
        
        # Add interfaces grouped by type
        for interface_type in ["Ethernet", "WiFi", "VPN", "Unknown"]:
            if interface_type in grouped:
                # Add type header
                header = InterfaceTypeHeader(interface_type)
                self.content_layout.addWidget(header)
                
                # Add interfaces of this type
                for interface in grouped[interface_type]:
                    item = InterfaceListItem(interface)
                    item.clicked.connect(self.on_interface_clicked)
                    self.content_layout.addWidget(item)
        
        # Add stretch at bottom
        self.content_layout.addStretch()
        
    def on_interface_clicked(self, interface):
        """Handle interface selection"""
        # Update visual selection
        for i in range(self.content_layout.count()):
            item = self.content_layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None and isinstance(widget, InterfaceListItem):
                    widget.set_selected(widget.interface.name == interface.name)
                    if widget.interface.name == interface.name:
                        self.selected_item = widget
        
        # Emit signal
        self.interface_selected.emit(interface)
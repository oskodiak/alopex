"""
Telemetry Panel - Revolutionary real-time network monitoring
Making NetworkManager's monitoring look prehistoric
"""

import math
from collections import deque
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGridLayout, QProgressBar, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QLinearGradient, 
    QRadialGradient, QPainterPath, QPolygonF
)

from network.discovery import NetworkMetrics

class AnimatedProgressBar(QProgressBar):
    """Beautiful animated progress bar with glow effects"""
    
    def __init__(self, color=QColor(52, 152, 219)):
        super().__init__()
        self.color = color
        self.setTextVisible(False)
        self.setFixedHeight(8)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        bg_gradient = QLinearGradient(0, 0, 0, self.height())
        bg_gradient.setColorAt(0, QColor(44, 62, 80))
        bg_gradient.setColorAt(1, QColor(52, 73, 94))
        
        painter.setBrush(QBrush(bg_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 4, 4)
        
        # Progress
        if self.value() > 0:
            progress_width = (self.value() / self.maximum()) * self.width()
            
            fg_gradient = QLinearGradient(0, 0, 0, self.height())
            fg_gradient.setColorAt(0, self.color.lighter(120))
            fg_gradient.setColorAt(1, self.color)
            
            painter.setBrush(QBrush(fg_gradient))
            painter.drawRoundedRect(0, 0, progress_width, self.height(), 4, 4)
            
            # Glow effect
            glow_gradient = QLinearGradient(0, 0, 0, self.height())
            glow_color = self.color.lighter(150)
            glow_color.setAlpha(100)
            glow_gradient.setColorAt(0, glow_color)
            glow_gradient.setColorAt(1, QColor(0, 0, 0, 0))
            
            painter.setBrush(QBrush(glow_gradient))
            painter.drawRoundedRect(0, 0, progress_width, self.height() // 2, 4, 4)

class RealTimeGraph(QWidget):
    """Beautiful real-time network traffic graph"""
    
    def __init__(self, title="Traffic", max_points=60):
        super().__init__()
        self.title = title
        self.max_points = max_points
        self.upload_data = deque(maxlen=max_points)
        self.download_data = deque(maxlen=max_points)
        self.max_value = 100.0
        
        self.setMinimumHeight(120)
        
        # Initialize with zeros
        for _ in range(max_points):
            self.upload_data.append(0)
            self.download_data.append(0)
            
    def add_data_point(self, upload_speed, download_speed):
        """Add new data point"""
        self.upload_data.append(upload_speed)
        self.download_data.append(download_speed)
        
        # Update max value for scaling
        current_max = max(max(self.upload_data), max(self.download_data))
        if current_max > self.max_value:
            self.max_value = current_max * 1.2
        elif current_max < self.max_value * 0.5 and self.max_value > 100:
            self.max_value = max(current_max * 1.5, 100)
            
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        bg_gradient = QLinearGradient(0, 0, 0, self.height())
        bg_gradient.setColorAt(0, QColor(44, 62, 80))
        bg_gradient.setColorAt(1, QColor(52, 73, 94))
        painter.fillRect(self.rect(), QBrush(bg_gradient))
        
        # Border
        painter.setPen(QPen(QColor(58, 82, 107), 1))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 8, 8)
        
        # Title
        painter.setPen(QPen(QColor(236, 240, 241), 1))
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(10)
        painter.setFont(title_font)
        painter.drawText(16, 20, self.title)
        
        # Graph area
        graph_rect = self.rect().adjusted(16, 30, -16, -16)
        if graph_rect.width() < 50 or graph_rect.height() < 30:
            return
            
        # Grid lines
        painter.setPen(QPen(QColor(58, 82, 107), 1))
        grid_steps = 5
        for i in range(1, grid_steps):
            y = graph_rect.top() + (graph_rect.height() * i // grid_steps)
            painter.drawLine(graph_rect.left(), y, graph_rect.right(), y)
            
        # Draw graphs
        self._draw_graph_line(painter, graph_rect, self.download_data, QColor(52, 152, 219))
        self._draw_graph_line(painter, graph_rect, self.upload_data, QColor(46, 204, 113))
        
        # Legend
        legend_y = graph_rect.bottom() + 8
        
        # Upload legend
        painter.setPen(QPen(QColor(46, 204, 113), 2))
        painter.drawLine(graph_rect.left(), legend_y, graph_rect.left() + 20, legend_y)
        painter.setPen(QPen(QColor(236, 240, 241), 1))
        painter.drawText(graph_rect.left() + 25, legend_y + 4, 
                        f"↑ Upload: {self.upload_data[-1]:.1f} KB/s")
        
        # Download legend  
        painter.setPen(QPen(QColor(52, 152, 219), 2))
        mid_x = graph_rect.left() + graph_rect.width() // 2
        painter.drawLine(mid_x, legend_y, mid_x + 20, legend_y)
        painter.setPen(QPen(QColor(236, 240, 241), 1))
        painter.drawText(mid_x + 25, legend_y + 4,
                        f"↓ Download: {self.download_data[-1]:.1f} KB/s")
        
    def _draw_graph_line(self, painter, rect, data, color):
        """Draw a graph line with gradient fill"""
        if len(data) < 2:
            return
            
        points = []
        step_x = rect.width() / (len(data) - 1)
        
        for i, value in enumerate(data):
            x = rect.left() + i * step_x
            y = rect.bottom() - (value / self.max_value) * rect.height()
            points.append(QPointF(x, y))
            
        # Create path for line
        path = QPainterPath()
        if points:
            path.moveTo(points[0])
            for point in points[1:]:
                path.lineTo(point)
                
        # Draw line
        painter.setPen(QPen(color, 2))
        painter.drawPath(path)
        
        # Create filled area under line
        fill_path = QPainterPath()
        if points:
            fill_path.moveTo(points[0].x(), rect.bottom())
            for point in points:
                fill_path.lineTo(point)
            fill_path.lineTo(points[-1].x(), rect.bottom())
            fill_path.closeSubpath()
            
            # Gradient fill
            gradient = QLinearGradient(0, rect.top(), 0, rect.bottom())
            fill_color = QColor(color)
            fill_color.setAlpha(60)
            gradient.setColorAt(0, fill_color)
            fill_color.setAlpha(10)
            gradient.setColorAt(1, fill_color)
            
            painter.fillPath(fill_path, QBrush(gradient))

class MetricCard(QFrame):
    """Beautiful metric display card"""
    
    def __init__(self, title, value="", unit="", icon_color=QColor(52, 152, 219)):
        super().__init__()
        self.title = title
        self.icon_color = icon_color
        self.setup_ui()
        self.update_value(value, unit)
        
    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            MetricCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34495e, stop:1 #2c3e50);
                border: 1px solid #4a6473;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        self.setFixedHeight(80)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            color: #95a5a6;
            font-size: 9pt;
            font-weight: bold;
        """)
        layout.addWidget(title_label)
        
        # Value container
        value_layout = QHBoxLayout()
        value_layout.setContentsMargins(0, 0, 0, 0)
        
        self.value_label = QLabel("--")
        self.value_label.setStyleSheet("""
            color: #ecf0f1;
            font-size: 16pt;
            font-weight: bold;
        """)
        value_layout.addWidget(self.value_label)
        
        self.unit_label = QLabel("")
        self.unit_label.setStyleSheet("""
            color: #95a5a6;
            font-size: 10pt;
        """)
        value_layout.addWidget(self.unit_label)
        value_layout.addStretch()
        
        layout.addLayout(value_layout)
        layout.addStretch()
        
    def update_value(self, value, unit=""):
        """Update the metric value"""
        self.value_label.setText(str(value))
        self.unit_label.setText(unit)

class StatusIndicator(QWidget):
    """Animated status indicator with glow"""
    
    def __init__(self, size=24):
        super().__init__()
        self.size = size
        self.status = "Disconnected"
        self.pulse_value = 0
        self.setFixedSize(size, size)
        
        # Pulse animation
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self._update_pulse)
        
    def set_status(self, status):
        """Set status and update animation"""
        self.status = status
        if status == "Connected":
            if not self.pulse_timer.isActive():
                self.pulse_timer.start(50)
        else:
            self.pulse_timer.stop()
            self.pulse_value = 0
        self.update()
        
    def _update_pulse(self):
        self.pulse_value = (self.pulse_value + 0.1) % (2 * math.pi)
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center = self.rect().center()
        radius = self.size // 3
        
        # Status colors
        colors = {
            "Connected": QColor(46, 204, 113),
            "Connecting": QColor(241, 196, 15),
            "Disconnected": QColor(231, 76, 60)
        }
        
        color = colors.get(self.status, colors["Disconnected"])
        
        # Outer glow for connected status
        if self.status == "Connected":
            pulse_intensity = (math.sin(self.pulse_value) + 1) / 2
            glow_radius = radius + int(4 * pulse_intensity)
            
            glow_gradient = QRadialGradient(QPointF(center), glow_radius)
            glow_color = QColor(color)
            glow_color.setAlpha(int(100 * pulse_intensity))
            glow_gradient.setColorAt(0, glow_color)
            glow_gradient.setColorAt(1, QColor(0, 0, 0, 0))
            
            painter.setBrush(QBrush(glow_gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(center.x() - glow_radius, center.y() - glow_radius, 
                               glow_radius * 2, glow_radius * 2)
        
        # Main circle
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.lighter(130), 1))
        painter.drawEllipse(center.x() - radius, center.y() - radius, 
                           radius * 2, radius * 2)

class TelemetryPanel(QWidget):
    """Revolutionary telemetry panel that makes NetworkManager obsolete"""
    
    def __init__(self):
        super().__init__()
        self.active = False
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Panel header with status indicator
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34495e, stop:1 #2c3e50);
                border-bottom: 2px solid #e74c3c;
            }
        """)
        
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(16, 12, 16, 12)
        
        self.status_indicator = StatusIndicator()
        header_layout.addWidget(self.status_indicator)
        
        header_label = QLabel("Telemetry Hub")
        header_label.setStyleSheet("""
            color: #ecf0f1;
            font-size: 14pt;
            font-weight: bold;
            margin-left: 12px;
        """)
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        layout.addWidget(header_widget)
        
        # Main content
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background: #2c3e50;
                border-left: 1px solid #34495e;
            }
        """)
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(12)
        
        # Real-time traffic graph
        self.traffic_graph = RealTimeGraph("Network Traffic")
        content_layout.addWidget(self.traffic_graph)
        
        # Metrics grid
        metrics_group = QGroupBox("Connection Metrics")
        metrics_group.setStyleSheet("""
            QGroupBox {
                color: #ecf0f1;
                font-weight: bold;
                border: 1px solid #4a6473;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
            }
        """)
        
        metrics_layout = QGridLayout(metrics_group)
        metrics_layout.setSpacing(8)
        
        # Create metric cards
        self.link_speed_card = MetricCard("Link Speed", "--", "Mbps", QColor(155, 89, 182))
        self.packets_card = MetricCard("Packets/sec", "--", "pps", QColor(26, 188, 156))  
        self.errors_card = MetricCard("Errors", "--", "", QColor(231, 76, 60))
        self.uptime_card = MetricCard("Uptime", "--", "", QColor(241, 196, 15))
        
        metrics_layout.addWidget(self.link_speed_card, 0, 0)
        metrics_layout.addWidget(self.packets_card, 0, 1)
        metrics_layout.addWidget(self.errors_card, 1, 0)  
        metrics_layout.addWidget(self.uptime_card, 1, 1)
        
        content_layout.addWidget(metrics_group)
        content_layout.addStretch()
        
        layout.addWidget(content_widget, 1)
        
        # Inactive state message
        self.inactive_label = QLabel("No Active Connection\n\nSelect a connected interface to view telemetry")
        self.inactive_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.inactive_label.setStyleSheet("""
            color: #7f8c8d;
            font-size: 12pt;
            padding: 40px;
        """)
        
        # Initially show inactive state
        self.set_active(False)
        
    def set_active(self, active: bool):
        """Set telemetry panel active/inactive state"""
        self.active = active
        self.status_indicator.set_status("Connected" if active else "Disconnected")
        
        # Update header color
        header_color = "#27ae60" if active else "#e74c3c"
        self.findChildren(QWidget)[0].setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34495e, stop:1 #2c3e50);
                border-bottom: 2px solid {header_color};
            }}
        """)
        
        if active:
            self.inactive_label.hide()
            self.traffic_graph.show()
            for card in [self.link_speed_card, self.packets_card, self.errors_card, self.uptime_card]:
                card.show()
        else:
            self.traffic_graph.hide()
            for card in [self.link_speed_card, self.packets_card, self.errors_card, self.uptime_card]:
                card.hide()
            # Show inactive message
            if not hasattr(self, 'inactive_added'):
                self.layout().addWidget(self.inactive_label)
                self.inactive_added = True
            self.inactive_label.show()
            
    def update_metrics(self, metrics: NetworkMetrics):
        """Update telemetry with fresh metrics"""
        if not self.active:
            return
            
        # Update traffic graph
        self.traffic_graph.add_data_point(metrics.speed_up, metrics.speed_down)
        
        # Update metric cards
        self.link_speed_card.update_value(
            metrics.link_speed or 0, 
            "Mbps" if metrics.link_speed else ""
        )
        
        total_packets = metrics.packets_per_sec_tx + metrics.packets_per_sec_rx
        self.packets_card.update_value(f"{total_packets:.0f}", "pps")
        
        total_errors = metrics.errors_tx + metrics.errors_rx
        error_color = "#e74c3c" if total_errors > 0 else "#95a5a6"
        self.errors_card.value_label.setStyleSheet(f"""
            color: {error_color};
            font-size: 16pt;
            font-weight: bold;
        """)
        self.errors_card.update_value(total_errors)
        
        if metrics.uptime:
            hours = int(metrics.uptime // 3600)
            minutes = int((metrics.uptime % 3600) // 60)
            self.uptime_card.update_value(f"{hours:02d}:{minutes:02d}", "h:m")
        else:
            self.uptime_card.update_value("--", "")
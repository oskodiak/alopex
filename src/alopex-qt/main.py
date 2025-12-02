#!/usr/bin/env python3
"""
ALOPEX Network Manager - Qt GUI
Revolutionary network management with professional telemetry
Onyx Digital Intelligence Development LLC
"""

import sys
import asyncio
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPalette, QColor

from ui.main_window import AlopexMainWindow

def setup_theme(app):
    """Configure professional dark theme"""
    app.setStyle('Fusion')
    
    palette = QPalette()
    # Professional dark theme colors
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    
    app.setPalette(palette)

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("ALOPEX Network Manager")
    app.setApplicationDisplayName("ALOPEX")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Onyx Digital Intelligence Development LLC")
    
    # Enable system tray support - don't quit when last window closes
    app.setQuitOnLastWindowClosed(False)
    
    # Setup professional theme
    setup_theme(app)
    
    # Create main window
    window = AlopexMainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
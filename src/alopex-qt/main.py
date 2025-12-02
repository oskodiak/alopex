#!/usr/bin/env python3
"""
ALOPEX Network Manager - Qt GUI
Network management interface
"""

import sys
import asyncio
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from ui.main_window import AlopexMainWindow
from ui.arctic_theme import ArcticTheme

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("ALOPEX Network Manager")
    app.setApplicationDisplayName("ALOPEX")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("")
    
    # Enable system tray support - don't quit when last window closes
    app.setQuitOnLastWindowClosed(False)
    
    # Apply Arctic Terminal theme
    ArcticTheme.apply_to_app(app)
    
    # Create main window
    window = AlopexMainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
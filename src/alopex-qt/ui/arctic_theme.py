"""
Arctic Terminal Theme for ALOPEX
Professional styling with Arctic Terminal color scheme
"""

from PyQt6.QtGui import QPalette, QColor, QFont
from PyQt6.QtWidgets import QApplication

class ArcticTheme:
    """Arctic Terminal professional color scheme for ALOPEX"""
    
    # Core Arctic Terminal colors
    BACKGROUND_MAIN = "#11151C"      # Near-black graphite
    BACKGROUND_PANEL = "#161B22"     # Panel/card background
    BACKGROUND_ELEVATED = "#1F2937"  # Elevated surfaces
    
    # Primary accent colors
    PRIMARY_ACCENT = "#3BA6FF"       # Cool slate/ice blue
    SECONDARY_ACCENT = "#64FFDA"     # Arctic cyan
    TERTIARY_ACCENT = "#BB86FC"      # Arctic purple
    
    # Status colors
    SUCCESS = "#4CAF50"              # Muted green
    WARNING = "#FFC107"              # Amber warning
    DANGER = "#F44336"               # Soft red
    INFO = "#2196F3"                 # Info blue
    
    # Text hierarchy
    TEXT_PRIMARY = "#FFFFFF"         # Pure white
    TEXT_SECONDARY = "#B0BEC5"       # Cool gray
    TEXT_MUTED = "#78909C"           # Muted gray
    TEXT_DISABLED = "#455A64"        # Disabled gray
    
    # Borders and surfaces
    BORDER_PRIMARY = "#37474F"       # Primary borders
    BORDER_SUBTLE = "#263238"        # Subtle dividers
    SURFACE_HOVER = "#1E3A8A"        # Hover states
    
    @classmethod
    def apply_to_app(cls, app: QApplication):
        """Apply Arctic Terminal theme to PyQt application"""
        app.setStyle('Fusion')
        
        palette = QPalette()
        
        # Window and base colors
        palette.setColor(QPalette.ColorRole.Window, QColor(cls.BACKGROUND_MAIN))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(cls.TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Base, QColor(cls.BACKGROUND_PANEL))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(cls.BACKGROUND_ELEVATED))
        
        # Text colors
        palette.setColor(QPalette.ColorRole.Text, QColor(cls.TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(cls.TEXT_PRIMARY))
        
        # Button colors
        palette.setColor(QPalette.ColorRole.Button, QColor(cls.BACKGROUND_ELEVATED))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(cls.TEXT_PRIMARY))
        
        # Tooltip colors
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(cls.BACKGROUND_MAIN))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(cls.TEXT_PRIMARY))
        
        # Selection and highlight
        palette.setColor(QPalette.ColorRole.Highlight, QColor(cls.PRIMARY_ACCENT))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(cls.BACKGROUND_MAIN))
        palette.setColor(QPalette.ColorRole.Link, QColor(cls.PRIMARY_ACCENT))
        
        app.setPalette(palette)
    
    @classmethod
    def get_header_style(cls) -> str:
        """Professional header styling"""
        return f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {cls.BACKGROUND_ELEVATED}, stop:1 {cls.BACKGROUND_PANEL});
                color: {cls.TEXT_PRIMARY};
                font-size: 14pt;
                font-weight: bold;
                padding: 16px;
                border-bottom: 2px solid {cls.PRIMARY_ACCENT};
            }}
        """
    
    @classmethod
    def get_panel_style(cls) -> str:
        """Professional panel styling"""
        return f"""
            QGroupBox {{
                background: {cls.BACKGROUND_PANEL};
                border: 1px solid {cls.BORDER_PRIMARY};
                border-radius: 8px;
                color: {cls.TEXT_PRIMARY};
                font-weight: bold;
                padding-top: 12px;
                margin-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: {cls.PRIMARY_ACCENT};
            }}
        """
    
    @classmethod
    def get_card_style(cls) -> str:
        """Beautiful metric card styling"""
        return f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {cls.BACKGROUND_ELEVATED}, stop:1 {cls.BACKGROUND_PANEL});
                border: 1px solid {cls.BORDER_PRIMARY};
                border-radius: 12px;
                padding: 8px;
            }}
        """
    
    @classmethod 
    def get_button_style(cls, variant="primary") -> str:
        """Professional button styling with variants"""
        if variant == "primary":
            bg_start = cls.PRIMARY_ACCENT
            bg_end = "#2E7DD2"  # Darker blue
            hover_start = cls.SUCCESS
            hover_end = "#388E3C"  # Darker green
        elif variant == "success":
            bg_start = cls.SUCCESS
            bg_end = "#388E3C"
            hover_start = "#66BB6A"
            hover_end = cls.SUCCESS
        elif variant == "danger":
            bg_start = cls.DANGER
            bg_end = "#C62828"
            hover_start = "#EF5350"
            hover_end = cls.DANGER
        else:
            bg_start = cls.BACKGROUND_ELEVATED
            bg_end = cls.BACKGROUND_PANEL
            hover_start = cls.SURFACE_HOVER
            hover_end = cls.BACKGROUND_ELEVATED
            
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {bg_start}, stop:1 {bg_end});
                color: {cls.TEXT_PRIMARY};
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {hover_start}, stop:1 {hover_end});
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {bg_end}, stop:1 {bg_start});
            }}
            QPushButton:disabled {{
                background: {cls.BACKGROUND_PANEL};
                color: {cls.TEXT_DISABLED};
            }}
        """
    
    @classmethod
    def get_input_style(cls) -> str:
        """Professional input field styling"""
        return f"""
            QLineEdit {{
                background: {cls.BACKGROUND_MAIN};
                color: {cls.TEXT_PRIMARY};
                border: 2px solid {cls.BORDER_SUBTLE};
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 10pt;
            }}
            QLineEdit:focus {{
                border-color: {cls.PRIMARY_ACCENT};
            }}
            QLineEdit:disabled {{
                background: {cls.BACKGROUND_PANEL};
                color: {cls.TEXT_DISABLED};
                border-color: {cls.BORDER_SUBTLE};
            }}
        """
    
    @classmethod
    def get_scrollbar_style(cls) -> str:
        """Professional scrollbar styling"""
        return f"""
            QScrollBar:vertical {{
                background: {cls.BACKGROUND_PANEL};
                width: 14px;
                border-radius: 7px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {cls.PRIMARY_ACCENT};
                border-radius: 7px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {cls.SECONDARY_ACCENT};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """
    
    @classmethod
    def get_list_style(cls) -> str:
        """Professional list widget styling"""
        return f"""
            QListWidget {{
                background: {cls.BACKGROUND_MAIN};
                color: {cls.TEXT_PRIMARY};
                border: 1px solid {cls.BORDER_PRIMARY};
                border-radius: 8px;
                font-size: 10pt;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 12px;
                border-bottom: 1px solid {cls.BORDER_SUBTLE};
                border-radius: 6px;
                margin: 2px;
            }}
            QListWidget::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {cls.PRIMARY_ACCENT}, stop:1 #2E7DD2);
                color: {cls.TEXT_PRIMARY};
            }}
            QListWidget::item:hover {{
                background: {cls.SURFACE_HOVER};
            }}
        """

class FontManager:
    """Professional font management for ALOPEX"""
    
    @classmethod
    def get_primary_font(cls, size=10, weight=400):
        """Primary application font"""
        font = QFont("Inter", size, weight)
        font.setStyleHint(QFont.StyleHint.SansSerif)
        return font
    
    @classmethod
    def get_title_font(cls, size=16):
        """Title font for headers"""
        font = QFont("Inter", size, 600)
        font.setStyleHint(QFont.StyleHint.SansSerif)
        return font
    
    @classmethod
    def get_monospace_font(cls, size=9):
        """Monospace font for telemetry"""
        font = QFont("SF Mono", size)
        font.setStyleHint(QFont.StyleHint.Monospace)
        return font
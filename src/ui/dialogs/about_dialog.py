# src/ui/dialogs/about_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QDialogButtonBox,
    QHBoxLayout, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont

class AboutDialog(QDialog):
    """Dialog showing information about the application."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("About Flashcard App")
        self.setFixedSize(500, 500)
        self.setObjectName("aboutDialog")  # For CSS styling
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # App title
        title = QLabel("Flashcard Study Application")
        title.setObjectName("appName")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        # Version
        version = QLabel("Version 1.0.0")
        version.setObjectName("appVersion")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)
        
        # Description
        description = QLabel(
            "An AI-powered flashcard application for studying any topic. "
            "This app connects to a powerful AI backend to generate high-quality "
            "flashcards on any subject, helping you learn more effectively."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)
        
        # Features
        features = QLabel(
            "• AI-generated flashcards on any topic\n"
            "• Interactive study sessions\n"
            "• Study history and performance tracking\n"
            "• Light and dark themes"
        )
        features.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(features)
        
        # Technology info
        tech_info = QLabel("Built with Python, PyQt6, and FastAPI")
        tech_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tech_info)
        
        # Add spacer
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Copyright
        copyright = QLabel("© 2025 Abdulla Kayyani")
        copyright.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
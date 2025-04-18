# src/ui/dialogs/settings_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, 
    QLineEdit, QSpinBox, QComboBox, QDialogButtonBox,
    QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt

from src.utils.logger import get_logger
from src.utils.error_handling import handle_errors

class SettingsDialog(QDialog):
    """Dialog for adjusting application settings."""
    
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.logger = get_logger(__name__)
        
        self.setWindowTitle("Settings")
        self.setMinimumWidth(450)
        self.setObjectName("settingsDialog")  # For CSS styling
        
        # Create UI
        self.setup_ui()
        
        # Load current settings
        self.load_settings()
    
    @handle_errors(dialog_title="UI Error")
    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # API settings group
        api_group = QGroupBox("API Settings")
        api_layout = QFormLayout(api_group)
        
        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("http://localhost:8000")
        api_layout.addRow("API URL:", self.api_url_input)
        
        # API connection timeout
        self.api_timeout_input = QSpinBox()
        self.api_timeout_input.setRange(10, 180)
        self.api_timeout_input.setSingleStep(10)
        self.api_timeout_input.setSuffix(" seconds")
        api_layout.addRow("Connection Timeout:", self.api_timeout_input)
        
        layout.addWidget(api_group)
        
        # Study settings group
        study_group = QGroupBox("Study Settings")
        study_layout = QFormLayout(study_group)
        
        self.cards_per_session_input = QSpinBox()
        self.cards_per_session_input.setRange(5, 100)
        self.cards_per_session_input.setSingleStep(5)
        study_layout.addRow("Cards per session:", self.cards_per_session_input)
        
        self.shuffle_cards_checkbox = QCheckBox("Shuffle cards during study")
        study_layout.addRow("", self.shuffle_cards_checkbox)
        
        self.auto_flip_checkbox = QCheckBox("Auto-flip to answer after marking")
        study_layout.addRow("", self.auto_flip_checkbox)
        
        layout.addWidget(study_group)
        
        # Appearance settings
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Light", "light")
        self.theme_combo.addItem("Dark", "dark")
        appearance_layout.addRow("Theme:", self.theme_combo)
        
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItem("Small", "small")
        self.font_size_combo.addItem("Medium", "medium")
        self.font_size_combo.addItem("Large", "large")
        appearance_layout.addRow("Font Size:", self.font_size_combo)
        
        layout.addWidget(appearance_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.Reset
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_settings)
        button_box.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(self.reset_to_defaults)
        layout.addWidget(button_box)
    
    def load_settings(self):
        """Load current settings into the UI."""
        # API URL
        api_url = self.settings.get("api_url", "http://localhost:8000")
        self.api_url_input.setText(api_url)
        
        # API timeout
        api_timeout = self.settings.get("api_timeout", 60)
        self.api_timeout_input.setValue(api_timeout)
        
        # Cards per session
        cards_per_session = self.settings.get("study_session_cards", 20)
        self.cards_per_session_input.setValue(cards_per_session)
        
        # Shuffle cards
        shuffle_cards = self.settings.get("shuffle_cards", True)
        self.shuffle_cards_checkbox.setChecked(shuffle_cards)
        
        # Auto flip
        auto_flip = self.settings.get("auto_flip", False)
        self.auto_flip_checkbox.setChecked(auto_flip)
        
        # Theme
        theme = self.settings.get("theme", "light")
        index = 1 if theme == "dark" else 0  # Default to light if unknown
        self.theme_combo.setCurrentIndex(index)
        
        # Font size
        font_size = self.settings.get("font_size", "medium")
        index = 0 if font_size == "small" else (2 if font_size == "large" else 1)
        self.font_size_combo.setCurrentIndex(index)
    
    def apply_settings(self):
        """Apply settings without closing the dialog."""
        # Get values from inputs
        api_url = self.api_url_input.text().strip()
        api_timeout = self.api_timeout_input.value()
        cards_per_session = self.cards_per_session_input.value()
        shuffle_cards = self.shuffle_cards_checkbox.isChecked()
        auto_flip = self.auto_flip_checkbox.isChecked()
        theme = self.theme_combo.currentData()
        font_size = self.font_size_combo.currentData()
        
        # Save to settings
        self.settings.set("api_url", api_url)
        self.settings.set("api_timeout", api_timeout)
        self.settings.set("study_session_cards", cards_per_session)
        self.settings.set("shuffle_cards", shuffle_cards)
        self.settings.set("auto_flip", auto_flip)
        self.settings.set("theme", theme)
        self.settings.set("font_size", font_size)
        
        self.logger.info("Settings applied")
        
        # Emit signal to notify parent of settings changes
        self.parent().settings_changed()
    
    def accept(self):
        """Save settings when dialog is accepted."""
        self.apply_settings()
        
        # Close dialog
        super().accept()
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        # First reset settings in storage
        self.settings.reset()
        
        # Then reload UI
        self.load_settings()
        
        self.logger.info("Settings reset to defaults")
        
        # Notify parent
        self.parent().settings_changed()
# src/ui/theme.py
import os
import json
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QFile, QTextStream, QIODevice
from src.utils.logger import get_logger
from src.utils.error_handling import handle_errors

class ThemeManager:
    """Manages application themes (light/dark) and applies styles."""
    
    def __init__(self, settings):
        self.settings = settings
        self.logger = get_logger(__name__)
        
        # Base directory for styles
        self.styles_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "assets", "styles"
        )
        
        # Load variables
        self.variables = self._load_variables()
    
    def _load_variables(self):
        """Load theme variables from JSON file."""
        variables_path = os.path.join(self.styles_dir, "variables.json")
        
        if os.path.exists(variables_path):
            try:
                with open(variables_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading theme variables: {e}")
        
        # Fallback variables
        return {
            "light": {
                "background": "#f5f5f5",
                "foreground": "#333333",
                "primary": "#4285F4",
                "secondary": "#34A853",
                "accent": "#FBBC05",
                "error": "#EA4335",
                "border": "#d0d0d0"
            },
            "dark": {
                "background": "#2d2d2d",
                "foreground": "#e0e0e0",
                "primary": "#4285F4",
                "secondary": "#34A853",
                "accent": "#FBBC05",
                "error": "#EA4335",
                "border": "#555555"
            }
        }
    
    def _load_stylesheet(self, file_path):
        """Load a QSS stylesheet from file."""
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    return f.read()
            except Exception as e:
                self.logger.error(f"Error loading stylesheet {file_path}: {e}")
        return ""
    
    def get_current_theme(self):
        """Get the current theme name from settings."""
        return self.settings.get("theme", "light")
    
    def set_theme(self, theme_name):
        """Set the theme and apply it."""
        if theme_name not in ["light", "dark"]:
            theme_name = "light"  # Default to light if invalid
        
        self.settings.set("theme", theme_name)
        self.apply_theme()
    
    @handle_errors(show_dialog=False, log_exception=True)
    def apply_theme(self):
        """Apply the current theme to the application."""
        theme_name = self.get_current_theme()
        self.logger.info(f"Applying theme: {theme_name}")
        
        # Load main stylesheet
        main_qss = self._load_stylesheet(os.path.join(self.styles_dir, "main.qss"))
        
        # Load theme-specific stylesheet
        theme_qss = self._load_stylesheet(os.path.join(self.styles_dir, f"{theme_name}_theme.qss"))
        
        # Load component stylesheets
        buttons_qss = self._load_stylesheet(os.path.join(self.styles_dir, "components", "buttons.qss"))
        cards_qss = self._load_stylesheet(os.path.join(self.styles_dir, "components", "cards.qss"))
        dialogs_qss = self._load_stylesheet(os.path.join(self.styles_dir, "components", "dialogs.qss"))
        forms_qss = self._load_stylesheet(os.path.join(self.styles_dir, "components", "forms.qss"))
        
        # Combine all stylesheets
        combined_qss = main_qss + theme_qss + buttons_qss + cards_qss + dialogs_qss + forms_qss
        
        # Replace variables
        if theme_name in self.variables:
            theme_vars = self.variables[theme_name]
            for var_name, var_value in theme_vars.items():
                combined_qss = combined_qss.replace(f"${{var.{var_name}}}", var_value)
        
        # Apply the stylesheet
        app = QApplication.instance()
        if app:
            app.setStyleSheet(combined_qss)
            self.logger.debug("Applied theme stylesheet to application")
        else:
            self.logger.error("Failed to apply theme: No QApplication instance found")

    def toggle_theme(self):
        """Toggle between light and dark theme."""
        current_theme = self.get_current_theme()
        new_theme = "dark" if current_theme == "light" else "light"
        self.set_theme(new_theme)
        return new_theme
import os
import json
from src.utils.logger import get_logger
from src.utils.error_handling import handle_errors

class Settings:
    """Manages application settings with loading and saving capabilities."""
    
    def __init__(self, settings_path=None):
        self.logger = get_logger("settings")
        
        # Set default settings file path if not provided
        if settings_path is None:
            settings_dir = os.path.join(os.path.expanduser("~"), ".flashcards")
            os.makedirs(settings_dir, exist_ok=True)
            settings_path = os.path.join(settings_dir, "settings.json")
        
        self.settings_path = settings_path
        self.logger.debug(f"Settings path: {self.settings_path}")
        
        # Default settings
        self.defaults = {
            "api_url": "http://localhost:8000",
            "theme": "light",
            "study_session_cards": 20,
            "card_font_size": 14,
            "save_history": True,
            "max_history_sessions": 100
        }
        
        # Load settings or create default ones
        self.data = self.load()
    
    @handle_errors(show_dialog=False, log_exception=True)
    def load(self):
        """Load settings from file or return defaults if file doesn't exist."""
        if os.path.exists(self.settings_path):
            with open(self.settings_path, 'r') as f:
                self.logger.debug("Loading settings from file")
                settings = json.load(f)
                
                # Merge with defaults to ensure all settings exist
                merged_settings = self.defaults.copy()
                merged_settings.update(settings)
                return merged_settings
        else:
            self.logger.info("Settings file not found, using defaults")
            # Save the defaults right away
            self.save()
            return self.defaults.copy()
    
    @handle_errors(show_dialog=False, log_exception=True)
    def save(self):
        """Save current settings to file."""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
        
        # Temporarily write to a new file
        temp_path = f"{self.settings_path}.tmp"
        with open(temp_path, 'w') as f:
            self.logger.debug("Saving settings to file")
            json.dump(self.data, f, indent=4)
        
        # Rename the temp file to the actual settings file (safer against corruption)
        if os.path.exists(self.settings_path):
            os.replace(temp_path, self.settings_path)
        else:
            os.rename(temp_path, self.settings_path)
            
        return True
    
    def get(self, key, default=None):
        """Get a setting value by key."""
        value = self.data.get(key)
        
        # If the key doesn't exist in data, return the provided default
        if value is None:
            # If we have a default defined in self.defaults, use that
            if key in self.defaults:
                return self.defaults.get(key)
            # Otherwise use the provided default
            return default
            
        return value
    
    @handle_errors(show_dialog=False, log_exception=True)
    def set(self, key, value):
        """Set a setting value and save to file."""
        self.data[key] = value
        return self.save()
    
    @handle_errors(dialog_title="Settings Reset", log_exception=True)
    def reset(self):
        """Reset settings to defaults."""
        self.data = self.defaults.copy()
        return self.save()
    
    @handle_errors(show_dialog=False, log_exception=True)
    def _backup_corrupt_settings(self):
        """Create a backup of corrupt settings file."""
        if os.path.exists(self.settings_path):
            backup_path = f"{self.settings_path}.bak"
            # Copy the corrupt file to a backup
            with open(self.settings_path, 'r') as src:
                with open(backup_path, 'w') as dst:
                    dst.write(src.read())
            self.logger.info(f"Created backup of corrupt settings at {backup_path}")
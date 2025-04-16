import os
import sys
from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtCore import Qt
from src.ui.mainwindow import MainWindow
from src.utils.logger import setup_logger, get_logger
from src.core.settings import Settings
from src.data.storage import SQLiteStorage

class FlashCardApp:
    """
    Main application controller class that initializes and connects all components
    of the flashcard application.
    """
    def __init__(self):
        # Set up logging first so we can track initialization
        self.logger = setup_logger()
        self.logger.info("Initializing FlashCard Application")
        
        # Load application settings
        self.settings = Settings()
        self.logger.info("Settings loaded")
        
        # Initialize data storage
        self.storage = SQLiteStorage()
        self.logger.info("Database storage initialized")
        
        # Create main application window
        self.main_window = MainWindow(self.settings, self.storage)
        self.logger.info("Main window created")
        
        # Connect application-level signals
        self._connect_signals()
        
    def _connect_signals(self):
        """Connect any application-level signals"""
        # Get the QApplication instance
        app = QApplication.instance()
        
        # Connect the aboutToQuit signal to our cleanup method
        app.aboutToQuit.connect(self.cleanup)
    
    def show(self):
        """Show the main application window"""
        self.main_window.show()
        self.logger.info("Main window displayed")
    
    def cleanup(self):
        """Perform cleanup operations before the application exits"""
        self.logger.info("Application shutting down, performing cleanup")
        
        # Save settings
        self.settings.save()
        
        # Close any open resources
        # (This would be where you'd close network connections, etc.)
        
        self.logger.info("Cleanup completed")
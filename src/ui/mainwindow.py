import sys
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QWidget, 
    QToolBar, QStatusBar, QMessageBox
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, pyqtSignal
from src.ui.views.home_view import HomeView
from src.ui.views.study_view import StudyView
from src.ui.views.history_view import HistoryView
from src.ui.dialogs.settings_dialog import SettingsDialog
from src.ui.dialogs.about_dialog import AboutDialog
from src.ui.theme import ThemeManager
from src.utils.logger import get_logger
from src.utils.error_handling import handle_errors
from src.api.client import APIClient

class MainWindow(QMainWindow):
    """Main application window with tabs, menus, and central widget."""
    
    def __init__(self, settings, storage):
        super().__init__()
        
        self.settings = settings
        self.storage = storage
        self.logger = get_logger("mainwindow")
        
        # Initialize theme manager
        self.theme_manager = ThemeManager(self.settings)
        
        # Setup UI components
        self.setup_ui()
        
        # Apply current theme
        self.theme_manager.apply_theme()
        
        self.logger.info("MainWindow initialized")
    
    @handle_errors(dialog_title="UI Error")
    def setup_ui(self):
        """Set up the main window UI components."""
        # Set window properties
        self.setWindowTitle("Flashcard App")
        self.setMinimumSize(900, 600)
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create views
        self.home_view = HomeView(self.settings, self.storage)
        self.study_view = StudyView(self.settings, self.storage)
        self.history_view = HistoryView(self.settings, self.storage)
        
        # Add tabs
        self.tab_widget.addTab(self.home_view, "Create Cards")
        self.tab_widget.addTab(self.study_view, "Study")
        self.tab_widget.addTab(self.history_view, "History")
        
        # Add tab widget to layout
        self.main_layout.addWidget(self.tab_widget)
        
        # Create status bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Setup menu and toolbar
        self.setup_menu()
        self.setup_toolbar()
        
        # Connect signals
        self.connect_signals()
    
    @handle_errors(dialog_title="UI Error")
    def setup_menu(self):
        """Set up the application menu bar."""
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        
        # New deck action
        new_deck_action = QAction("New Deck", self)
        new_deck_action.setShortcut("Ctrl+N")
        new_deck_action.triggered.connect(self.on_new_deck)
        file_menu.addAction(new_deck_action)
        
        file_menu.addSeparator()
        
        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = self.menuBar().addMenu("&View")
        
        # Theme submenu
        theme_menu = view_menu.addMenu("Theme")
        
        # Light theme action
        light_theme_action = QAction("Light", self)
        light_theme_action.triggered.connect(lambda: self.change_theme("light"))
        theme_menu.addAction(light_theme_action)
        
        # Dark theme action
        dark_theme_action = QAction("Dark", self)
        dark_theme_action.triggered.connect(lambda: self.change_theme("dark"))
        theme_menu.addAction(dark_theme_action)
        
        # Help menu
        help_menu = self.menuBar().addMenu("&Help")
        
        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    @handle_errors(dialog_title="UI Error")
    def setup_toolbar(self):
        """Set up the main toolbar."""
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        
        # Add toolbar actions
        # Create Cards action
        create_action = QAction("Create Cards", self)
        create_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        self.toolbar.addAction(create_action)
        
        # Study action
        study_action = QAction("Study", self)
        study_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        self.toolbar.addAction(study_action)
        
        # History action
        history_action = QAction("History", self)
        history_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
        self.toolbar.addAction(history_action)
        
        self.toolbar.addSeparator()
        
        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        self.toolbar.addAction(settings_action)
    
    def connect_signals(self):
        """Connect signals between components."""
        # Connect home view signals
        self.home_view.deck_created.connect(self.on_deck_created)
        
        # Connect study view signals
        self.study_view.study_completed.connect(self.on_study_completed)
        
        # Connect tab changed signal
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

    def settings_changed(self):
        """Handle settings being changed."""
        self.logger.info("Applying updated settings")
        
        # Apply theme
        self.theme_manager.apply_theme()
        
        # Update API client with new URL
        api_url = self.settings.get("api_url", "http://localhost:8000")
        api_timeout = self.settings.get("api_timeout", 60)
        
        # Create new API client with updated settings
        self.api_client = APIClient(base_url=api_url, timeout=api_timeout)
        
        # Notify views of settings changes
        if hasattr(self, 'home_view'):
            self.home_view.update_settings()
        
        if hasattr(self, 'study_view'):
            self.study_view.update_settings()
        
        if hasattr(self, 'history_view'):
            self.history_view.update_settings()
        
        # Update status bar
        self.status_bar.showMessage("Settings updated", 3000)
    
    @handle_errors(dialog_title="Theme Error")
    def change_theme(self, theme_name):
        """Change the application theme."""
        self.theme_manager.set_theme(theme_name)
        self.settings.set("theme", theme_name)
        self.status_bar.showMessage(f"{theme_name.capitalize()} theme applied", 3000)
    
    @handle_errors(dialog_title="Settings Error")
    def show_settings(self):
        """Show the settings dialog."""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            # Apply any changed settings
            self.theme_manager.apply_theme()
            self.status_bar.showMessage("Settings updated", 3000)
    
    def show_about(self):
        """Show the about dialog."""
        dialog = AboutDialog(self)
        dialog.exec()
    
    def on_new_deck(self):
        """Handle new deck action."""
        # Switch to home tab
        self.tab_widget.setCurrentIndex(0)
        # Tell home view to start a new deck
        self.home_view.start_new_deck()
    
    def on_deck_created(self, deck_id):
        """Handle deck created signal from home view."""
        self.logger.info(f"Deck created: {deck_id}")
        self.status_bar.showMessage("New deck created", 3000)
        
        # Switch to study tab
        self.tab_widget.setCurrentIndex(1)
        
        # Refresh study view
        self.study_view.refresh_decks()
        
        # Auto-select the newly created deck
        self.study_view.select_deck(deck_id)
    
    def on_study_completed(self, deck_id, cards_studied, cards_correct):
        """Handle study session completed signal."""
        self.logger.info(f"Study session completed: {deck_id}, {cards_studied}/{cards_correct}")
        
        # Update status bar
        if cards_studied > 0:
            accuracy = (cards_correct / cards_studied) * 100
            self.status_bar.showMessage(f"Study session completed: {accuracy:.1f}% accuracy", 5000)
        else:
            self.status_bar.showMessage("Study session completed", 3000)
    
    def on_tab_changed(self, index):
        """Handle tab changed event."""
        tab_name = self.tab_widget.tabText(index)
        self.logger.debug(f"Tab changed to: {tab_name}")
        
        # Refresh the view when switching to it
        if index == 1:  # Study tab
            self.study_view.refresh_decks()
        elif index == 2:  # History tab
            self.history_view.refresh_history()
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Ask for confirmation before closing
        reply = QMessageBox.question(
            self, 
            'Confirm Exit',
            'Are you sure you want to exit?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.logger.info("Application closing")
            event.accept()
        else:
            event.ignore()
# src/ui/mainwindow.py
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QWidget,
    QStatusBar, QMessageBox, QSplitter, QApplication
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRect
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

        # Get screen information for responsive sizing
        self.screen_geometry = QApplication.primaryScreen().geometry()
        self.screen_width = self.screen_geometry.width()
        self.screen_height = self.screen_geometry.height()
        self.logger.info(f"Screen dimensions: {self.screen_width}x{self.screen_height}")

        # Setup UI components
        self.setup_ui()

        # Apply current theme
        self.theme_manager.apply_theme()

        # Set up responsive sizing
        self.setup_responsive_layout()

        self.logger.info("MainWindow initialized")

    @handle_errors(dialog_title="UI Error")
    def setup_ui(self):
        """Set up the main window UI components."""
        # Set window properties
        self.setWindowTitle("Flashcard App")

        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Create main layout and explicitly parent it to the central widget
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)  # Minimize spacing for maximizing content area

        # Create tab widget WITHOUT explicit parent initially
        # self.tab_widget = QTabWidget(self.central_widget) # <-- Original line
        self.tab_widget = QTabWidget() # <-- FIX: Create without parent
        self.tab_widget.setDocumentMode(True)  # Cleaner tab appearance
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(True)  # Allow tab reordering

        # Create views
        self.home_view = HomeView(self.settings, self.storage)
        self.study_view = StudyView(self.settings, self.storage)
        self.history_view = HistoryView(self.settings, self.storage)

        # Add tabs (QTabWidget takes ownership of the view widgets)
        self.tab_widget.addTab(self.home_view, "Create Cards")
        self.tab_widget.addTab(self.study_view, "Study")
        self.tab_widget.addTab(self.history_view, "History")

        # Add tab widget to layout (layout handles parenting now)
        self.main_layout.addWidget(self.tab_widget)

        # Create status bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Setup menu bar
        self.setup_menu()

        # Connect signals
        self.connect_signals()

    def setup_responsive_layout(self):
        """Configure responsive behavior based on screen size."""
        # Set initial window size based on screen dimensions
        width = min(int(self.screen_width * 0.85), 1400)  # Use 85% of screen width up to 1400px
        height = min(int(self.screen_height * 0.85), 900)  # Use 85% of screen height up to 900px

        # Calculate position to center on screen
        x = (self.screen_width - width) // 2
        y = (self.screen_height - height) // 2

        # Set geometry
        self.setGeometry(x, y, width, height)

        # Set minimum size to ensure usability on smaller screens
        min_width = min(800, self.screen_width - 100)
        min_height = min(600, self.screen_height - 100)
        self.setMinimumSize(min_width, min_height)

        # Adjust font size based on screen DPI
        base_font_size = 10
        logical_dpi = QApplication.primaryScreen().logicalDotsPerInch()
        if logical_dpi > 120:
            base_font_size = 12

        # Apply full screen optimizations
        # Retain menu bar in full screen mode
        self.menuBar().setNativeMenuBar(False)

        # Log the responsive setup
        self.logger.info(f"Responsive layout configured: window size {width}x{height}, "
                         f"minimum size {min_width}x{min_height}")

    def resizeEvent(self, event):
        """Handle window resize events for responsive adjustments."""
        # Call parent implementation
        super().resizeEvent(event)

        # Adjust UI elements based on new window size
        window_width = event.size().width()
        window_height = event.size().height()

        # Example: Adjust tab widget height dynamically
        # Calculate available height excluding menu and status bars
        menu_bar_height = self.menuBar().height() if self.menuBar() and not self.menuBar().isHidden() else 0
        status_bar_height = self.statusBar().height() if self.statusBar() and not self.statusBar().isHidden() else 0
        content_height = window_height - menu_bar_height - status_bar_height

        # Ensure content_height is not negative
        content_height = max(0, content_height)

        # Set the fixed height for the tab widget based on available space
        # Note: Setting fixed height might conflict with expanding size policy.
        # Consider if setting minimum/maximum height or adjusting layout stretch is better.
        # self.tab_widget.setFixedHeight(content_height) # Potential conflict

        # Let child views know about the resize
        for i in range(self.tab_widget.count()):
            view = self.tab_widget.widget(i)
            if view and hasattr(view, 'handle_resize'):
                 # Pass the size of the tab widget's content area if possible,
                 # otherwise pass the window's content height.
                tab_content_rect = self.tab_widget.rect() # Might need adjustment for tab bar
                view.handle_resize(window_width, content_height)


    def showMaximized(self):
        """Override to optimize UI for maximized state."""
        # Do any pre-maximized adjustments
        super().showMaximized()

        # Adjust UI for maximized state
        self.logger.info("Window maximized - optimizing layout")

        # Notify views of maximized state
        for i in range(self.tab_widget.count()):
            view = self.tab_widget.widget(i)
            if view and hasattr(view, 'handle_maximized'):
                view.handle_maximized()

    def showNormal(self):
        """Override to revert UI optimizations when un-maximizing."""
        # Do any pre-normal state adjustments
        super().showNormal()

        # Adjust UI for normal state
        self.logger.info("Window restored - reverting to normal layout")

        # Notify views of normal state
        for i in range(self.tab_widget.count()):
            view = self.tab_widget.widget(i)
            if view and hasattr(view, 'handle_normal'):
                view.handle_normal()

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

        # Full screen toggle
        toggle_fullscreen_action = QAction("Toggle Full Screen", self)
        toggle_fullscreen_action.setShortcut("F11")
        toggle_fullscreen_action.triggered.connect(self.toggle_fullscreen)
        file_menu.addAction(toggle_fullscreen_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = self.menuBar().addMenu("&View")

        # Add navigation actions to View menu
        create_cards_action = QAction("Create Cards", self)
        create_cards_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        view_menu.addAction(create_cards_action)

        study_action = QAction("Study", self)
        study_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        view_menu.addAction(study_action)

        history_action = QAction("History", self)
        history_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
        view_menu.addAction(history_action)

        view_menu.addSeparator()

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

    def toggle_fullscreen(self):
        """Toggle between fullscreen and normal window mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def connect_signals(self):
        """Connect signals between components."""
        # Connect home view signals
        if hasattr(self, 'home_view') and self.home_view:
             self.home_view.deck_created.connect(self.on_deck_created)

        # Connect study view signals
        if hasattr(self, 'study_view') and self.study_view:
             self.study_view.study_completed.connect(self.on_study_completed)

        # Connect tab changed signal
        if hasattr(self, 'tab_widget') and self.tab_widget:
             self.tab_widget.currentChanged.connect(self.on_tab_changed)


    def settings_changed(self):
        """Handle settings being changed (called from SettingsDialog or here)."""
        self.logger.info("Applying updated settings")

        # Apply theme
        self.theme_manager.apply_theme()

        # Notify views of settings changes if they need it
        for i in range(self.tab_widget.count()):
             view = self.tab_widget.widget(i)
             if view and hasattr(view, 'update_settings'):
                  view.update_settings()

        # Update status bar
        self.status_bar.showMessage("Settings updated", 3000)

    @handle_errors(dialog_title="Theme Error")
    def change_theme(self, theme_name):
        """Change the application theme."""
        self.theme_manager.set_theme(theme_name)
        self.status_bar.showMessage(f"{theme_name.capitalize()} theme applied", 3000)

    @handle_errors(dialog_title="Settings Error")
    def show_settings(self, checked=None):
        """Show the settings dialog."""
        dialog = SettingsDialog(self.settings, self)
        # Connect the accepted signal to settings_changed AFTER dialog execution
        # to ensure changes are applied only if OK/Apply is pressed.
        if dialog.exec():
            # Re-apply settings if dialog was accepted (OK pressed)
            self.settings_changed()
        # Note: Apply button in dialog already calls self.settings_changed

    def show_about(self):
        """Show the about dialog."""
        dialog = AboutDialog(self)
        dialog.exec()

    def on_new_deck(self):
        """Handle new deck action."""
        # Switch to home tab
        if hasattr(self, 'tab_widget') and self.tab_widget:
             self.tab_widget.setCurrentIndex(0)

        # Tell home view to start a new deck
        if hasattr(self, 'home_view') and self.home_view:
             self.home_view.start_new_deck()


    def on_deck_created(self, deck_id):
        """Handle deck created signal from home view."""
        self.logger.info(f"Deck created: {deck_id}")
        self.status_bar.showMessage("New deck created", 3000)

        # Switch to study tab
        if hasattr(self, 'tab_widget') and self.tab_widget:
             self.tab_widget.setCurrentIndex(1)

        # Refresh study view deck list and select the new deck
        if hasattr(self, 'study_view') and self.study_view:
             self.study_view.refresh_decks()
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
        if not hasattr(self, 'tab_widget') or not self.tab_widget:
             return # Guard against calls during setup/teardown

        tab_name = self.tab_widget.tabText(index)
        view = self.tab_widget.widget(index) # Get the widget for the current index

        if not view:
             self.logger.warning(f"Tab changed to index {index} ({tab_name}), but view widget is None.")
             return

        self.logger.debug(f"Tab changed to: {tab_name} (index {index})")

        # Refresh the view when switching to it
        try:
             if index == 1:  # Study tab
                  if hasattr(view, 'refresh_decks'):
                       view.refresh_decks()
             elif index == 2:  # History tab
                  if hasattr(view, 'refresh_history'):
                       view.refresh_history()
        except RuntimeError as e:
             # Catch specific Qt runtime errors that might indicate deleted objects
             self.logger.error(f"Error refreshing tab {tab_name}: {e}")
             QMessageBox.critical(self, "Error", f"Failed to load the {tab_name} tab.\nThe view might have been closed unexpectedly. Please restart the application.")
        except Exception as e:
             # Catch any other unexpected errors
             self.logger.error(f"Unexpected error refreshing tab {tab_name}: {e}", exc_info=True)
             QMessageBox.critical(self, "Error", f"An unexpected error occurred loading the {tab_name} tab.")


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
            self.logger.info("Application closing by user confirmation")
            # Perform any necessary cleanup before accepting exit
            # (e.g., stop background threads if any)
            event.accept() # Allow window to close
        else:
            self.logger.debug("User cancelled application exit")
            event.ignore() # Prevent window from closing
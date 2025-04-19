from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QComboBox,
    QGroupBox, QSplitter, QFrame, QHeaderView,
    QPushButton, QDateEdit, QSizePolicy, QWidget
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from src.ui.widgets.card_list_widget import CardListWidget
from src.utils.logger import get_logger
from src.utils.error_handling import handle_errors
from src.ui.views.responsive_view import ResponsiveView

class HistoryView(ResponsiveView):
    """View for displaying study history and statistics with responsive layout."""
    
    def __init__(self, settings, storage, parent=None):
        super().__init__(settings, storage, parent)
        
        # Setup UI
        self.setup_ui()
        
        self.logger.info("HistoryView initialized")
    
    @handle_errors(dialog_title="UI Error")
    def setup_ui(self):
        """Set up the user interface with responsive design and modern styling."""
        # Main layout
        main_layout = self.keep_reference(QVBoxLayout(self))
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)
        
        # Title
        title_label = QLabel("Study History")
        title_label.setProperty("class", "h1")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        main_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Track your progress and review past study sessions")
        subtitle_label.setProperty("class", "subtitle")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        main_layout.addWidget(subtitle_label)
        
        # Filter controls in a horizontal layout
        filter_container = QGroupBox("Filter Options")
        filter_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        filter_layout = self.keep_reference(QHBoxLayout(filter_container))
        filter_layout.setContentsMargins(16, 24, 16, 16)
        filter_layout.setSpacing(16)
        
        # Deck selector
        deck_label = QLabel("Deck:")
        deck_label.setProperty("class", "form-label")
        deck_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        filter_layout.addWidget(deck_label)
        
        self.deck_combo = QComboBox()
        self.deck_combo.addItem("All Decks", None)
        self.deck_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        filter_layout.addWidget(self.deck_combo)
        
        # Date range
        date_label = QLabel("Date Range:")
        date_label.setProperty("class", "form-label")
        date_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        filter_layout.addWidget(date_label)
        
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        filter_layout.addWidget(self.start_date)
        
        filter_layout.addWidget(QLabel("to"))
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addDays(1))
        self.end_date.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        filter_layout.addWidget(self.end_date)
        
        filter_layout.addStretch(1)
        
        # Refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.setProperty("class", "primary")
        refresh_button.clicked.connect(self.refresh_history)
        refresh_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        filter_layout.addWidget(refresh_button)
        
        # Add filter controls to main layout
        main_layout.addWidget(filter_container)
        
        # Create main vertical splitter
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Statistics section
        stats_frame = QFrame()
        stats_frame.setProperty("class", "stats-container")
        stats_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        stats_layout = self.keep_reference(QVBoxLayout(stats_frame))
        stats_layout.setContentsMargins(16, 16, 16, 16)
        stats_layout.setSpacing(16)
        
        stats_title = QLabel("Study Statistics")
        stats_title.setProperty("class", "h2")
        stats_title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        stats_layout.addWidget(stats_title)
        
        # Statistics table
        self.stats_table = QTableWidget(0, 5)
        self.stats_table.setHorizontalHeaderLabels([
            "Deck", "Cards", "Sessions", "Cards Studied", "Accuracy"
        ])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stats_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.stats_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        stats_layout.addWidget(self.stats_table)
        
        # Create horizontal splitter for sessions and cards
        self.bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.bottom_splitter.setChildrenCollapsible(False)
        self.bottom_splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Sessions section
        sessions_frame = QFrame()
        sessions_frame.setProperty("class", "card")
        sessions_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sessions_layout = self.keep_reference(QVBoxLayout(sessions_frame))
        sessions_layout.setContentsMargins(16, 16, 16, 16)
        sessions_layout.setSpacing(16)
        
        sessions_title = QLabel("Recent Study Sessions")
        sessions_title.setProperty("class", "h2")
        sessions_title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        sessions_layout.addWidget(sessions_title)
        
        # Sessions table
        self.sessions_table = QTableWidget(0, 6)
        self.sessions_table.setHorizontalHeaderLabels([
            "Date", "Time", "Deck", "Duration", "Cards Studied", "Accuracy"
        ])
        self.sessions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sessions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sessions_table.cellClicked.connect(self.on_session_selected)
        self.sessions_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sessions_layout.addWidget(self.sessions_table)
        
        # Cards section for the selected session
        cards_frame = QFrame()
        cards_frame.setProperty("class", "card")
        cards_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        cards_layout = self.keep_reference(QVBoxLayout(cards_frame))
        cards_layout.setContentsMargins(16, 16, 16, 16)
        cards_layout.setSpacing(16)
        
        cards_title = QLabel("Session Cards")
        cards_title.setProperty("class", "h2")
        cards_title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        cards_layout.addWidget(cards_title)
        
        # Card list
        self.session_card_list = CardListWidget(show_toolbar=False, read_only=True)
        self.session_card_list.setProperty("class", "card-list")
        self.session_card_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        cards_layout.addWidget(self.session_card_list)
        
        # Add frames to bottom splitter
        self.bottom_splitter.addWidget(sessions_frame)
        self.bottom_splitter.addWidget(cards_frame)
        
        # Set sizes (60% sessions, 40% cards)
        self.bottom_splitter.setSizes([int(self.width() * 0.6), int(self.width() * 0.4)])
        
        # Add frames to main splitter
        self.main_splitter.addWidget(stats_frame)
        self.main_splitter.addWidget(self.bottom_splitter)
        
        # Set proportions for main splitter (25% stats, 75% detail)
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 3)
        
        # Add main splitter to layout
        main_layout.addWidget(self.main_splitter)
        
        # Connect signals
        self.deck_combo.currentIndexChanged.connect(self.on_filter_changed)
        self.start_date.dateChanged.connect(self.on_filter_changed)
        self.end_date.dateChanged.connect(self.on_filter_changed)
    
    
    def handle_resize(self, width, height):
        """Handle parent window resize to adjust layout dynamically."""
        super().handle_resize(width, height)
        
        # Adjust layout based on available width
        if width < 900:
            # In compact mode, adjust splitter orientation for narrow windows
            if hasattr(self, 'bottom_splitter'):
                if self.bottom_splitter.orientation() != Qt.Orientation.Vertical:
                    # Switch to vertical orientation for narrow screens
                    self.bottom_splitter.setOrientation(Qt.Orientation.Vertical)
                    # Adjust proportions
                    self.bottom_splitter.setSizes([int(height * 0.5), int(height * 0.5)])
        else:
            # In normal mode, maintain horizontal orientation
            if hasattr(self, 'bottom_splitter'):
                if self.bottom_splitter.orientation() != Qt.Orientation.Horizontal:
                    # Switch back to horizontal orientation
                    self.bottom_splitter.setOrientation(Qt.Orientation.Horizontal)
                    # Adjust proportions
                    self.bottom_splitter.setSizes([int(width * 0.6), int(width * 0.4)])
        
        # For very small screens, adjust main splitter proportions
        if height < 600:
            self.main_splitter.setSizes([int(height * 0.3), int(height * 0.7)])
        else:
            self.main_splitter.setSizes([int(height * 0.25), int(height * 0.75)])
    
    def switch_to_compact_mode(self):
        """Switch to compact layout for smaller screens."""
        super().switch_to_compact_mode()
        
        # Simplify filter layout
        self.reorganize_filter_controls()
    
    def switch_to_normal_mode(self):
        """Switch to normal layout for larger screens."""
        super().switch_to_normal_mode()
        
        # Restore standard filter layout
        self.reorganize_filter_controls()
    
    def reorganize_filter_controls(self):
        """Reorganize filter controls based on current mode."""
        # This would involve restructuring the filter_layout
        # In a real implementation, we'd need to remove and re-add widgets
        pass
    
    def refresh_history(self):
        """Refresh the history display with data from storage."""
        self.logger.debug("Refreshing history view")
        
        # Remember current selection
        current_deck_id = self.deck_combo.currentData()
        
        # Refresh deck list
        self.refresh_deck_list()
        
        # Restore filter selection if possible
        if current_deck_id:
            for i in range(self.deck_combo.count()):
                if self.deck_combo.itemData(i) == current_deck_id:
                    self.deck_combo.setCurrentIndex(i)
                    break
        
        # Load data with current filter
        self.load_statistics()
        self.load_sessions()
    
    def refresh_deck_list(self):
        """Refresh the deck filter dropdown."""
        # Remember current selection
        current_deck_id = self.deck_combo.currentData()
        
        # Clear combo box but keep "All Decks" option
        self.deck_combo.clear()
        self.deck_combo.addItem("All Decks", None)
        
        # Get all decks from storage
        decks = self.storage.get_all_decks()
        
        # Add decks to combo box
        for deck in decks:
            self.deck_combo.addItem(deck.name, deck.id)
        
        # Try to restore previous selection
        if current_deck_id:
            for i in range(self.deck_combo.count()):
                if self.deck_combo.itemData(i) == current_deck_id:
                    self.deck_combo.setCurrentIndex(i)
                    return
    
    def on_filter_changed(self):
        """Handle filter selection changed."""
        self.load_statistics()
        self.load_sessions()
        self.session_card_list.clear()
    
    @handle_errors(dialog_title="Data Error")
    def load_statistics(self):
        """Load and display deck statistics."""
        # Get selected deck ID (None for all decks)
        deck_id = self.deck_combo.currentData()
        
        # Clear table
        self.stats_table.setRowCount(0)
        
        # Start and end dates
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        
        # If specific deck is selected, show only that deck
        if deck_id:
            deck = self.storage.get_deck(deck_id)
            if deck:
                stats = self.storage.get_deck_stats(deck_id, start_date, end_date)
                self.add_stats_row(deck, stats)
        else:
            # Show all decks
            decks = self.storage.get_all_decks()
            
            for deck in decks:
                stats = self.storage.get_deck_stats(deck.id, start_date, end_date)
                self.add_stats_row(deck, stats)
    
    def add_stats_row(self, deck, stats):
        """Add a row to the statistics table."""
        row = self.stats_table.rowCount()
        self.stats_table.insertRow(row)
        
        # Deck name
        self.stats_table.setItem(row, 0, QTableWidgetItem(deck.name))
        
        # Card count
        self.stats_table.setItem(row, 1, QTableWidgetItem(str(stats['total_cards'])))
        
        # Session count
        self.stats_table.setItem(row, 2, QTableWidgetItem(str(stats['session_count'])))
        
        # Cards studied
        self.stats_table.setItem(row, 3, QTableWidgetItem(str(stats['total_studied'])))
        
        # Accuracy
        accuracy_text = f"{stats['accuracy']:.1f}%" if stats['total_studied'] > 0 else "N/A"
        accuracy_item = QTableWidgetItem(accuracy_text)
        self.stats_table.setItem(row, 4, accuracy_item)
        
        # Color code by accuracy
        if stats['total_studied'] > 0:
            if stats['accuracy'] >= 80:
                accuracy_item.setBackground(QColor(200, 255, 200))  # Light green
            elif stats['accuracy'] >= 60:
                accuracy_item.setBackground(QColor(255, 255, 200))  # Light yellow
            else:  # < 60%
                accuracy_item.setBackground(QColor(255, 200, 200))  # Light red
    
    @handle_errors(dialog_title="Data Error")
    def load_sessions(self):
        """Load and display study sessions."""
        # Get selected deck ID (None for all decks)
        deck_id = self.deck_combo.currentData()
        
        # Get date range
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        
        # Get study sessions
        sessions = self.storage.get_study_sessions(deck_id, start_date, end_date)
        
        # Clear table
        self.sessions_table.setRowCount(0)
        
        # Add sessions to table
        for session in sessions:
            # Skip incomplete sessions
            if not session.end_time:
                continue
                
            row = self.sessions_table.rowCount()
            self.sessions_table.insertRow(row)
            
            # Store session ID in the item data for retrieval
            for col in range(6):
                self.sessions_table.setItem(row, col, QTableWidgetItem())
                self.sessions_table.item(row, col).setData(Qt.ItemDataRole.UserRole, session.id)
            
            # Get deck name
            deck = self.storage.get_deck(session.deck_id)
            deck_name = deck.name if deck else "Unknown Deck"
            
            # Date (just the date part)
            date_str = session.start_time.strftime("%Y-%m-%d")
            self.sessions_table.item(row, 0).setText(date_str)
            
            # Time (just the time part)
            time_str = session.start_time.strftime("%H:%M")
            self.sessions_table.item(row, 1).setText(time_str)
            
            # Deck name
            self.sessions_table.item(row, 2).setText(deck_name)
            
            # Duration
            duration = session.duration
            if duration:
                minutes = duration.total_seconds() // 60
                seconds = duration.total_seconds() % 60
                duration_str = f"{int(minutes)}m {int(seconds)}s"
            else:
                duration_str = "N/A"
            self.sessions_table.item(row, 3).setText(duration_str)
            
            # Cards studied
            self.sessions_table.item(row, 4).setText(str(session.cards_studied))
            
            # Accuracy
            accuracy = session.accuracy
            accuracy_str = f"{accuracy:.1f}%" if session.cards_studied > 0 else "N/A"
            self.sessions_table.item(row, 5).setText(accuracy_str)
            
            # Color code by accuracy
            if session.cards_studied > 0:
                if accuracy >= 80:
                    self.sessions_table.item(row, 5).setBackground(QColor(200, 255, 200))  # Light green
                elif accuracy >= 60:
                    self.sessions_table.item(row, 5).setBackground(QColor(255, 255, 200))  # Light yellow
                else:  # < 60%
                    self.sessions_table.item(row, 5).setBackground(QColor(255, 200, 200))  # Light red
    
    def on_session_selected(self, row, column):
        """Handle session selection to show cards studied in that session."""
        session_id = self.sessions_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        if not session_id:
            return
        
        # Get the session
        session = self.storage.get_study_session(session_id)
        
        if not session:
            self.session_card_list.clear()
            return
        
        # Get the deck
        deck = self.storage.get_deck(session.deck_id)
        
        if not deck:
            self.session_card_list.clear()
            return
        
        # Show the cards from this deck
        self.session_card_list.clear()
        self.session_card_list.add_cards(deck.cards)
    
    def update_settings(self):
        """Update view based on changed settings."""
        # Check for theme changes
        theme = self.settings.get("theme", "light")
        
        # Apply theme-specific styling to tables
        if theme == "dark":
            # Apply dark theme styling to tables
            self.apply_dark_theme_to_tables()
        else:
            # Apply light theme styling to tables
            self.apply_light_theme_to_tables()

    def apply_dark_theme_to_tables(self):
        """Apply dark theme styling to table widgets."""
        # Example styling - would be integrated with the theme system
        if hasattr(self, 'stats_table'):
            self.stats_table.setStyleSheet(
                "QTableWidget { background-color: #2d2d2d; color: #e0e0e0; }"
                "QHeaderView::section { background-color: #3d3d3d; color: #e0e0e0; }"
            )
        
        if hasattr(self, 'sessions_table'):
            self.sessions_table.setStyleSheet(
                "QTableWidget { background-color: #2d2d2d; color: #e0e0e0; }"
                "QHeaderView::section { background-color: #3d3d3d; color: #e0e0e0; }"
            )

    def apply_light_theme_to_tables(self):
        """Apply light theme styling to table widgets."""
        # Example styling - would be integrated with the theme system
        if hasattr(self, 'stats_table'):
            self.stats_table.setStyleSheet(
                "QTableWidget { background-color: #ffffff; color: #333333; }"
                "QHeaderView::section { background-color: #f0f0f0; color: #333333; }"
            )
        
        if hasattr(self, 'sessions_table'):
            self.sessions_table.setStyleSheet(
                "QTableWidget { background-color: #ffffff; color: #333333; }"
                "QHeaderView::section { background-color: #f0f0f0; color: #333333; }"
            )
# src/ui/views/history_view.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QComboBox,
    QGroupBox, QSplitter, QFrame, QHeaderView,
    QPushButton, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from src.ui.widgets.card_list_widget import CardListWidget
from src.utils.logger import get_logger
from src.utils.error_handling import handle_errors

class HistoryView(QWidget):
    """View for displaying study history and statistics."""
    
    def __init__(self, settings, storage):
        super().__init__()
        self.settings = settings
        self.storage = storage
        self.logger = get_logger(__name__)
        
        # Setup UI
        self.setup_ui()
        
        self.logger.info("HistoryView initialized")
    
    @handle_errors(dialog_title="UI Error")
    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Study History")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Deck selector
        deck_label = QLabel("Deck:")
        self.deck_combo = QComboBox()
        self.deck_combo.addItem("All Decks", None)
        
        filter_layout.addWidget(deck_label)
        filter_layout.addWidget(self.deck_combo)
        
        # Date range
        date_label = QLabel("Date Range:")
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        
        filter_layout.addWidget(date_label)
        filter_layout.addWidget(self.start_date)
        filter_layout.addWidget(QLabel("to"))
        filter_layout.addWidget(self.end_date)
        
        filter_layout.addStretch(1)
        
        # Refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_history)
        filter_layout.addWidget(refresh_button)
        
        main_layout.addLayout(filter_layout)
        
        # Create splitter for statistics, sessions, and cards
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        
        # Statistics section
        stats_frame = QFrame()
        stats_layout = QVBoxLayout(stats_frame)
        
        stats_title = QLabel("Study Statistics")
        stats_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        stats_layout.addWidget(stats_title)
        
        # Statistics table
        self.stats_table = QTableWidget(0, 5)  # rows will be added dynamically
        self.stats_table.setHorizontalHeaderLabels([
            "Deck", "Cards", "Sessions", "Cards Studied", "Accuracy"
        ])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stats_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        stats_layout.addWidget(self.stats_table)
        
        # Create horizontal splitter for sessions and cards
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Sessions section
        sessions_frame = QFrame()
        sessions_layout = QVBoxLayout(sessions_frame)
        
        sessions_title = QLabel("Recent Study Sessions")
        sessions_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        sessions_layout.addWidget(sessions_title)
        
        # Sessions table
        self.sessions_table = QTableWidget(0, 6)  # rows will be added dynamically
        self.sessions_table.setHorizontalHeaderLabels([
            "Date", "Time", "Deck", "Duration", "Cards Studied", "Accuracy"
        ])
        self.sessions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sessions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sessions_table.cellClicked.connect(self.on_session_selected)
        
        sessions_layout.addWidget(self.sessions_table)
        
        # Cards section for the selected session
        cards_frame = QFrame()
        cards_layout = QVBoxLayout(cards_frame)
        
        cards_title = QLabel("Session Cards")
        cards_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        cards_layout.addWidget(cards_title)
        
        # Card list
        self.session_card_list = CardListWidget()
        cards_layout.addWidget(self.session_card_list)
        
        # Add frames to bottom splitter
        bottom_splitter.addWidget(sessions_frame)
        bottom_splitter.addWidget(cards_frame)
        
        # Set sizes (60% sessions, 40% cards)
        bottom_splitter.setSizes([600, 400])
        
        # Add frames to main splitter
        splitter.addWidget(stats_frame)
        splitter.addWidget(bottom_splitter)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
        main_layout.addWidget(splitter)
        
        # Connect signals
        self.deck_combo.currentIndexChanged.connect(self.on_filter_changed)
        self.start_date.dateChanged.connect(self.on_filter_changed)
        self.end_date.dateChanged.connect(self.on_filter_changed)
    
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
        self.stats_table.setItem(row, 4, QTableWidgetItem(accuracy_text))
        
        # Color code by accuracy
        if stats['accuracy'] >= 80:
            self.stats_table.item(row, 4).setBackground(QColor(200, 255, 200))  # Light green
        elif stats['accuracy'] >= 60:
            self.stats_table.item(row, 4).setBackground(QColor(255, 255, 200))  # Light yellow
        elif stats['accuracy'] > 0:
            self.stats_table.item(row, 4).setBackground(QColor(255, 200, 200))  # Light red
    
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
            if accuracy >= 80:
                self.sessions_table.item(row, 5).setBackground(QColor(200, 255, 200))  # Light green
            elif accuracy >= 60:
                self.sessions_table.item(row, 5).setBackground(QColor(255, 255, 200))  # Light yellow
            elif accuracy > 0:
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
        # No specific settings to update here
        pass
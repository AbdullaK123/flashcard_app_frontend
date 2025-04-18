# src/ui/views/history_view.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox,
    QGroupBox, QSplitter, QFrame, QHeaderView,
    QPushButton, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from src.ui.widgets.card_list_widget import CardListWidget #
from src.utils.logger import get_logger #
from src.utils.error_handling import handle_errors #

class HistoryView(QWidget): #
    """View for displaying study history and statistics."""

    def __init__(self, settings, storage): #
        super().__init__()
        self.settings = settings
        self.storage = storage
        self.logger = get_logger(__name__)

        # Setup UI
        self.setup_ui()

        self.logger.info("HistoryView initialized")

    @handle_errors(dialog_title="UI Error") #
    def setup_ui(self): #
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

    def refresh_history(self): #
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

    def refresh_deck_list(self): #
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

    def on_filter_changed(self): #
        """Handle filter selection changed."""
        self.load_statistics()
        self.load_sessions()
        self.session_card_list.clear()

    @handle_errors(dialog_title="Data Error") #
    def load_statistics(self): #
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

    def add_stats_row(self, deck, stats): #
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

        # --- MODIFIED HERE ---
        # Accuracy
        # Directly display the accuracy from stats, which is 0.0 if total_studied is 0
        accuracy_text = f"{stats['accuracy']:.1f}%"
        accuracy_item = QTableWidgetItem(accuracy_text)
        self.stats_table.setItem(row, 4, accuracy_item)

        # Color code by accuracy
        if stats['total_studied'] > 0: # Only color if accuracy is meaningful
            if stats['accuracy'] >= 80:
                accuracy_item.setBackground(QColor(200, 255, 200))  # Light green
            elif stats['accuracy'] >= 60:
                accuracy_item.setBackground(QColor(255, 255, 200))  # Light yellow
            else: # Accuracy < 60%
                accuracy_item.setBackground(QColor(255, 200, 200))  # Light red
        # --- END MODIFICATION ---

    @handle_errors(dialog_title="Data Error") #
    def load_sessions(self): #
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
            session_id_item = QTableWidgetItem() # Create a base item to hold data
            session_id_item.setData(Qt.ItemDataRole.UserRole, session.id)
            # Add this item conceptually to all cells, or retrieve id from row 0
            self.sessions_table.setItem(row, 0, QTableWidgetItem()) # Date item
            self.sessions_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, session.id) # Store ID here too for easy access

            # Get deck name
            deck = self.storage.get_deck(session.deck_id)
            deck_name = deck.name if deck else "Unknown Deck"

            # Date (just the date part)
            date_str = session.start_time.strftime("%Y-%m-%d")
            self.sessions_table.item(row, 0).setText(date_str)

            # Time (just the time part)
            time_str = session.start_time.strftime("%H:%M")
            self.sessions_table.setItem(row, 1, QTableWidgetItem(time_str))

            # Deck name
            self.sessions_table.setItem(row, 2, QTableWidgetItem(deck_name))

            # Duration
            duration = session.duration
            if duration:
                minutes = duration.total_seconds() // 60
                seconds = duration.total_seconds() % 60
                duration_str = f"{int(minutes)}m {int(seconds)}s"
            else:
                duration_str = "N/A" # Should not happen if end_time exists
            self.sessions_table.setItem(row, 3, QTableWidgetItem(duration_str))

            # Cards studied
            self.sessions_table.setItem(row, 4, QTableWidgetItem(str(session.cards_studied)))

            # --- MODIFIED HERE ---
            # Accuracy
            accuracy = session.accuracy # Use the accuracy property from the session model
            accuracy_str = f"{accuracy:.1f}%" # Display the calculated accuracy (which is 0.0 if cards_studied is 0)
            accuracy_item = QTableWidgetItem(accuracy_str)
            self.sessions_table.setItem(row, 5, accuracy_item)

            # Color code by accuracy
            if session.cards_studied > 0: # Only color if accuracy is meaningful
                 if accuracy >= 80:
                     accuracy_item.setBackground(QColor(200, 255, 200))  # Light green
                 elif accuracy >= 60:
                     accuracy_item.setBackground(QColor(255, 255, 200))  # Light yellow
                 else: # Accuracy < 60%
                     accuracy_item.setBackground(QColor(255, 200, 200))  # Light red
            # --- END MODIFICATION ---

    def on_session_selected(self, row, column): #
        """Handle session selection to show cards studied in that session."""
        # Retrieve session ID stored in the first column's item data
        item = self.sessions_table.item(row, 0)
        if not item:
             self.logger.warning(f"No item found at row {row}, column 0 for session selection.")
             return

        session_id = item.data(Qt.ItemDataRole.UserRole)

        if not session_id:
            self.logger.warning(f"No session ID found in item data at row {row}, column 0.")
            return

        # Get the session
        session = self.storage.get_study_session(session_id)

        if not session:
            self.logger.warning(f"Could not retrieve session with ID: {session_id}")
            self.session_card_list.clear()
            return

        # Get the deck
        deck = self.storage.get_deck(session.deck_id)

        if not deck:
            self.logger.warning(f"Could not retrieve deck with ID: {session.deck_id} for session {session_id}")
            self.session_card_list.clear()
            return

        # Show the cards from this deck
        # Note: This shows *all* cards in the deck, not just those *marked* in the session.
        # Displaying only marked cards would require more complex data tracking/storage.
        self.session_card_list.clear()
        self.session_card_list.add_cards(deck.cards)

    def update_settings(self): #
        """Update view based on changed settings."""
        # No specific settings affect this view directly, but method is kept for consistency
        pass
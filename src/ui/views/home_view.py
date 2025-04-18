# src/ui/views/home_view.py
import sys
import asyncio
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QTextEdit, QSpinBox, QProgressBar, QMessageBox,
    QFormLayout, QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QThreadPool, QRunnable, pyqtSlot, QObject

from src.api.client import APIClient
from src.data.models import Flashcard, FlashcardDeck
from src.ui.widgets.card_list_widget import CardListWidget
from src.utils.logger import get_logger
from src.utils.error_handling import handle_errors

# Worker signals for background processing
class WorkerSignals(QObject):
    """Signals for communicating from worker thread."""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

# Worker for background flashcard generation
class GenerateFlashcardsWorker(QRunnable):
    """Worker for generating flashcards in background thread."""
    
    def __init__(self, api_client, topic, num_cards):
        super().__init__()
        self.api_client = api_client
        self.topic = topic
        self.num_cards = num_cards
        self.signals = WorkerSignals()
    
    @pyqtSlot()
    def run(self):
        """Main worker function that runs in background thread."""
        try:
            # Create a new event loop for the thread
            if sys.platform == 'win32':
                loop = asyncio.ProactorEventLoop()
            else:
                loop = asyncio.new_event_loop()
            
            asyncio.set_event_loop(loop)
            
            # Call the API
            response = loop.run_until_complete(
                self.api_client.generate_flashcards(self.topic, self.num_cards)
            )
            
            # Emit response
            self.signals.finished.emit(response)
        except Exception as e:
            self.signals.error.emit(str(e))

class HomeView(QWidget):
    """Home view for creating new flashcards and viewing recent cards."""
    
    # Signal emitted when a new deck is created
    deck_created = pyqtSignal(str)  # Emits deck ID
    
    def __init__(self, settings, storage):
        super().__init__()
        self.settings = settings
        self.storage = storage
        self.logger = get_logger(__name__)
        
        # Create API client
        api_url = self.settings.get("api_url", "http://localhost:8000")
        self.api_client = APIClient(api_url)
        
        # Create thread pool for background tasks
        self.thread_pool = QThreadPool()
        
        # Setup UI
        self.setup_ui()
        
        # Load recent cards
        self.load_recent_cards()
        
        self.logger.info("HomeView initialized")
    
    @handle_errors(dialog_title="UI Error")
    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create a splitter to divide the view
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # --- Top section for card generation ---
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel("Create New Flashcards")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        top_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(
            "Enter a topic and our AI will generate flashcards to help you study."
            " The AI uses web search to ensure accurate, up-to-date information."
        )
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(desc_label)
        
        # Form group
        form_group = QGroupBox("Flashcard Generator")
        form_layout = QFormLayout()
        form_group.setLayout(form_layout)
        
        # Topic input
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("e.g., Python Programming, French Revolution, Quantum Physics")
        form_layout.addRow("Topic:", self.topic_input)
        
        # Number of cards
        self.num_cards_input = QSpinBox()
        self.num_cards_input.setMinimum(5)
        self.num_cards_input.setMaximum(40)  # Limit to 40 cards
        self.num_cards_input.setValue(10)
        self.num_cards_input.setSingleStep(5)
        form_layout.addRow("Number of cards:", self.num_cards_input)
        
        # Additional notes
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Any specific areas to focus on? (optional)")
        self.notes_input.setMaximumHeight(100)
        form_layout.addRow("Additional notes:", self.notes_input)
        
        top_layout.addWidget(form_group)
        
        # Progress area
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(False)
        top_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setVisible(False)
        top_layout.addWidget(self.status_label)
        
        # Button area
        button_layout = QHBoxLayout()
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_form)
        button_layout.addWidget(self.clear_button)
        
        # Generate button
        self.generate_button = QPushButton("Generate Flashcards")
        self.generate_button.clicked.connect(self.generate_flashcards)
        self.generate_button.setDefault(True)
        button_layout.addWidget(self.generate_button)
        
        top_layout.addLayout(button_layout)
        
        # --- Bottom section for recent cards ---
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        # Recent cards label
        recent_cards_label = QLabel("Recent Flashcards")
        recent_cards_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        bottom_layout.addWidget(recent_cards_label)
        
        # Card list widget
        self.card_list = CardListWidget()
        self.card_list.card_selected.connect(self.preview_card)
        self.card_list.edit_requested.connect(self.edit_card)
        self.card_list.delete_requested.connect(self.delete_card)
        bottom_layout.addWidget(self.card_list)
        
        # Add widgets to splitter
        splitter.addWidget(top_widget)
        splitter.addWidget(bottom_widget)
        
        # Set initial sizes (60% top, 40% bottom)
        splitter.setSizes([600, 400])
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
    
    def clear_form(self):
        """Clear all input fields."""
        self.topic_input.clear()
        self.num_cards_input.setValue(10)
        self.notes_input.clear()
        self.topic_input.setFocus()
    
    def start_new_deck(self):
        """Method that can be called from outside to start new deck creation."""
        self.clear_form()
        self.topic_input.setFocus()
    
    @handle_errors(dialog_title="Generation Error")
    def generate_flashcards(self, checked=None):
        """Generate flashcards using the API."""
        # Get input values
        topic = self.topic_input.text().strip()
        num_cards = self.num_cards_input.value()
        notes = self.notes_input.toPlainText().strip()
        
        # Validate input
        if not topic:
            QMessageBox.warning(
                self, 
                "Missing Topic", 
                "Please enter a topic for the flashcards."
            )
            self.topic_input.setFocus()
            return
        
        # Add notes to topic if provided
        if notes:
            topic = f"{topic}\n\nAdditional focus areas: {notes}"
        
        # Show progress UI
        self.progress_bar.setVisible(True)
        self.status_label.setText("Generating flashcards... This may take up to a minute.")
        self.status_label.setVisible(True)
        self.generate_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        
        # Create worker for background processing
        worker = GenerateFlashcardsWorker(self.api_client, topic, num_cards)
        
        # Connect signals
        worker.signals.finished.connect(self.on_generation_complete)
        worker.signals.error.connect(self.on_generation_error)
        
        # Start worker
        self.thread_pool.start(worker)
        
        self.logger.info(f"Started flashcard generation for '{topic}' with {num_cards} cards")
    
    @handle_errors(dialog_title="Processing Error")
    def on_generation_complete(self, response):
        """Handle successful flashcard generation."""
        if not response or not response.cards:
            self.on_generation_error("No flashcards were generated. Please try again.")
            return
        
        # Create a new deck from the response
        deck = FlashcardDeck.create(
            name=response.topic,
            description=f"Flashcards about {response.topic}"
        )
        
        # Add cards to the deck
        for card_data in response.cards:
            card = Flashcard.create(
                question=card_data.question,
                answer=card_data.answer,
                topic=response.topic
            )
            deck.add_card(card)
        
        # Save the deck
        self.storage.save_deck(deck)
        
        # Reset UI
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        self.generate_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.clear_form()
        
        # Refresh recent cards
        self.load_recent_cards()
        
        # Show success message
        QMessageBox.information(
            self,
            "Flashcards Generated",
            f"Successfully created {len(response.cards)} flashcards on '{response.topic}'.\n\n"
            f"Switch to the Study tab to start learning!"
        )
        
        # Emit signal that a new deck was created
        self.deck_created.emit(deck.id)
    
    def on_generation_error(self, error_message):
        """Handle error during flashcard generation."""
        # Reset UI
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        self.generate_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        
        # Show error message
        QMessageBox.critical(
            self,
            "Generation Failed",
            f"Failed to generate flashcards: {error_message}\n\n"
            f"Please check your internet connection and try again."
        )
    
    def load_recent_cards(self):
        """Load and display recently created cards."""
        self.logger.debug("Loading recent cards")
        
        # Clear current list
        self.card_list.clear()
        
        # Get all decks ordered by creation date
        decks = self.storage.get_all_decks()
        
        # Get recent cards (up to 50 cards from newest decks)
        recent_cards = []
        for deck in sorted(decks, key=lambda d: d.created_at, reverse=True):
            recent_cards.extend(deck.cards)
            if len(recent_cards) >= 50:
                break
        
        # Sort by creation date and take most recent 50
        recent_cards.sort(key=lambda c: c.created_at, reverse=True)
        recent_cards = recent_cards[:50]
        
        # Add to card list
        self.card_list.add_cards(recent_cards)
    
    def preview_card(self, card_id):
        """Preview a card when it's selected in the list."""
        # This could show card details in a separate area
        pass
    
    @handle_errors(dialog_title="Edit Error")
    def edit_card(self, card_id):
        """Edit a flashcard."""
        # Find the card in storage
        for deck in self.storage.get_all_decks():
            for card in deck.cards:
                if card.id == card_id:
                    # Show edit dialog (would need to create this dialog)
                    from src.ui.dialogs.edit_card_dialog import EditCardDialog
                    dialog = EditCardDialog(card, self)
                    if dialog.exec():
                        # Update card and save
                        updated_card = dialog.get_updated_card()
                        self.storage.save_card(updated_card, deck.id)
                        self.card_list.update_card(updated_card)
                        self.logger.info(f"Card {card_id} updated")
                    return
        
        self.logger.warning(f"Card {card_id} not found for editing")
    
    @handle_errors(dialog_title="Delete Error")
    def delete_card(self, card_id):
        """Delete a flashcard."""
        # Ask for confirmation
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this flashcard?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Delete from storage
        result = self.storage.delete_card(card_id)
        
        if result:
            # Remove from UI
            self.card_list.remove_card(card_id)
            self.logger.info(f"Card {card_id} deleted")
        else:
            self.logger.warning(f"Failed to delete card {card_id}")
    
    def update_settings(self):
        """Update view based on changed settings."""
        # Get updated settings
        api_url = self.settings.get("api_url", "http://localhost:8000")
        api_timeout = self.settings.get("api_timeout", 60)
        
        # Update API client
        self.api_client = APIClient(base_url=api_url, timeout=api_timeout)
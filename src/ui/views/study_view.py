# src/ui/views/study_view.py
import random
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QStackedWidget, QMessageBox, QProgressBar,
    QGroupBox, QFrame, QSplitter, QSizePolicy, QWidget,
    QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from src.data.models import StudySession, Flashcard
from src.ui.widgets.flashcard_widget import FlashcardWidget
from src.ui.widgets.card_list_widget import CardListWidget
from src.utils.logger import get_logger
from src.utils.error_handling import handle_errors
from src.ui.views.responsive_view import ResponsiveView

class StudyView(ResponsiveView):
    """View for studying flashcards with responsive layout."""
    
    # Signal when study session is completed
    study_completed = pyqtSignal(str, int, int)  # deck_id, cards_studied, cards_correct
    
    def __init__(self, settings, storage, parent=None):
        super().__init__(settings, storage, parent)
        
        # Study session state
        self.current_deck = None
        self.current_session = None
        self.cards = []
        self.current_index = 0
        self.cards_studied = 0
        self.cards_correct = 0
        
        # Setup UI
        self.setup_ui()
        
        self.logger.info("StudyView initialized")
    
    @handle_errors(dialog_title="UI Error")
    def setup_ui(self):
        """Set up the user interface with responsive layouts."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create stacked widget for different screens
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # --- 1. Deck Selection Screen ---
        deck_selection_widget = QWidget()
        deck_layout = QVBoxLayout(deck_selection_widget)
        
        # Title with responsive styling
        deck_title = QLabel("Study Flashcards")
        deck_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        deck_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        deck_title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        deck_layout.addWidget(deck_title)
        
        # Create a splitter for deck selection and preview
        self.selection_splitter = QSplitter(Qt.Orientation.Vertical)
        self.selection_splitter.setChildrenCollapsible(False)
        self.selection_splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Deck selection section
        deck_selection_widget = QWidget()
        deck_selection_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        deck_selection_layout = QVBoxLayout(deck_selection_widget)
        
        # Deck selection group box
        deck_group = QGroupBox("Select a Deck to Study")
        deck_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        deck_group_layout = QVBoxLayout(deck_group)
        
        # Controls in horizontal layout with responsive spacing
        deck_controls = QHBoxLayout()
        
        self.deck_combo = QComboBox()
        self.deck_combo.setMinimumWidth(300)
        self.deck_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        deck_controls.addWidget(self.deck_combo, 3)  # 75% of space
        
        self.start_button = QPushButton("Start Studying")
        self.start_button.clicked.connect(self.start_study_session)
        self.start_button.setEnabled(False)
        self.start_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        deck_controls.addWidget(self.start_button, 1)  # 25% of space
        
        deck_group_layout.addLayout(deck_controls)
        deck_selection_layout.addWidget(deck_group)
        
        # Description of selected deck
        self.deck_description = QLabel()
        self.deck_description.setWordWrap(True)
        self.deck_description.setStyleSheet("font-style: italic; color: #666;")
        self.deck_description.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        deck_selection_layout.addWidget(self.deck_description)
        
        # Preview section
        preview_widget = QWidget()
        preview_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        preview_layout = QVBoxLayout(preview_widget)
        
        # Card list with ability to add/edit cards
        self.preview_card_list = CardListWidget()
        self.preview_card_list.set_title("Cards in this Deck")
        self.preview_card_list.create_requested.connect(self.create_new_card)
        self.preview_card_list.edit_requested.connect(self.edit_card)
        self.preview_card_list.delete_requested.connect(self.delete_card)
        self.preview_card_list.card_selected.connect(self.preview_card)
        self.preview_card_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        preview_layout.addWidget(self.preview_card_list)
        
        # Add widgets to splitter
        self.selection_splitter.addWidget(deck_selection_widget)
        self.selection_splitter.addWidget(preview_widget)
        
        # Default size proportion (40% top, 60% bottom)
        self.selection_splitter.setSizes([400, 600])
        
        deck_layout.addWidget(self.selection_splitter)
        
        # --- 2. Study Screen ---
        study_widget = QWidget()
        study_layout = QVBoxLayout(study_widget)
        
        # Create splitter for flashcard and card list (side by side)
        self.study_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.study_splitter.setChildrenCollapsible(False)
        self.study_splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Left side - flashcard area
        flashcard_widget = QWidget()
        flashcard_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.flashcard_layout = QVBoxLayout(flashcard_widget)
        
        # Deck info
        self.deck_info_label = QLabel()
        self.deck_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.deck_info_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.deck_info_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.flashcard_layout.addWidget(self.deck_info_label)
        
        # Progress
        progress_layout = QHBoxLayout()
        
        self.progress_label = QLabel("Card 0 of 0")
        self.progress_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        progress_layout.addWidget(self.progress_bar)
        
        self.flashcard_layout.addLayout(progress_layout)
        
        # Flashcard widget (will auto-scale)
        self.flashcard_widget = FlashcardWidget()
        self.flashcard_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.flashcard_widget.card_flipped.connect(self.on_card_flipped)
        self.flashcard_layout.addWidget(self.flashcard_widget)
        
        # Control buttons in responsive grid layout
        self.controls_layout = QHBoxLayout()
        
        # Add flexible spacing around buttons
        self.controls_layout.addStretch(1)
        
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.show_previous_card)
        self.prev_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.controls_layout.addWidget(self.prev_button)
        
        self.controls_layout.addStretch(1)
        
        self.flip_button = QPushButton("Flip Card")
        self.flip_button.clicked.connect(self.flashcard_widget.flip_card)
        self.flip_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.controls_layout.addWidget(self.flip_button)
        
        self.correct_button = QPushButton("Mark Correct")
        self.correct_button.setStyleSheet("background-color: #34A853; color: white;")
        self.correct_button.clicked.connect(lambda: self.mark_card(True))
        self.correct_button.setVisible(False)
        self.correct_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.controls_layout.addWidget(self.correct_button)
        
        self.incorrect_button = QPushButton("Mark Incorrect")
        self.incorrect_button.setStyleSheet("background-color: #EA4335; color: white;")
        self.incorrect_button.clicked.connect(lambda: self.mark_card(False))
        self.incorrect_button.setVisible(False)
        self.incorrect_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.controls_layout.addWidget(self.incorrect_button)
        
        self.controls_layout.addStretch(1)
        
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.show_next_card)
        self.next_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.controls_layout.addWidget(self.next_button)
        
        self.controls_layout.addStretch(1)
        
        self.flashcard_layout.addLayout(self.controls_layout)
        
        # End button
        end_layout = QHBoxLayout()
        end_layout.addStretch(1)
        self.end_button = QPushButton("End Study Session")
        self.end_button.clicked.connect(self.end_study_session)
        self.end_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        end_layout.addWidget(self.end_button)
        end_layout.addStretch(1)
        
        self.flashcard_layout.addLayout(end_layout)
        
        # Right side - card list
        self.study_card_list = CardListWidget(show_toolbar=False, read_only=True)
        self.study_card_list.set_title("Cards in Session")
        self.study_card_list.card_selected.connect(self.go_to_card)
        self.study_card_list.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        
        # Add both sides to splitter
        self.study_splitter.addWidget(flashcard_widget)
        self.study_splitter.addWidget(self.study_card_list)
        
        # Set initial sizes (70% flashcard, 30% list)
        self.study_splitter.setSizes([700, 300])
        
        study_layout.addWidget(self.study_splitter)
        
        # --- 3. Results Screen ---
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        
        results_title = QLabel("Study Session Complete")
        results_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        results_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        results_title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        results_layout.addWidget(results_title)
        
        # Results box
        results_group = QGroupBox("Your Results")
        results_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        results_group_layout = QVBoxLayout(results_group)
        
        self.results_label = QLabel()
        self.results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results_label.setStyleSheet("font-size: 16px;")
        self.results_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        results_group_layout.addWidget(self.results_label)
        
        results_layout.addWidget(results_group)
        
        # Session cards
        session_cards_group = QGroupBox("Cards in This Session")
        session_cards_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        session_cards_layout = QVBoxLayout(session_cards_group)
        
        self.results_card_list = CardListWidget(show_toolbar=False, read_only=True)
        self.results_card_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        session_cards_layout.addWidget(self.results_card_list)
        
        results_layout.addWidget(session_cards_group)
        
        # Buttons
        results_buttons = QHBoxLayout()
        results_buttons.addStretch(1)
        
        self.restart_button = QPushButton("Study Again")
        self.restart_button.clicked.connect(self.restart_session)
        self.restart_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        results_buttons.addWidget(self.restart_button)
        
        results_buttons.addSpacing(20)  # Add space between buttons
        
        self.finish_button = QPushButton("Return to Deck Selection")
        self.finish_button.clicked.connect(self.return_to_deck_selection)
        self.finish_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        results_buttons.addWidget(self.finish_button)
        
        results_buttons.addStretch(1)
        
        results_layout.addLayout(results_buttons)
        
        # Add all screens to stacked widget
        self.stacked_widget.addWidget(deck_selection_widget)  # Index 0
        self.stacked_widget.addWidget(study_widget)           # Index 1
        self.stacked_widget.addWidget(results_widget)         # Index 2
        
        # Add stacked widget to main layout
        main_layout.addWidget(self.stacked_widget)
        
        # Connect signals
        self.deck_combo.currentIndexChanged.connect(self.on_deck_selected)
    
    def handle_resize(self, width, height):
        """Handle parent window resize to adjust layout dynamically."""
        super().handle_resize(width, height)
        
        # Adjust layout based on available width
        if width < 900:
            # Hide card list in study mode in narrow windows
            if hasattr(self, 'study_splitter') and self.stacked_widget.currentIndex() == 1:
                # Give more space to the flashcard
                self.study_splitter.setSizes([width, 0])
        else:
            # Show card list in normal width
            if hasattr(self, 'study_splitter') and self.stacked_widget.currentIndex() == 1:
                # Use standard 70/30 split
                self.study_splitter.setSizes([int(width * 0.7), int(width * 0.3)])
    
    def handle_maximized(self):
        """Handle window being maximized."""
        super().handle_maximized()
        
        # Make adjustments specific to maximized state
        if hasattr(self, 'flashcard_widget'):
            # For maximized windows, adjust flashcard size for optimal reading
            self.flashcard_widget.setMinimumHeight(400)
            
        # Ensure proper splitter proportions
        if hasattr(self, 'study_splitter') and self.stacked_widget.currentIndex() == 1:
            self.study_splitter.setSizes([int(self.current_width * 0.7), int(self.current_width * 0.3)])
    
    def handle_normal(self):
        """Handle window returning to normal size."""
        super().handle_normal()
        
        # Restore normal settings
        if hasattr(self, 'flashcard_widget'):
            self.flashcard_widget.setMinimumHeight(250)
    
    def switch_to_compact_mode(self):
        """Switch to compact layout for smaller screens."""
        super().switch_to_compact_mode()
        
        # For narrow screens, reorganize controls to vertical layout
        if hasattr(self, 'controls_layout'):
            # Clear existing layout
            while self.controls_layout.count():
                item = self.controls_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            
            # Re-add in more compact arrangement
            self.controls_layout.addWidget(self.prev_button)
            self.controls_layout.addWidget(self.next_button)
            self.controls_layout.addWidget(self.flip_button)
            self.controls_layout.addWidget(self.correct_button)
            self.controls_layout.addWidget(self.incorrect_button)
    
    def switch_to_normal_mode(self):
        """Switch to normal layout for larger screens."""
        super().switch_to_normal_mode()
        
        # Restore normal control layout
        if hasattr(self, 'controls_layout'):
            # Clear existing layout
            while self.controls_layout.count():
                item = self.controls_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            
            # Re-add in original arrangement
            self.controls_layout.addStretch(1)
            self.controls_layout.addWidget(self.prev_button)
            self.controls_layout.addStretch(1)
            self.controls_layout.addWidget(self.flip_button)
            self.controls_layout.addWidget(self.correct_button)
            self.controls_layout.addWidget(self.incorrect_button)
            self.controls_layout.addStretch(1)
            self.controls_layout.addWidget(self.next_button)
            self.controls_layout.addStretch(1)
    
    def refresh_decks(self):
        """Refresh the deck list from storage."""
        self.logger.debug("Refreshing decks list")
        
        # Remember current selection if any
        current_id = self.deck_combo.currentData() if self.deck_combo.count() > 0 else None
        
        # Clear the combo box
        self.deck_combo.clear()
        
        # Get all decks from storage
        decks = self.storage.get_all_decks()
        
        if not decks:
            self.deck_combo.addItem("No decks available", None)
            self.start_button.setEnabled(False)
            self.preview_card_list.clear()
            self.deck_description.setText("Create a deck of flashcards to start studying")
            return
        
        # Add decks to combo box
        selected_index = 0
        for i, deck in enumerate(decks):
            # Load the complete deck to get card count
            full_deck = self.storage.get_deck(deck.id)
            card_count = len(full_deck.cards) if full_deck else 0
            self.deck_combo.addItem(f"{deck.name} ({card_count} cards)", deck.id)
            
            # If this was the previously selected deck, remember its index
            if deck.id == current_id:
                selected_index = i
        
        # Restore previous selection if possible
        if current_id and selected_index < self.deck_combo.count():
            self.deck_combo.setCurrentIndex(selected_index)
        else:
            # Otherwise select first item and trigger selection
            self.deck_combo.setCurrentIndex(0)
            self.on_deck_selected(0)
    
    def select_deck(self, deck_id):
        """Select a specific deck by ID."""
        for i in range(self.deck_combo.count()):
            if self.deck_combo.itemData(i) == deck_id:
                self.deck_combo.setCurrentIndex(i)
                return True
        return False
    
    def on_deck_selected(self, index):
        """Handle deck selection."""
        deck_id = self.deck_combo.itemData(index)
        self.start_button.setEnabled(deck_id is not None)
        
        # Update preview
        self.preview_card_list.clear()
        
        if deck_id:
            # Load deck with cards
            deck = self.storage.get_deck(deck_id)
            if deck:
                self.deck_description.setText(deck.description or "No description provided.")
                
                if deck.cards:
                    # Show cards in preview
                    self.preview_card_list.add_cards(deck.cards)
                else:
                    self.deck_description.setText(f"{deck.description or 'No description provided.'}\n\nThis deck has no cards yet. Add some cards to start studying.")
        else:
            self.deck_description.setText("")
    
    @handle_errors(dialog_title="Study Error")
    def start_study_session(self, checked=None):
        """Start a new study session with the selected deck."""
        deck_id = self.deck_combo.currentData()
        if not deck_id:
            return
        
        # Load the selected deck with all its cards
        self.current_deck = self.storage.get_deck(deck_id)
        if not self.current_deck or not self.current_deck.cards:
            QMessageBox.warning(
                self,
                "Empty Deck",
                "This deck doesn't have any cards. Please add cards first."
            )
            return
        
        # Create a new study session
        self.current_session = StudySession.create(self.current_deck.id)
        
        # Reset counters
        self.cards_studied = 0
        self.cards_correct = 0
        
        # Get all cards and shuffle them if setting enabled
        self.cards = self.current_deck.cards.copy()
        if self.settings.get("shuffle_cards", True):
            random.shuffle(self.cards)
        
        # Reset to first card
        self.current_index = 0
        
        # Update UI for study mode
        self.deck_info_label.setText(f"Studying: {self.current_deck.name}")
        self.update_progress()
        
        # Show the cards in the list
        self.study_card_list.clear()
        self.study_card_list.add_cards(self.cards)
        
        # Show the first card
        self.show_current_card()
        
        # Switch to study screen
        self.stacked_widget.setCurrentIndex(1)
        
        # Apply appropriate layout for current window size
        self.handle_resize(self.current_width, self.current_height)
        
        self.logger.info(f"Started study session for deck: {self.current_deck.name}")
    
    def update_progress(self):
        """Update the progress display."""
        # Update card count display
        total_cards = len(self.cards)
        current_number = self.current_index + 1 if total_cards > 0 else 0
        self.progress_label.setText(f"Card {current_number} of {total_cards}")
        
        # Update progress bar
        if total_cards > 0:
            progress = (self.current_index / total_cards) * 100
            self.progress_bar.setValue(int(progress))
    
    def show_current_card(self):
        """Show the current card."""
        if not self.cards or self.current_index >= len(self.cards):
            return
        
        # Get the current card
        card = self.cards[self.current_index]
        
        # Update the flashcard widget
        self.flashcard_widget.set_card(card.question, card.answer)
        
        # Update navigation buttons
        self.prev_button.setEnabled(self.current_index > 0)
        self.next_button.setEnabled(self.current_index < len(self.cards) - 1)
        
        # Reset marking buttons visibility
        self.correct_button.setVisible(False)
        self.incorrect_button.setVisible(False)
        self.flip_button.setVisible(True)
        
        # Update progress
        self.update_progress()
        
        # Highlight the current card in the list
        self.study_card_list.highlight_card(card.id)
    
    def show_previous_card(self):
        """Show the previous card."""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_card()
    
    def show_next_card(self):
        """Show the next card."""
        if self.current_index < len(self.cards) - 1:
            self.current_index += 1
            self.show_current_card()
    
    def go_to_card(self, card_id):
        """Go to a specific card by ID."""
        for i, card in enumerate(self.cards):
            if card.id == card_id:
                self.current_index = i
                self.show_current_card()
                break
    
    def on_card_flipped(self, is_flipped):
        """Handle card being flipped."""
        # Show the marking buttons when card is flipped to answer side
        self.correct_button.setVisible(is_flipped)
        self.incorrect_button.setVisible(is_flipped)
        self.flip_button.setVisible(not is_flipped)
    
    @handle_errors(dialog_title="Study Error")
    def mark_card(self, is_correct):
        """Mark the current card as correct or incorrect."""
        if not self.cards or self.current_index >= len(self.cards):
            return
        
        # Get the current card
        card = self.cards[self.current_index]
        
        # Mark as reviewed
        card.mark_reviewed()
        
        # Update the card in storage
        self.storage.save_card(card, self.current_deck.id)
        
        # Track statistics
        self.cards_studied += 1
        if is_correct:
            self.cards_correct += 1
        
        # Move to next card if available
        if self.current_index < len(self.cards) - 1:
            self.current_index += 1
            self.show_current_card()
        else:
            # All cards done
            self.end_study_session()
    
    @handle_errors(dialog_title="Study Error")
    def end_study_session(self):
        """End the current study session."""
        if not self.current_session:
            return
        
        # Complete the session
        self.current_session.complete(self.cards_studied, self.cards_correct)
        
        # Save session to storage
        self.storage.save_study_session(self.current_session)
        
        # Update deck's last studied time
        self.current_deck.update_last_studied()
        self.storage.save_deck(self.current_deck)
        
        # Calculate results
        accuracy = 0
        if self.cards_studied > 0:
            accuracy = (self.cards_correct / self.cards_studied) * 100
        
        # Update results display
        self.results_label.setText(
            f"Cards Studied: {self.cards_studied} of {len(self.cards)}\n"
            f"Correct Answers: {self.cards_correct}\n"
            f"Accuracy: {accuracy:.1f}%"
        )
        
        # Show cards in the results screen
        self.results_card_list.clear()
        self.results_card_list.add_cards(self.cards)
        
        # Switch to results screen
        self.stacked_widget.setCurrentIndex(2)
        
        # Emit signal about completed session
        self.study_completed.emit(
            self.current_deck.id, 
            self.cards_studied, 
            self.cards_correct
        )
        
        self.logger.info(
            f"Study session completed: {self.cards_studied} cards studied, "
            f"{self.cards_correct} correct, {accuracy:.1f}% accuracy"
        )
    
    def restart_session(self):
        """Restart studying the same deck."""
        if not self.current_deck:
            return
        
        # Get the deck ID and restart
        deck_id = self.current_deck.id
        self.return_to_deck_selection()
        self.select_deck(deck_id)
        self.start_study_session()
    
    def return_to_deck_selection(self):
        """Return to the deck selection screen."""
        # Reset session state
        self.current_deck = None
        self.current_session = None
        self.cards = []
        self.current_index = 0
        self.cards_studied = 0
        self.cards_correct = 0
        
        # Refresh decks to get latest data
        self.refresh_decks()
        
        # Switch to deck selection screen
        self.stacked_widget.setCurrentIndex(0)
    
    def preview_card(self, card_id):
        """Preview a card when selected in the list."""
        card = self.preview_card_list.get_card(card_id)
        if card:
            QMessageBox.information(
                self,
                "Card Preview",
                f"Question:\n{card.question}\n\nAnswer:\n{card.answer}"
            )
    
    @handle_errors(dialog_title="Create Error")
    def create_new_card(self):
        """Create a new flashcard."""
        # Get current deck
        deck_id = self.deck_combo.currentData()
        if not deck_id:
            QMessageBox.warning(
                self,
                "No Deck Selected",
                "Please select a deck first."
            )
            return
        
        # Get deck name
        deck_name = self.deck_combo.currentText().split(" (")[0]
        
        # Show dialog
        from src.ui.dialogs.new_card_dialog import NewCardDialog
        dialog = NewCardDialog(deck_id, deck_name, self)
        
        if dialog.exec():
            # Get the new card
            card = dialog.get_new_card()
            if card:
                # Save to storage
                self.storage.save_card(card, deck_id)
                
                # Refresh card list in the preview
                self.on_deck_selected(self.deck_combo.currentIndex())
                
                # Update display in combo box
                current_text = self.deck_combo.currentText()
                count_part = current_text.split("(")[1].split(" ")[0]
                new_count = int(count_part) + 1
                new_text = f"{deck_name} ({new_count} cards)"
                self.deck_combo.setItemText(self.deck_combo.currentIndex(), new_text)
                
                # Show confirmation
                QMessageBox.information(
                    self,
                    "Card Created",
                    "The new flashcard has been added to the deck."
                )
    
    @handle_errors(dialog_title="Edit Error")
    def edit_card(self, card_id):
        """Edit a flashcard."""
        # Find the card in storage (needs deck context)
        deck_id = self.deck_combo.currentData()
        if not deck_id:
            self.logger.warning("Edit card requested but no deck selected.")
            return
            
        # Get the deck for this card
        deck = self.storage.get_deck(deck_id)
        if not deck:
            self.logger.warning(f"Deck {deck_id} not found for editing.")
            return
            
        # Find the card in the deck
        card = None
        for c in deck.cards:
            if c.id == card_id:
                card = c
                break
                
        if not card:
            self.logger.warning(f"Card {card_id} not found for editing in deck {deck_id}.")
            return
            
        # Show edit dialog
        from src.ui.dialogs.edit_card_dialog import EditCardDialog
        dialog = EditCardDialog(card, self)
        if dialog.exec():
            # Update card and save
            updated_card = dialog.get_updated_card()
            self.storage.save_card(updated_card, deck_id)
            
            # Update in the preview list
            self.preview_card_list.update_card(updated_card)
            
            # Show confirmation
            QMessageBox.information(
                self,
                "Card Updated",
                "The flashcard has been updated successfully."
            )
    
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
        
        # Get current deck
        deck_id = self.deck_combo.currentData()
        if not deck_id:
            self.logger.warning("Delete card requested but no deck selected.")
            return
        
        # Delete from storage
        result = self.storage.delete_card(card_id)
        
        if result:
            # Remove from preview list
            self.preview_card_list.remove_card(card_id)
            
            # Update display in combo box
            current_text = self.deck_combo.currentText()
            count_part = current_text.split("(")[1].split(" ")[0]
            new_count = max(0, int(count_part) - 1)
            deck_name = current_text.split(" (")[0]
            new_text = f"{deck_name} ({new_count} cards)"
            self.deck_combo.setItemText(self.deck_combo.currentIndex(), new_text)
            
            # Show confirmation
            QMessageBox.information(
                self,
                "Card Deleted",
                "The flashcard has been deleted successfully."
            )
        else:
            self.logger.warning(f"Failed to delete card {card_id} from storage.")
            QMessageBox.warning(
                self,
                "Delete Failed",
                "Failed to delete the flashcard from storage. Please check logs."
            )
    
    def update_settings(self):
        """Update view based on changed settings."""
        # Apply any settings changes that affect the study view
        # e.g., shuffle setting, card display preferences
        
        # Check for theme changes that might affect card display
        theme = self.settings.get("theme", "light")
        if hasattr(self, 'flashcard_widget'):
            # Update flashcard styling based on theme
            if theme == "dark":
                self.flashcard_widget.card_frame.setStyleSheet("background-color: #3a3a3a; color: #e0e0e0;")
            else:
                self.flashcard_widget.card_frame.setStyleSheet("background-color: white; color: #333333;")
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
        main_layout = self.keep_reference(QVBoxLayout(self))
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Create stacked widget for different screens
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # --- 1. Deck Selection Screen ---
        deck_selection_widget = QWidget()
        deck_layout = self.keep_reference(QVBoxLayout(deck_selection_widget))

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
        deck_selection_sub_widget = QWidget() # Renamed local variable
        deck_selection_sub_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        deck_selection_layout = self.keep_reference(QVBoxLayout(deck_selection_sub_widget)) # Parent layout to renamed widget

        # Deck selection group box
        deck_group = QGroupBox("Select a Deck to Study")
        deck_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        deck_group_layout = self.keep_reference(QVBoxLayout(deck_group))

        # Controls in horizontal layout with responsive spacing
        deck_controls = self.keep_reference(QHBoxLayout())

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
        preview_layout = self.keep_reference(QVBoxLayout(preview_widget))

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
        self.selection_splitter.addWidget(deck_selection_sub_widget) # Use renamed widget
        self.selection_splitter.addWidget(preview_widget)

        # Default size proportion (40% top, 60% bottom)
        self.selection_splitter.setSizes([400, 600])

        deck_layout.addWidget(self.selection_splitter)

        # --- 2. Study Screen ---
        study_widget = QWidget()
        study_layout = self.keep_reference(QVBoxLayout(study_widget))

        # Create splitter for flashcard and card list (side by side)
        self.study_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.study_splitter.setChildrenCollapsible(False)
        self.study_splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Left side - flashcard area
        flashcard_area_widget = QWidget() # Renamed local variable
        flashcard_area_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.flashcard_layout = self.keep_reference(QVBoxLayout(flashcard_area_widget)) # Parent layout to renamed widget

        # Deck info
        self.deck_info_label = QLabel()
        self.deck_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.deck_info_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.deck_info_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.flashcard_layout.addWidget(self.deck_info_label)

        # Progress
        progress_layout = self.keep_reference(QHBoxLayout())

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
        self.controls_layout = self.keep_reference(QHBoxLayout())

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
        end_layout = self.keep_reference(QHBoxLayout())
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
        self.study_splitter.addWidget(flashcard_area_widget) # Use renamed widget
        self.study_splitter.addWidget(self.study_card_list)

        # Set initial sizes (70% flashcard, 30% list)
        self.study_splitter.setSizes([700, 300])

        study_layout.addWidget(self.study_splitter)

        # --- 3. Results Screen ---
        results_widget = QWidget()
        results_layout = self.keep_reference(QVBoxLayout(results_widget))
        print(f"DEBUG: StudyView results_layout valid after creation: {results_layout is not None}") # <-- ADDED PRINT

        results_title = QLabel("Study Session Complete")
        results_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        results_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        results_title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        results_layout.addWidget(results_title)

        # Results box
        results_group = QGroupBox("Your Results")
        results_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        results_group_layout = self.keep_reference(QVBoxLayout(results_group))
        print(f"DEBUG: StudyView results_group_layout valid after creation: {results_group_layout is not None}") # <-- ADDED PRINT

        self.results_label = QLabel()
        self.results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results_label.setStyleSheet("font-size: 16px;")
        self.results_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        results_group_layout.addWidget(self.results_label)

        results_layout.addWidget(results_group)

        # Session cards
        session_cards_group = QGroupBox("Cards in This Session")
        session_cards_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        session_cards_layout = self.keep_reference(QVBoxLayout(session_cards_group))
        print(f"DEBUG: StudyView session_cards_layout valid after creation: {session_cards_layout is not None}") # <-- ADDED PRINT

        self.results_card_list = CardListWidget(show_toolbar=False, read_only=True)
        self.results_card_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        session_cards_layout.addWidget(self.results_card_list)

        results_layout.addWidget(session_cards_group)

        # Buttons
        results_buttons = self.keep_reference(QHBoxLayout())
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
        if hasattr(self, 'study_splitter'): # Check if splitter exists
            if width < 900:
                # Hide card list in study mode in narrow windows
                if self.stacked_widget.currentIndex() == 1:
                    # Give more space to the flashcard
                    self.study_splitter.setSizes([width, 0])
            else:
                # Show card list in normal width
                if self.stacked_widget.currentIndex() == 1:
                    # Use standard 70/30 split
                    current_splitter_width = self.study_splitter.width() # Get current width
                    if current_splitter_width > 0: # Avoid division by zero
                        self.study_splitter.setSizes([int(current_splitter_width * 0.7), int(current_splitter_width * 0.3)])
                    else: # Fallback if width is zero
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
             splitter_width = self.study_splitter.width()
             if splitter_width > 0:
                self.study_splitter.setSizes([int(splitter_width * 0.7), int(splitter_width * 0.3)])
             else: # Fallback using current view width
                self.study_splitter.setSizes([int(self.current_width * 0.7), int(self.current_width * 0.3)])


    def handle_normal(self):
        """Handle window returning to normal size."""
        super().handle_normal()

        # Restore normal settings
        if hasattr(self, 'flashcard_widget'):
            self.flashcard_widget.setMinimumHeight(250) # Restore default minimum height

        # Recalculate splitter sizes based on normal window width
        if hasattr(self, 'study_splitter') and self.stacked_widget.currentIndex() == 1:
             splitter_width = self.study_splitter.width()
             if splitter_width > 0:
                self.study_splitter.setSizes([int(splitter_width * 0.7), int(splitter_width * 0.3)])
             else: # Fallback using current view width
                 self.study_splitter.setSizes([int(self.current_width * 0.7), int(self.current_width * 0.3)])


    def switch_to_compact_mode(self):
        """Switch to compact layout for smaller screens."""
        if not hasattr(self, 'controls_layout'): # Guard against calls before setup_ui completes
             return
        super().switch_to_compact_mode()

        # For narrow screens, reorganize controls to vertical layout
        # Temporarily store widgets
        widgets_to_move = []
        while self.controls_layout.count():
            item = self.controls_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widgets_to_move.append(widget)
            elif item.spacerItem():
                pass # Discard spacers

        # Re-add in more compact arrangement (simple vertical stack)
        for widget in widgets_to_move:
             if widget in [self.prev_button, self.next_button, self.flip_button, self.correct_button, self.incorrect_button]:
                  self.controls_layout.addWidget(widget)


    def switch_to_normal_mode(self):
        """Switch to normal layout for larger screens."""
        if not hasattr(self, 'controls_layout'): # Guard against calls before setup_ui completes
             return
        super().switch_to_normal_mode()

        # Restore normal control layout
        # Temporarily store widgets
        widgets_to_move = []
        while self.controls_layout.count():
            item = self.controls_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widgets_to_move.append(widget)

        # Create dictionary for easier access
        widget_map = {
            "prev": self.prev_button,
            "next": self.next_button,
            "flip": self.flip_button,
            "correct": self.correct_button,
            "incorrect": self.incorrect_button
        }

        # Re-add in original arrangement with stretches
        self.controls_layout.addStretch(1)
        if widget_map["prev"] in widgets_to_move: self.controls_layout.addWidget(widget_map["prev"])
        self.controls_layout.addStretch(1)
        if widget_map["flip"] in widgets_to_move: self.controls_layout.addWidget(widget_map["flip"])
        if widget_map["correct"] in widgets_to_move: self.controls_layout.addWidget(widget_map["correct"])
        if widget_map["incorrect"] in widgets_to_move: self.controls_layout.addWidget(widget_map["incorrect"])
        self.controls_layout.addStretch(1)
        if widget_map["next"] in widgets_to_move: self.controls_layout.addWidget(widget_map["next"])
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
            # Manually trigger on_deck_selected if index didn't change but content might have
            if self.deck_combo.currentIndex() == selected_index:
                 self.on_deck_selected(selected_index)
        elif self.deck_combo.count() > 0:
            # Otherwise select first item and trigger selection
            self.deck_combo.setCurrentIndex(0)
            self.on_deck_selected(0)
        else:
             # Handle case where decks became empty after refresh
             self.on_deck_selected(-1) # Pass invalid index


    def select_deck(self, deck_id):
        """Select a specific deck by ID."""
        for i in range(self.deck_combo.count()):
            if self.deck_combo.itemData(i) == deck_id:
                self.deck_combo.setCurrentIndex(i)
                return True
        return False

    def on_deck_selected(self, index):
        """Handle deck selection."""
        if index < 0 or index >= self.deck_combo.count(): # Check for invalid index
             deck_id = None
             self.deck_description.setText("")
             self.preview_card_list.clear()
             self.start_button.setEnabled(False)
             return

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
                 # Deck ID exists but couldn't be loaded (error?)
                 self.deck_description.setText("Error loading deck details.")
                 self.start_button.setEnabled(False) # Disable start if deck fails to load
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
            # Progress should be based on cards *viewed* not just index if non-linear
            # Using index for now as simple progress indicator
            progress = ((self.current_index + 1) / total_cards) * 100
            self.progress_bar.setValue(int(progress))
        else:
            self.progress_bar.setValue(0)


    def show_current_card(self):
        """Show the current card."""
        if not self.cards or not (0 <= self.current_index < len(self.cards)):
            # Handle edge case where index might be out of bounds after deletion/modification
            self.logger.warning("show_current_card called with invalid index or empty cards.")
            # Optionally switch back to deck selection or show an error
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
        self.flip_button.setVisible(True) # Always show flip button initially

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
        if not self.cards or not (0 <= self.current_index < len(self.cards)):
             self.logger.warning("mark_card called with invalid index or empty cards.")
             return

        # Get the current card
        card = self.cards[self.current_index]

        # Mark as reviewed
        card.mark_reviewed()

        # Update the card in storage
        # Need deck_id - ensure self.current_deck is valid
        if not self.current_deck:
             self.logger.error("Cannot save reviewed card: current_deck is None.")
             QMessageBox.critical(self, "Internal Error", "Cannot save card review status. Deck information missing.")
             return
        self.storage.save_card(card, self.current_deck.id)

        # Track statistics
        self.cards_studied += 1
        if is_correct:
            self.cards_correct += 1

        # Optional: Auto-flip back if setting enabled? (Not implemented here)

        # Move to next card if available
        if self.current_index < len(self.cards) - 1:
            # Auto-advance setting check could go here
            self.show_next_card() # Use show_next_card to handle index increment
        else:
            # All cards done
            self.end_study_session()


    @handle_errors(dialog_title="Study Error")
    def end_study_session(self, checked=None):
        """End the current study session."""
        if not self.current_session or not self.current_deck:
             self.logger.warning("Attempted to end session, but no active session or deck found.")
             # Maybe force return to deck selection if state is inconsistent
             self.return_to_deck_selection()
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
        # Use the cards list from the session (self.cards) which might be shuffled
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
            # If something went wrong, just go back to selection
            self.return_to_deck_selection()
            return

        # Get the deck ID and restart
        deck_id = self.current_deck.id
        # Reset internal state without clearing combo box selection yet
        # Reset session state before potentially starting a new one
        self.current_session = None
        self.cards = []
        self.current_index = 0
        self.cards_studied = 0
        self.cards_correct = 0

        # Ensure the correct deck is still selected in the combo
        if self.select_deck(deck_id):
             # Start new session directly
             self.start_study_session()
        else:
             # If deck somehow disappeared, go back to selection screen
             self.logger.warning(f"Could not find deck {deck_id} to restart session.")
             self.return_to_deck_selection()


    def return_to_deck_selection(self):
        """Return to the deck selection screen."""
        # Reset session state
        self.current_deck = None
        self.current_session = None
        self.cards = []
        self.current_index = 0
        self.cards_studied = 0
        self.cards_correct = 0

        # Refresh decks to get latest data (might re-select current if still exists)
        self.refresh_decks()

        # Switch to deck selection screen
        self.stacked_widget.setCurrentIndex(0)

    def preview_card(self, card_id):
        """Preview a card when selected in the list."""
        # Use preview_card_list, not study_card_list
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
        # Get current deck from combo box
        deck_id = self.deck_combo.currentData()
        if not deck_id:
            QMessageBox.warning(
                self,
                "No Deck Selected",
                "Please select a deck first."
            )
            return

        # Get deck name from combo box text
        deck_name_with_count = self.deck_combo.currentText()
        deck_name = deck_name_with_count.split(" (")[0] if " (" in deck_name_with_count else deck_name_with_count


        # Show dialog
        from src.ui.dialogs.new_card_dialog import NewCardDialog
        dialog = NewCardDialog(deck_id, deck_name, self)

        if dialog.exec():
            # Get the new card
            card = dialog.get_new_card()
            if card:
                # Save to storage
                self.storage.save_card(card, deck_id)

                # Refresh card list in the preview ONLY (don't reload entire deck list)
                self.preview_card_list.add_card(card) # Directly add to preview

                # Update card count in combo box
                current_text = self.deck_combo.currentText()
                try:
                     count_part = current_text.split("(")[1].split(" ")[0]
                     new_count = int(count_part) + 1
                     new_text = f"{deck_name} ({new_count} cards)"
                     self.deck_combo.setItemText(self.deck_combo.currentIndex(), new_text)
                except (IndexError, ValueError):
                     self.logger.warning(f"Could not parse card count from '{current_text}' to update.")
                     # Fallback: Refresh the whole deck list if parsing fails
                     self.refresh_decks()


                # Show confirmation
                QMessageBox.information(
                    self,
                    "Card Created",
                    "The new flashcard has been added to the deck."
                )

    @handle_errors(dialog_title="Edit Error")
    def edit_card(self, card_id):
        """Edit a flashcard from the preview list."""
        # Find the card in the preview list's data
        card = self.preview_card_list.get_card(card_id)

        if not card:
            self.logger.warning(f"Card {card_id} not found in preview list for editing.")
            return

        # Get the deck context (assuming the currently selected deck is correct)
        deck_id = self.deck_combo.currentData()
        if not deck_id:
            self.logger.warning("Edit card requested but no deck selected.")
            return

        # Show edit dialog
        from src.ui.dialogs.edit_card_dialog import EditCardDialog
        dialog = EditCardDialog(card, self) # Pass the existing card object
        if dialog.exec():
            # Card object was modified in place by the dialog if accepted
            updated_card = dialog.get_updated_card()

            # Save changes to storage
            self.storage.save_card(updated_card, deck_id)

            # Update in the preview list display
            self.preview_card_list.update_card(updated_card)

            # Show confirmation
            QMessageBox.information(
                self,
                "Card Updated",
                "The flashcard has been updated successfully."
            )


    @handle_errors(dialog_title="Delete Error")
    def delete_card(self, card_id):
        """Delete a flashcard from the preview list."""
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

        # Get current deck from combo box
        deck_id = self.deck_combo.currentData()
        if not deck_id:
            self.logger.warning("Delete card requested but no deck selected.")
            return

        # Delete from storage
        result = self.storage.delete_card(card_id)

        if result:
            # Remove from preview list visually
            self.preview_card_list.remove_card(card_id)

            # Update card count display in combo box
            current_text = self.deck_combo.currentText()
            try:
                 deck_name = current_text.split(" (")[0]
                 count_part = current_text.split("(")[1].split(" ")[0]
                 new_count = max(0, int(count_part) - 1) # Ensure count doesn't go below 0
                 new_text = f"{deck_name} ({new_count} cards)"
                 self.deck_combo.setItemText(self.deck_combo.currentIndex(), new_text)
            except (IndexError, ValueError):
                 self.logger.warning(f"Could not parse card count from '{current_text}' to update after delete.")
                 # Fallback: Refresh the whole deck list if parsing fails
                 self.refresh_decks()


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
            # More robust theme handling might involve stylesheets or specific methods
            # Keeping simple background color change for now
            if theme == "dark":
                # Example: Use theme variables if available
                bg_color = self.theme_manager.variables.get("dark", {}).get("background", "#3a3a3a")
                fg_color = self.theme_manager.variables.get("dark", {}).get("foreground", "#e0e0e0")
                border_color = self.theme_manager.variables.get("dark", {}).get("border", "#555555")
                # Apply to card_frame specifically if general theme isn't enough
                # self.flashcard_widget.card_frame.setStyleSheet(f"background-color: {bg_color}; color: {fg_color}; border: 1px solid {border_color};")
            else:
                bg_color = self.theme_manager.variables.get("light", {}).get("background", "white")
                fg_color = self.theme_manager.variables.get("light", {}).get("foreground", "#333333")
                border_color = self.theme_manager.variables.get("light", {}).get("border", "#cccccc")
                # self.flashcard_widget.card_frame.setStyleSheet(f"background-color: {bg_color}; color: {fg_color}; border: 1px solid {border_color};")
            # Note: Theme application is primarily handled by ThemeManager applying stylesheets.
            # This direct styling might be redundant or conflict if not managed carefully.
            pass # Rely on ThemeManager stylesheet updates primarily
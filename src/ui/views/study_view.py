# src/ui/views/study_view.py
import random
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QStackedWidget, QMessageBox, QProgressBar,
    QGroupBox, QFrame, QSplitter, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from src.data.models import StudySession, Flashcard     #
from src.ui.widgets.flashcard_widget import FlashcardWidget #
from src.ui.widgets.card_list_widget import CardListWidget #
from src.utils.logger import get_logger                 #
from src.utils.error_handling import handle_errors      #

class StudyView(QWidget):                               #
    """View for studying flashcards."""

    # Signal when study session is completed
    # deck_id, cards_studied, cards_correct
    study_completed = pyqtSignal(str, int, int)

    def __init__(self, settings, storage):              #
        super().__init__()
        self.settings = settings
        self.storage = storage
        self.logger = get_logger(__name__)

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
    def setup_ui(self):                                 #
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Create stacked widget for different screens
        self.stacked_widget = QStackedWidget()

        # --- 1. Deck Selection Screen ---
        # STORE reference to this screen widget
        self.deck_selection_screen_widget = QWidget()
        deck_layout = QVBoxLayout(self.deck_selection_screen_widget)

        deck_title = QLabel("Study Flashcards")
        deck_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        deck_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        deck_layout.addWidget(deck_title)

        # Create a splitter for deck selection and preview
        # STORE reference to this splitter
        self.selection_splitter = QSplitter(Qt.Orientation.Vertical)

        # Deck selection section (container widget)
        # STORE reference to this container widget
        self.deck_selection_container_widget = QWidget()
        deck_selection_layout = QVBoxLayout(self.deck_selection_container_widget)

        deck_group = QGroupBox("Select a Deck to Study")
        deck_group_layout = QVBoxLayout(deck_group)
        deck_controls = QHBoxLayout()
        self.deck_combo = QComboBox()
        self.deck_combo.setMinimumWidth(300)
        self.start_button = QPushButton("Start Studying")
        # Connect with the corrected signature in mind (from previous fix)
        self.start_button.clicked.connect(self.start_study_session)
        self.start_button.setEnabled(False)
        deck_controls.addWidget(self.deck_combo)
        deck_controls.addWidget(self.start_button)
        deck_group_layout.addLayout(deck_controls)
        deck_selection_layout.addWidget(deck_group)

        self.deck_description = QLabel()
        self.deck_description.setWordWrap(True)
        self.deck_description.setStyleSheet("font-style: italic; color: #666;")
        deck_selection_layout.addWidget(self.deck_description)

        # Preview section (container widget)
        # STORE reference to this container widget
        self.preview_container_widget = QWidget()
        preview_layout = QVBoxLayout(self.preview_container_widget)

        self.preview_card_list = CardListWidget()
        self.preview_card_list.set_title("Cards in this Deck")
        self.preview_card_list.create_requested.connect(self.create_new_card)
        self.preview_card_list.edit_requested.connect(self.edit_card)
        self.preview_card_list.delete_requested.connect(self.delete_card)
        self.preview_card_list.card_selected.connect(self.preview_card)
        preview_layout.addWidget(self.preview_card_list)

        # Add container widgets to the splitter (using stored refs)
        self.selection_splitter.addWidget(self.deck_selection_container_widget)
        self.selection_splitter.addWidget(self.preview_container_widget)
        self.selection_splitter.setSizes([400, 600])

        deck_layout.addWidget(self.selection_splitter) # Add stored splitter

        # --- 2. Study Screen ---
        # STORE reference to this screen widget
        self.study_screen_widget = QWidget()
        study_layout = QVBoxLayout(self.study_screen_widget)

        # Create splitter for flashcard and card list
        # STORE reference to this splitter
        self.study_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side - flashcard area (container widget)
        # STORE reference to this container widget
        self.flashcard_container_widget = QWidget()
        flashcard_layout = QVBoxLayout(self.flashcard_container_widget)

        self.deck_info_label = QLabel()
        self.deck_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.deck_info_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        flashcard_layout.addWidget(self.deck_info_label)

        # Progress
        progress_layout = QHBoxLayout()

        # --- MODIFIED HERE ---
        # Assign the QLabel instance to self.progress_label
        self.progress_label = QLabel("Card 0 of 0")
        # Add the instance variable to the layout
        progress_layout.addWidget(self.progress_label)
        # --- END MODIFICATION ---

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        flashcard_layout.addLayout(progress_layout)


        self.flashcard_widget = FlashcardWidget()
        self.flashcard_widget.card_flipped.connect(self.on_card_flipped)
        flashcard_layout.addWidget(self.flashcard_widget)

        # Control buttons
        controls_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.show_previous_card)
        controls_layout.addWidget(self.prev_button)

        self.flip_button = QPushButton("Flip Card")
        self.flip_button.clicked.connect(self.flashcard_widget.flip_card)
        controls_layout.addWidget(self.flip_button)

        self.correct_button = QPushButton("Mark Correct")
        self.correct_button.setStyleSheet("background-color: #34A853; color: white;")
        self.correct_button.clicked.connect(lambda: self.mark_card(True))
        self.correct_button.setVisible(False)
        controls_layout.addWidget(self.correct_button)

        self.incorrect_button = QPushButton("Mark Incorrect")
        self.incorrect_button.setStyleSheet("background-color: #EA4335; color: white;")
        self.incorrect_button.clicked.connect(lambda: self.mark_card(False))
        self.incorrect_button.setVisible(False)
        controls_layout.addWidget(self.incorrect_button)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.show_next_card)
        controls_layout.addWidget(self.next_button)

        flashcard_layout.addLayout(controls_layout)

        # End button
        end_layout = QHBoxLayout()
        self.end_button = QPushButton("End Study Session")
        self.end_button.clicked.connect(self.end_study_session)
        end_layout.addStretch(1)
        end_layout.addWidget(self.end_button)
        end_layout.addStretch(1)
        flashcard_layout.addLayout(end_layout)

        # Right side - card list
        self.study_card_list = CardListWidget(show_toolbar=False, read_only=True)
        self.study_card_list.set_title("Cards in Session")
        self.study_card_list.card_selected.connect(self.go_to_card)

        # Add container widgets to the splitter (using stored refs)
        self.study_splitter.addWidget(self.flashcard_container_widget)
        self.study_splitter.addWidget(self.study_card_list)
        self.study_splitter.setSizes([700, 300])

        study_layout.addWidget(self.study_splitter) # Add stored splitter

        # --- 3. Results Screen ---
        # STORE reference to this screen widget
        self.results_screen_widget = QWidget()
        results_layout = QVBoxLayout(self.results_screen_widget)

        results_title = QLabel("Study Session Complete")
        results_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        results_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        results_layout.addWidget(results_title)

        results_group = QGroupBox("Your Results")
        results_group_layout = QVBoxLayout(results_group)
        self.results_label = QLabel()
        self.results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results_label.setStyleSheet("font-size: 16px;")
        results_group_layout.addWidget(self.results_label)
        results_layout.addWidget(results_group)

        session_cards_group = QGroupBox("Cards in This Session")
        session_cards_layout = QVBoxLayout(session_cards_group)
        self.results_card_list = CardListWidget(show_toolbar=False, read_only=True)
        session_cards_layout.addWidget(self.results_card_list)
        results_layout.addWidget(session_cards_group)

        results_buttons = QHBoxLayout()
        self.restart_button = QPushButton("Study Again")
        self.restart_button.clicked.connect(self.restart_session)
        results_buttons.addWidget(self.restart_button)
        self.finish_button = QPushButton("Return to Deck Selection")
        self.finish_button.clicked.connect(self.return_to_deck_selection)
        results_buttons.addWidget(self.finish_button)
        results_layout.addLayout(results_buttons)


        # Add all screen widgets (using stored refs) to stacked widget
        self.stacked_widget.addWidget(self.deck_selection_screen_widget) # Index 0
        self.stacked_widget.addWidget(self.study_screen_widget)          # Index 1
        self.stacked_widget.addWidget(self.results_screen_widget)        # Index 2

        # Add stacked widget to main layout
        main_layout.addWidget(self.stacked_widget)

        # Connect signals
        self.deck_combo.currentIndexChanged.connect(self.on_deck_selected)

    def refresh_decks(self):                            #
        """Refresh the deck list from storage."""
        self.logger.debug("Refreshing decks list")

        # Remember current selection if any
        # Handle potential RuntimeError if combo box was deleted somehow (defensive)
        try:
            current_id = self.deck_combo.currentData() if self.deck_combo.count() > 0 else None
            self.deck_combo.clear() # Clear after getting data
        except RuntimeError as e:
            self.logger.error(f"Error accessing deck_combo in refresh_decks: {e}")
            # Attempt to recreate or handle gracefully? For now, just log and return.
            # Might need to re-initialize part of the UI if this happens.
            return

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
            # Use card_count property from model if available, otherwise query storage
            # Assuming get_deck_stats returns necessary info or have a separate count method
            # For now, just show name; card count requires loading deck or separate query
            # Let's try getting count from the list widget if it's populated for the preview
            # Better: modify get_all_decks to include count if efficient
            # Simplest: Just show name for now. Card count is tricky here without loading all.
            deck_name_display = f"{deck.name}"
            # To show count, would need: card_count = len(self.storage.get_deck(deck.id).cards) # Inefficient
            # Or add count method to storage: card_count = self.storage.get_deck_card_count(deck.id)
            # deck_name_display = f"{deck.name} ({card_count} cards)"

            self.deck_combo.addItem(deck_name_display, deck.id)

            if deck.id == current_id:
                selected_index = i

        # Restore previous selection if possible
        if current_id and selected_index < self.deck_combo.count():
            self.deck_combo.setCurrentIndex(selected_index)
        else:
            # Otherwise select first item and trigger selection if decks exist
            if self.deck_combo.count() > 0:
                self.deck_combo.setCurrentIndex(0)
                self.on_deck_selected(0) # Trigger preview update for first item


    def select_deck(self, deck_id):                     #
        """Select a specific deck by ID."""
        for i in range(self.deck_combo.count()):
            if self.deck_combo.itemData(i) == deck_id:
                self.deck_combo.setCurrentIndex(i)
                return True
        return False

    def on_deck_selected(self, index):                  #
        """Handle deck selection."""
        deck_id = self.deck_combo.itemData(index)
        self.start_button.setEnabled(deck_id is not None)

        # Update preview
        self.preview_card_list.clear()
        self.deck_description.setText("") # Clear previous description

        if deck_id:
            # Load deck with cards
            deck = self.storage.get_deck(deck_id)
            if deck:
                self.deck_description.setText(deck.description if deck.description else "No description provided.")

                if deck.cards:
                    # Show cards in preview
                    self.preview_card_list.add_cards(deck.cards)
                    # Update combo text with actual count
                    current_text = self.deck_combo.itemText(index)
                    if f"({len(deck.cards)} cards)" not in current_text:
                         self.deck_combo.setItemText(index, f"{deck.name} ({len(deck.cards)} cards)")
                else:
                    desc = deck.description if deck.description else "No description provided."
                    self.deck_description.setText(f"{desc}\n\nThis deck has no cards yet. Add some cards to start studying.")
                    # Update combo text with 0 count
                    self.deck_combo.setItemText(index, f"{deck.name} (0 cards)")
            else:
                 self.logger.warning(f"Could not load deck with ID: {deck_id}")
                 self.deck_description.setText("Error loading deck details.")
                 self.start_button.setEnabled(False)

    @handle_errors(dialog_title="Study Error")
    # MODIFIED SIGNATURE (previous fix)
    def start_study_session(self, checked=None):        #
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
        self.update_progress() # Call progress update here

        # Show the cards in the list
        self.study_card_list.clear()
        self.study_card_list.add_cards(self.cards)

        # Show the first card
        self.show_current_card()

        # Switch to study screen
        self.stacked_widget.setCurrentIndex(1)

        self.logger.info(f"Started study session for deck: {self.current_deck.name}")

    def update_progress(self):                          #
        """Update the progress display."""
        # Update card count display
        total_cards = len(self.cards)
        current_number = self.current_index + 1 if total_cards > 0 else 0
        # Use self.progress_label (now correctly assigned)
        self.progress_label.setText(f"Card {current_number} of {total_cards}")

        # Update progress bar
        if total_cards > 0:
            # Ensure progress calculation avoids division by zero if index somehow matches total
            # (e.g., if called after last card is marked)
            progress_index = min(self.current_index, total_cards - 1)
            progress = ((progress_index + 1) / total_cards) * 100 # Show progress based on completing current card
            self.progress_bar.setValue(int(progress))
        else:
            self.progress_bar.setValue(0)


    def show_current_card(self):                        #
        """Show the current card."""
        if not self.cards or not (0 <= self.current_index < len(self.cards)):
            self.logger.warning("Attempted to show card with invalid index or empty list.")
            # Handle gracefully, maybe show an empty state or return to selection?
            # For now, just return to avoid errors.
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
        self.study_card_list.list_widget.clearSelection()
        # Find item by card ID
        items = self.study_card_list.list_widget.findItems(card.question[:50], Qt.MatchFlag.MatchStartsWith) # Fragile match
        target_item = None
        for i in range(self.study_card_list.list_widget.count()):
             item = self.study_card_list.list_widget.item(i)
             if item.data(Qt.ItemDataRole.UserRole) == card.id:
                 target_item = item
                 break
        if target_item:
            self.study_card_list.list_widget.setCurrentItem(target_item)


    def show_previous_card(self):                       #
        """Show the previous card."""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_card()

    def show_next_card(self):                           #
        """Show the next card."""
        if self.current_index < len(self.cards) - 1:
            self.current_index += 1
            self.show_current_card()

    def go_to_card(self, card_id):                      #
        """Go to a specific card by ID."""
        for i, card in enumerate(self.cards):
            if card.id == card_id:
                self.current_index = i
                self.show_current_card()
                break

    def on_card_flipped(self, is_flipped):              #
        """Handle card being flipped."""
        # Show the marking buttons when card is flipped to answer side
        self.correct_button.setVisible(is_flipped)
        self.incorrect_button.setVisible(is_flipped)
        self.flip_button.setVisible(not is_flipped)

    @handle_errors(dialog_title="Study Error")
    def mark_card(self, is_correct):                    #
        """Mark the current card as correct or incorrect."""
        if not self.cards or not (0 <= self.current_index < len(self.cards)):
             self.logger.warning("Attempted to mark card with invalid index or empty list.")
             return

        # Get the current card
        card = self.cards[self.current_index]

        # Mark as reviewed
        card.mark_reviewed()

        # Update the card in storage
        if not self.storage.save_card(card, self.current_deck.id):
             self.logger.error(f"Failed to save reviewed status for card {card.id}")
             # Optionally inform user

        # Track statistics
        # Only count as studied if it wasn't already reviewed in *this specific session*?
        # Current logic counts every mark action as studying. Assume this is intended.
        self.cards_studied += 1
        if is_correct:
            self.cards_correct += 1

        # Auto-flip back? - Check setting
        auto_flip_back = self.settings.get("auto_flip_back_after_mark", False) # Example setting
        if auto_flip_back and self.flashcard_widget.is_flipped:
             self.flashcard_widget.flip_card() # Flip back to question

        # Move to next card if available
        if self.current_index < len(self.cards) - 1:
            self.current_index += 1
            self.show_current_card()
        else:
            # All cards done for this pass
            self.logger.info("Reached end of cards in study session.")
            self.end_study_session() # End the session

    @handle_errors(dialog_title="Study Error")
    def end_study_session(self):                        #
        """End the current study session."""
        if not self.current_session or not self.current_deck:
            self.logger.warning("Attempted to end session without active session/deck.")
            # Go back to selection if called unexpectedly
            self.return_to_deck_selection()
            return

        self.logger.info(f"Ending study session for deck: {self.current_deck.name}")

        # Complete the session - ensure cards_studied reflects unique cards?
        # Current logic uses count of marks. Let's assume that's ok for now.
        self.current_session.complete(self.cards_studied, self.cards_correct)

        # Save session to storage
        if not self.storage.save_study_session(self.current_session):
             self.logger.error(f"Failed to save study session {self.current_session.id}")
             # Optionally inform user

        # Update deck's last studied time (only if session was saved)
        if self.current_session.end_time: # Ensure completion was successful
            self.current_deck.update_last_studied()
            if not self.storage.save_deck(self.current_deck):
                self.logger.error(f"Failed to update last_studied time for deck {self.current_deck.id}")
                # Optionally inform user

        # Calculate results
        accuracy = self.current_session.accuracy # Use property from session model

        # Update results display
        self.results_label.setText(
            f"Cards Marked: {self.cards_studied}\n" # Changed label from "Studied"
            f"Correct Answers: {self.cards_correct}\n"
            f"Accuracy: {accuracy:.1f}%"
        )

        # Show cards in the results screen (using the order they were studied in?)
        # self.cards currently holds the shuffled order used in the session
        self.results_card_list.clear()
        self.results_card_list.add_cards(self.cards)

        # Switch to results screen
        self.stacked_widget.setCurrentIndex(2)

        # Emit signal about completed session
        self.study_completed.emit(
            self.current_deck.id,
            self.cards_studied, # Send count of marks
            self.cards_correct
        )

        self.logger.info(
            f"Study session completed: {self.cards_studied} marks, "
            f"{self.cards_correct} correct, {accuracy:.1f}% accuracy"
        )
        # Clear current session state variables *after* processing is done
        # Moved reset to return_to_deck_selection


    def restart_session(self):                          #
        """Restart studying the same deck."""
        if not self.current_deck:
            # If somehow called without a deck, go back to selection
            self.return_to_deck_selection()
            return

        # Get the deck ID and restart
        deck_id = self.current_deck.id
        self.logger.info(f"Restarting study session for deck: {deck_id}")
        # Reset state first
        self.return_to_deck_selection()
        # Reselect deck (triggers on_deck_selected)
        if self.select_deck(deck_id):
            # Start study session again
            self.start_study_session()
        else:
            self.logger.error(f"Could not re-select deck {deck_id} for restart.")


    def return_to_deck_selection(self):                 #
        """Return to the deck selection screen."""
        self.logger.debug("Returning to deck selection screen.")
        # Reset session state
        self.current_deck = None
        self.current_session = None
        self.cards = []
        self.current_index = 0
        self.cards_studied = 0
        self.cards_correct = 0

        # Refresh decks to get latest data (especially card counts)
        self.refresh_decks()

        # Switch to deck selection screen
        self.stacked_widget.setCurrentIndex(0)

    def preview_card(self, card_id):                    #
        """Preview a card when selected in the list."""
        # Find the card in the currently loaded preview list's data
        card = self.preview_card_list.cards.get(card_id)

        if card:
            # Show preview in a message box
             QMessageBox.information(
                 self,
                 "Card Preview",
                 f"Question:\n{card.question}\n\nAnswer:\n{card.answer}"
             )
        else:
             self.logger.warning(f"Card ID {card_id} not found in preview list for preview.")


    @handle_errors(dialog_title="Create Error")
    def create_new_card(self):                          #
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
        deck_name = self.deck_combo.currentText().split(" (")[0] # Robustness? Assumes format

        # Show dialog
        from src.ui.dialogs.new_card_dialog import NewCardDialog # Keep import local
        dialog = NewCardDialog(deck_id, deck_name, self)

        if dialog.exec():
            # Get the new card
            card = dialog.get_new_card()
            if card:
                # Save to storage
                if self.storage.save_card(card, deck_id):
                    self.logger.info(f"New card {card.id} created for deck {deck_id}")
                    # Refresh card list in the preview
                    self.on_deck_selected(self.deck_combo.currentIndex())
                    # Show confirmation
                    QMessageBox.information(
                        self,
                        "Card Created",
                        "The new flashcard has been added to the deck."
                    )
                else:
                    self.logger.error(f"Failed to save new card for deck {deck_id}")
                    QMessageBox.critical(self, "Error", "Failed to save the new card.")


    @handle_errors(dialog_title="Edit Error")
    def edit_card(self, card_id):                       #
        """Edit a flashcard."""
        # Find the card in storage (needs deck context)
        deck_id = self.deck_combo.currentData()
        if not deck_id:
            self.logger.warning("Edit card requested but no deck selected.")
            return

        # Get the specific card object (maybe directly from preview list?)
        card = self.preview_card_list.cards.get(card_id)

        if not card:
            self.logger.warning(f"Card {card_id} not found for editing in preview list.")
            # Fallback: try loading from storage, though less efficient
            deck = self.storage.get_deck(deck_id)
            if deck:
                 for c in deck.cards:
                     if c.id == card_id:
                         card = c
                         break
            if not card:
                 self.logger.error(f"Card {card_id} not found for editing even after storage check.")
                 QMessageBox.warning(self, "Not Found", "Could not find the selected card to edit.")
                 return

        # Show edit dialog
        from src.ui.dialogs.edit_card_dialog import EditCardDialog # Keep import local
        dialog = EditCardDialog(card, self) # Pass the found card object
        if dialog.exec():
            # Update card and save
            updated_card = dialog.get_updated_card() # Dialog modifies card in-place
            if self.storage.save_card(updated_card, deck_id):
                self.logger.info(f"Card {card_id} updated")
                # Update in the UI list
                self.preview_card_list.update_card(updated_card)
                 # Show confirmation
                QMessageBox.information(
                    self,
                    "Card Updated",
                    "The flashcard has been updated successfully."
                )
            else:
                 self.logger.error(f"Failed to save updated card {card_id}")
                 QMessageBox.critical(self, "Error", "Failed to save card updates.")


    @handle_errors(dialog_title="Delete Error")
    def delete_card(self, card_id):                     #
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
            self.logger.info(f"Card {card_id} deleted from storage.")
            # Remove from UI preview list
            self.preview_card_list.remove_card(card_id)

            # Update deck info in combo box (need to refresh count)
            self.refresh_decks() # Refreshing might re-select deck, triggering on_deck_selected

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

    def update_settings(self):                          #
        """Update view based on changed settings."""
        # Apply any settings changes that affect the study view
        # e.g., shuffle setting, default cards per session (though not used here directly)
        self.logger.debug("StudyView settings updated (no specific actions implemented yet).")
        pass
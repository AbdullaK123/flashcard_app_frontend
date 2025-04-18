from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel,
    QTextEdit, QComboBox, QDialogButtonBox,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from src.data.models import Flashcard
from src.utils.logger import get_logger
from src.utils.error_handling import handle_errors
from typing import List, Tuple  # Import Tuple


class NewCardWithTopicDialog(QDialog):
    """Dialog for creating a new flashcard, allowing topic selection."""

    # Signal to send the new card and deck_id
    card_created = pyqtSignal(Flashcard, str)  # Modified signal

    def __init__(self, topics: List[Tuple[str, str]], parent=None):  # Modified topics type
        super().__init__(parent)
        self.topics = topics  # List of (topic_name, deck_id) tuples
        self.logger = get_logger(__name__)

        self.setWindowTitle("Create New Flashcard")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setObjectName("newCardWithTopicDialog")  # For CSS styling

        # Setup UI
        self.setup_ui()

    @handle_errors(dialog_title="UI Error")
    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title
        title = QLabel("Create New Flashcard")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Form layout
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Topic selection
        topic_label = QLabel("Topic:")
        topic_label.setStyleSheet("font-weight: bold;")
        self.topic_combo = QComboBox()
        for topic_name, _ in self.topics:
            self.topic_combo.addItem(topic_name)
        form_layout.addRow(topic_label, self.topic_combo)

        # Question field
        question_label = QLabel("Question:")
        question_label.setStyleSheet("font-weight: bold;")
        self.question_edit = QTextEdit()
        self.question_edit.setMinimumHeight(100)
        form_layout.addRow(question_label, self.question_edit)

        # Answer field
        answer_label = QLabel("Answer:")
        answer_label.setStyleSheet("font-weight: bold;")
        self.answer_edit = QTextEdit()
        self.answer_edit.setMinimumHeight(150)
        form_layout.addRow(answer_label, self.answer_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.create_card)
        button_box.rejected.connect(self.reject)

        # Replace "Save" text with "Create"
        create_button = button_box.button(QDialogButtonBox.StandardButton.Save)
        if create_button:
            create_button.setText("Create")

        layout.addWidget(button_box)

    @handle_errors(dialog_title="Creation Error")
    def create_card(self):
        """Create a new flashcard."""
        # Get the values
        topic_name = self.topic_combo.currentText()
        question = self.question_edit.toPlainText().strip()
        answer = self.answer_edit.toPlainText().strip()

        # Validate
        if not topic_name:
            QMessageBox.warning(self, "Missing Topic", "The topic field cannot be empty.")
            self.topic_combo.setFocus()
            return

        if not question:
            QMessageBox.warning(self, "Missing Question", "The question field cannot be empty.")
            self.question_edit.setFocus()
            return

        if not answer:
            QMessageBox.warning(self, "Missing Answer", "The answer field cannot be empty.")
            self.answer_edit.setFocus()
            return

        # Find the deck_id associated with the selected topic_name
        deck_id = None
        for name, d_id in self.topics:
            if name == topic_name:
                deck_id = d_id
                break

        if not deck_id:
            self.logger.error(f"Could not find deck_id for topic: {topic_name}")
            QMessageBox.critical(
                self,
                "Database Error",
                "Could not retrieve deck information. Please try again."
            )
            return

        # Create the new card
        new_card = Flashcard.create(
            question=question,
            answer=answer,
            topic=topic_name
        )

        # Emit the signal with the new card and deck_id
        self.card_created.emit(new_card, deck_id)  # Modified emit

        # Accept dialog (return True)
        self.accept()
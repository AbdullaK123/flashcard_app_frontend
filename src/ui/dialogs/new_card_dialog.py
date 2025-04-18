# src/ui/dialogs/new_card_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, 
    QTextEdit, QLineEdit, QDialogButtonBox,
    QMessageBox
)
from PyQt6.QtCore import Qt

from src.data.models import Flashcard
from src.utils.logger import get_logger
from src.utils.error_handling import handle_errors

class NewCardDialog(QDialog):
    """Dialog for creating a new flashcard manually."""
    
    def __init__(self, deck_id, deck_name, parent=None):
        super().__init__(parent)
        self.deck_id = deck_id
        self.deck_name = deck_name
        self.logger = get_logger(__name__)
        
        self.setWindowTitle("Create New Flashcard")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setObjectName("newCardDialog")  # For CSS styling
        
        # The created card
        self.new_card = None
        
        # Setup UI
        self.setup_ui()
    
    @handle_errors(dialog_title="UI Error")
    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel(f"Add Card to '{self.deck_name}'")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # Topic field (pre-filled with deck name but editable)
        topic_label = QLabel("Topic:")
        topic_label.setStyleSheet("font-weight: bold;")
        self.topic_edit = QLineEdit(self.deck_name)
        form_layout.addRow(topic_label, self.topic_edit)
        
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
        topic = self.topic_edit.text().strip()
        question = self.question_edit.toPlainText().strip()
        answer = self.answer_edit.toPlainText().strip()
        
        # Validate
        if not topic:
            QMessageBox.warning(self, "Missing Topic", "The topic field cannot be empty.")
            self.topic_edit.setFocus()
            return
            
        if not question:
            QMessageBox.warning(self, "Missing Question", "The question field cannot be empty.")
            self.question_edit.setFocus()
            return
            
        if not answer:
            QMessageBox.warning(self, "Missing Answer", "The answer field cannot be empty.")
            self.answer_edit.setFocus()
            return
        
        # Create the new card
        self.new_card = Flashcard.create(
            question=question,
            answer=answer,
            topic=topic
        )
        
        # Accept dialog (return True)
        self.accept()
    
    def get_new_card(self):
        """Return the newly created card object."""
        return self.new_card
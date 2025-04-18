# src/ui/dialogs/edit_card_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, 
    QTextEdit, QPushButton, QDialogButtonBox,
    QMessageBox
)
from PyQt6.QtCore import Qt
from src.data.models import Flashcard
from src.utils.logger import get_logger
from src.utils.error_handling import handle_errors

class EditCardDialog(QDialog):
    """Dialog for editing a flashcard's question and answer."""
    
    def __init__(self, card, parent=None):
        super().__init__(parent)
        self.card = card
        self.logger = get_logger(__name__)
        
        self.setWindowTitle("Edit Flashcard")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setObjectName("editCardDialog")  # For CSS styling
        
        # Setup UI
        self.setup_ui()
        
        # Load card data
        self.load_card_data()
    
    @handle_errors(dialog_title="UI Error")
    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Edit Flashcard")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
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
        
        # Topic (non-editable)
        topic_label = QLabel("Topic:")
        topic_label.setStyleSheet("font-weight: bold;")
        self.topic_display = QLabel()
        form_layout.addRow(topic_label, self.topic_display)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.save_changes)
        button_box.rejected.connect(self.reject)
        
        # Replace "Save" text with "Update"
        update_button = button_box.button(QDialogButtonBox.StandardButton.Save)
        if update_button:
            update_button.setText("Update")
        
        layout.addWidget(button_box)
    
    def load_card_data(self):
        """Load the card data into the form fields."""
        self.question_edit.setText(self.card.question)
        self.answer_edit.setText(self.card.answer)
        self.topic_display.setText(self.card.topic)
    
    @handle_errors(dialog_title="Save Error")
    def save_changes(self):
        """Save changes to the flashcard."""
        # Get the edited values
        new_question = self.question_edit.toPlainText().strip()
        new_answer = self.answer_edit.toPlainText().strip()
        
        # Validate
        if not new_question:
            QMessageBox.warning(self, "Missing Question", "The question field cannot be empty.")
            self.question_edit.setFocus()
            return
            
        if not new_answer:
            QMessageBox.warning(self, "Missing Answer", "The answer field cannot be empty.")
            self.answer_edit.setFocus()
            return
        
        # Update card values (without saving yet)
        self.card.question = new_question
        self.card.answer = new_answer
        
        # Accept dialog (return True)
        self.accept()
    
    def get_updated_card(self):
        """Return the updated card object."""
        return self.card
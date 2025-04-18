# src/ui/widgets/flashcard_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, 
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QRect

class FlashcardWidget(QWidget):
    """Widget for displaying and interacting with a flashcard."""
    
    # Signal emitted when card is flipped
    card_flipped = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        
        # State
        self.question = ""
        self.answer = ""
        self.is_flipped = False
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create card frame
        self.card_frame = QFrame()
        self.card_frame.setFrameShape(QFrame.Shape.Box)
        self.card_frame.setLineWidth(2)
        self.card_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Expanding
        )
        self.card_frame.setMinimumHeight(200)
        
        # Card layout
        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(20, 20, 20, 20)
        
        # Content label
        self.content_label = QLabel()
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet(
            "font-size: 18px; padding: 10px;"
        )
        card_layout.addWidget(self.content_label, 1)
        
        # Add card frame to main layout
        layout.addWidget(self.card_frame)
    
    def set_card(self, question, answer):
        """Set the card content."""
        self.question = question
        self.answer = answer
        
        # Reset to question side
        self.is_flipped = False
        self.update_display()
    
    def update_display(self):
        """Update the display based on current state."""
        if self.is_flipped:
            self.content_label.setText(self.answer)
            self.card_frame.setStyleSheet(
                "background-color: #f0f8ff;"  # Light blue for answer side
            )
        else:
            self.content_label.setText(self.question)
            self.card_frame.setStyleSheet(
                "background-color: white;"
            )
    
    def flip_card(self):
        """Flip the card between question and answer."""
        self.is_flipped = not self.is_flipped
        
        # Update display with animation
        self.animate_flip()
        
        # Emit signal
        self.card_flipped.emit(self.is_flipped)
    
    def animate_flip(self):
        """Animate the card flip."""
        # Simple animation - just update content
        # In a more advanced implementation, you could add a 3D flip effect
        self.update_display()
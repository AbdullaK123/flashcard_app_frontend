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
        """Set up the user interface with modern styling."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create card frame
        self.card_frame = QFrame()
        self.card_frame.setObjectName("flashcardFrame")
        self.card_frame.setFrameShape(QFrame.Shape.Box)
        self.card_frame.setLineWidth(0)  # No explicit line - handled by stylesheet border
        self.card_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Expanding
        )
        self.card_frame.setMinimumHeight(300)
        
        # Card layout
        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(16)
        
        # Content label
        self.content_label = QLabel()
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_label.setWordWrap(True)
        self.content_label.setProperty("class", "card-content")
        card_layout.addWidget(self.content_label, 1)
        
        # Add card frame to main layout
        layout.addWidget(self.card_frame)
        
        # Set initial content
        self.update_display()

    def update_display(self):
        """Update the display based on current state with proper styling."""
        if self.is_flipped:
            self.content_label.setText(self.answer)
            self.content_label.setProperty("class", "card-content card-answer")
            # Set flipped property for styling
            self.card_frame.setProperty("flipped", "true")
        else:
            self.content_label.setText(self.question)
            self.content_label.setProperty("class", "card-content card-question")
            # Remove flipped property
            self.card_frame.setProperty("flipped", "false")
        
        # Force style refresh
        self.card_frame.style().unpolish(self.card_frame)
        self.card_frame.style().polish(self.card_frame)
        self.content_label.style().unpolish(self.content_label)
        self.content_label.style().polish(self.content_label)
    
    def set_card(self, question, answer):
        """Set the card content."""
        self.question = question
        self.answer = answer
        
        # Reset to question side
        self.is_flipped = False
        self.update_display()
    
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
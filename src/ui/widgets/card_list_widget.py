# src/ui/widgets/card_list_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QPushButton,
    QMenu, QAbstractItemView, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QFont
from src.utils.logger import get_logger
from src.utils.error_handling import handle_errors

class CardListWidget(QWidget):
    """Widget for displaying and managing a list of flashcards."""
    
    # Signals for communication with parent widgets
    card_selected = pyqtSignal(str)  # Emits card ID when selected
    edit_requested = pyqtSignal(str)  # Emits card ID when edit requested
    delete_requested = pyqtSignal(str)  # Emits card ID when delete requested
    create_requested = pyqtSignal()  # Emits when user wants to create a new card
    
    def __init__(self, parent=None, show_toolbar=True, read_only=False):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.show_toolbar = show_toolbar
        self.read_only = read_only
        
        # Store cards data for reference
        self.cards = {}  # card_id -> card object
        
        # Setup UI
        self.setup_ui()
    
    @handle_errors(dialog_title="UI Error")
    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Create header and instructions
        self.header_label = QLabel("Flashcards")
        self.header_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.header_label)
        
        # Create list widget
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.list_widget.setAlternatingRowColors(True)
        layout.addWidget(self.list_widget)
        
        # Add Empty message when list is empty
        self.empty_label = QLabel("No flashcards in this list")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #888; font-style: italic; padding: 20px;")
        self.empty_label.setVisible(False)
        layout.addWidget(self.empty_label)
        
        # Only show toolbar if requested
        if self.show_toolbar:
            # Create toolbar
            toolbar_layout = QHBoxLayout()
            toolbar_layout.setSpacing(8)
            
            # New button
            self.new_button = QPushButton("New Card")
            self.new_button.setIcon(QIcon.fromTheme("document-new"))
            self.new_button.clicked.connect(self.create_new_card)
            self.new_button.setEnabled(not self.read_only)
            toolbar_layout.addWidget(self.new_button)
            
            # Spacer
            toolbar_layout.addStretch(1)
            
            # Edit button
            self.edit_button = QPushButton("Edit")
            self.edit_button.setIcon(QIcon.fromTheme("document-edit"))
            self.edit_button.clicked.connect(self.edit_selected_card)
            self.edit_button.setEnabled(False)
            toolbar_layout.addWidget(self.edit_button)
            
            # Delete button
            self.delete_button = QPushButton("Delete")
            self.delete_button.setIcon(QIcon.fromTheme("edit-delete"))
            self.delete_button.clicked.connect(self.delete_selected_card)
            self.delete_button.setEnabled(False)
            toolbar_layout.addWidget(self.delete_button)
            
            layout.addLayout(toolbar_layout)
    
    def set_title(self, title):
        """Set the header title."""
        self.header_label.setText(title)
    
    def clear(self):
        """Clear all cards from the list."""
        self.list_widget.clear()
        self.cards = {}
        self.update_button_states()
        self.update_empty_state()
    
    def add_card(self, card):
        """Add a card to the list."""
        if card.id in self.cards:
            # Update existing card
            self.update_card(card)
            return
        
        # Store card data
        self.cards[card.id] = card
        
        # Create list item
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, card.id)
        
        # Set item text (first 50 chars of question)
        question = card.question
        if len(question) > 50:
            question = question[:47] + "..."
        item.setText(question)
        
        # Add to list
        self.list_widget.addItem(item)
        self.update_empty_state()
    
    def add_cards(self, cards):
        """Add multiple cards to the list."""
        for card in cards:
            self.add_card(card)
    
    def update_card(self, card):
        """Update an existing card in the list."""
        # Update stored data
        self.cards[card.id] = card
        
        # Find and update list item
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == card.id:
                # Update item text
                question = card.question
                if len(question) > 50:
                    question = question[:47] + "..."
                item.setText(question)
                break
    
    def remove_card(self, card_id):
        """Remove a card from the list."""
        # Remove from stored data
        if card_id in self.cards:
            del self.cards[card_id]
        
        # Find and remove list item
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == card_id:
                self.list_widget.takeItem(i)
                break
        
        self.update_button_states()
        self.update_empty_state()
    
    def get_selected_card_id(self):
        """Get the ID of the currently selected card."""
        items = self.list_widget.selectedItems()
        if items:
            return items[0].data(Qt.ItemDataRole.UserRole)
        return None
    
    def get_selected_card(self):
        """Get the currently selected card object."""
        card_id = self.get_selected_card_id()
        if card_id and card_id in self.cards:
            return self.cards[card_id]
        return None
    
    def on_item_clicked(self, item):
        """Handle item clicked event."""
        card_id = item.data(Qt.ItemDataRole.UserRole)
        self.card_selected.emit(card_id)
        self.update_button_states()
    
    def on_item_double_clicked(self, item):
        """Handle item double-clicked event."""
        if self.read_only:
            # Just emit selection signal
            self.card_selected.emit(item.data(Qt.ItemDataRole.UserRole))
        else:
            # Edit the card
            self.edit_selected_card()
    
    def update_button_states(self):
        """Update button enabled states based on selection."""
        if not self.show_toolbar or not hasattr(self, 'edit_button'):
            return
            
        has_selection = self.get_selected_card_id() is not None
        self.edit_button.setEnabled(has_selection and not self.read_only)
        self.delete_button.setEnabled(has_selection and not self.read_only)
    
    def update_empty_state(self):
        """Show/hide the empty state message."""
        is_empty = self.list_widget.count() == 0
        self.empty_label.setVisible(is_empty)
        self.list_widget.setVisible(not is_empty)
    
    def create_new_card(self):
        """Request creation of a new card."""
        if not self.read_only:
            self.create_requested.emit()
    
    def edit_selected_card(self):
        """Edit the currently selected card."""
        if self.read_only:
            return
            
        card_id = self.get_selected_card_id()
        if card_id:
            self.edit_requested.emit(card_id)
    
    def delete_selected_card(self):
        """Delete the currently selected card."""
        if self.read_only:
            return
            
        card_id = self.get_selected_card_id()
        if card_id:
            self.delete_requested.emit(card_id)
    
    def show_context_menu(self, position):
        """Show context menu for card list items."""
        if self.read_only:
            return
            
        menu = QMenu(self)
        
        # Add "New Card" option at the top
        new_action = QAction("New Card", self)
        new_action.triggered.connect(self.create_new_card)
        menu.addAction(new_action)
        
        # Get the item at the position
        item = self.list_widget.itemAt(position)
        
        if item:
            menu.addSeparator()
            
            # Add actions for selected item
            view_action = QAction("View Card", self)
            view_action.triggered.connect(lambda: self.card_selected.emit(item.data(Qt.ItemDataRole.UserRole)))
            menu.addAction(view_action)
            
            edit_action = QAction("Edit Card", self)
            edit_action.triggered.connect(self.edit_selected_card)
            menu.addAction(edit_action)
            
            menu.addSeparator()
            
            delete_action = QAction("Delete Card", self)
            delete_action.triggered.connect(self.delete_selected_card)
            menu.addAction(delete_action)
        
        # Show the menu
        menu.exec(self.list_widget.mapToGlobal(position))
    
    def set_read_only(self, read_only):
        """Set whether the widget is read-only."""
        self.read_only = read_only
        if self.show_toolbar:
            self.new_button.setEnabled(not read_only)
            self.update_button_states()
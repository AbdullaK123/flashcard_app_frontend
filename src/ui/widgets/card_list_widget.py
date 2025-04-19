from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QPushButton,
    QMenu, QAbstractItemView, QMessageBox,
    QSizePolicy, QToolButton, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QIcon, QFont
from src.utils.logger import get_logger
from src.utils.error_handling import handle_errors

class CardListWidget(QWidget):
    """Widget for displaying and managing a list of flashcards with responsive layout."""
    
    # Signals for communication with parent widgets
    card_selected = pyqtSignal(str)  # Emits card ID when selected
    preview_requested = pyqtSignal(str)  # Emits card ID when preview requested - NEW SIGNAL
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
        
        # Track UI state
        self.is_compact_mode = False
        
        # Setup UI
        self.setup_ui()
    
    @handle_errors(dialog_title="UI Error")
    def setup_ui(self):
        """Set up the user interface with modern styling."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Create header container
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(8, 0, 8, 0)
        header_layout.setSpacing(8)
        
        # Header title
        self.header_label = QLabel("Flashcards")
        self.header_label.setProperty("class", "h3")
        self.header_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        header_layout.addWidget(self.header_label)
        
        # Add header to main layout
        layout.addWidget(header_container)
        
        # Create list widget
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        # Turn off alternating row colors to fix the issue
        self.list_widget.setAlternatingRowColors(False)
        self.list_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Set list item height for better readability and ensure all items have same background
        self.list_widget.setStyleSheet("""
            QListWidget::item {
                min-height: 32px;
                background-color: transparent;
            }
        """)
        
        layout.addWidget(self.list_widget)
        
        # Add empty state message
        self.empty_label = QLabel("No flashcards in this list")
        self.empty_label.setProperty("class", "muted")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setVisible(False)
        self.empty_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.empty_label)
        
        # Only show toolbar if requested
        if self.show_toolbar:
            # Create toolbar - horizontal by default
            toolbar_container = QWidget()
            toolbar_container.setProperty("class", "card-toolbar")
            self.toolbar_layout = QHBoxLayout(toolbar_container)
            self.toolbar_layout.setContentsMargins(8, 8, 8, 8)
            self.toolbar_layout.setSpacing(16)
            
            # New button
            self.new_button = QPushButton("New Card")
            self.new_button.setProperty("class", "primary")
            self.new_button.clicked.connect(self.create_new_card)
            self.new_button.setEnabled(not self.read_only)
            self.new_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
            self.toolbar_layout.addWidget(self.new_button)
            
            # Spacer
            self.toolbar_layout.addStretch(1)
            
            # Edit button
            self.edit_button = QPushButton("Edit")
            self.edit_button.setProperty("class", "secondary")
            self.edit_button.clicked.connect(self.edit_selected_card)
            self.edit_button.setEnabled(False)
            self.edit_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
            self.toolbar_layout.addWidget(self.edit_button)
            
            # Delete button
            self.delete_button = QPushButton("Delete")
            self.delete_button.setProperty("class", "danger")
            self.delete_button.clicked.connect(self.delete_selected_card)
            self.delete_button.setEnabled(False)
            self.delete_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
            self.toolbar_layout.addWidget(self.delete_button)
            
            layout.addWidget(toolbar_container)
        
        # Update the empty state visibility
        self.update_empty_state()
    
    def handle_resize(self, width, height):
        """Handle resize events to adapt layout."""
        if width < 500 and not self.is_compact_mode:
            self.switch_to_compact_mode()
        elif width >= 500 and self.is_compact_mode:
            self.switch_to_normal_mode()
    
    def switch_to_compact_mode(self):
        """Switch to compact layout for smaller screens."""
        self.is_compact_mode = True
        
        # If we have a toolbar, reorganize it for compact mode
        if self.show_toolbar and hasattr(self, 'toolbar_layout'):
            # Convert toolbar to vertical layout if it's currently horizontal
            if isinstance(self.toolbar_layout, QHBoxLayout):
                # Remove current toolbar layout
                old_layout = self.toolbar_layout
                
                # Create new vertical layout
                self.toolbar_layout = QVBoxLayout()
                self.toolbar_layout.setSpacing(8)
                
                # Move buttons to new layout
                while old_layout.count():
                    item = old_layout.takeAt(0)
                    if item.widget():
                        self.toolbar_layout.addWidget(item.widget())
                    elif item.spacerItem():
                        # Skip spacers in compact mode
                        pass
                
                # Apply compact styling
                for i in range(self.toolbar_layout.count()):
                    item = self.toolbar_layout.itemAt(i)
                    if item.widget():
                        item.widget().setMinimumWidth(150)
                        item.widget().setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    
    def switch_to_normal_mode(self):
        """Switch to normal layout for larger screens."""
        self.is_compact_mode = False
        
        # If we have a toolbar, restore normal layout
        if self.show_toolbar and hasattr(self, 'toolbar_layout'):
            # Convert toolbar to horizontal layout if it's vertical
            if isinstance(self.toolbar_layout, QVBoxLayout):
                # Remove current toolbar layout
                old_layout = self.toolbar_layout
                
                # Create new horizontal layout
                self.toolbar_layout = QHBoxLayout()
                self.toolbar_layout.setSpacing(8)
                
                # Move buttons to new layout
                has_new_button = False
                has_edit_button = False
                has_delete_button = False
                
                # First extract all widgets
                widgets = []
                while old_layout.count():
                    item = old_layout.takeAt(0)
                    if item.widget():
                        widgets.append(item.widget())
                
                # Add new button first
                for widget in widgets:
                    if widget == self.new_button:
                        self.toolbar_layout.addWidget(widget)
                        has_new_button = True
                        break
                
                # Add spacer in the middle
                self.toolbar_layout.addStretch(1)
                
                # Add edit and delete buttons
                for widget in widgets:
                    if widget == self.edit_button:
                        self.toolbar_layout.addWidget(widget)
                        has_edit_button = True
                    elif widget == self.delete_button:
                        self.toolbar_layout.addWidget(widget)
                        has_delete_button = True
                
                # Restore normal styling
                for widget in widgets:
                    widget.setMinimumWidth(80)
                    widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
    
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
    
    def get_card(self, card_id):
        """Get a card by ID."""
        return self.cards.get(card_id)
    
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
    
    def highlight_card(self, card_id):
        """Highlight a specific card in the list."""
        # Clear current selection
        self.list_widget.clearSelection()
        
        # Find and select the item
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == card_id:
                self.list_widget.setCurrentItem(item)
                self.list_widget.scrollToItem(item)
                break
    
    def on_item_clicked(self, item):
        """Handle item clicked event."""
        card_id = item.data(Qt.ItemDataRole.UserRole)
        self.card_selected.emit(card_id)
        self.update_button_states()
    
    def on_item_double_clicked(self, item):
        """Handle item double-clicked event - FIX: Always emit preview_requested."""
        card_id = item.data(Qt.ItemDataRole.UserRole)
        # Always emit the preview signal, regardless of read_only status
        self.preview_requested.emit(card_id)
    
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
            # FIX: Change view action to trigger preview signal
            view_action = QAction("View Card", self)
            card_id = item.data(Qt.ItemDataRole.UserRole)
            view_action.triggered.connect(lambda: self.preview_requested.emit(card_id))
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
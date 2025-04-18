from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QSize
from src.utils.logger import get_logger

class ResponsiveView(QWidget):
    """
    Base class for responsive views that adapt to different screen sizes.
    Inherit from this class to create views that respond to window size changes.
    """
    
    def __init__(self, settings, storage, parent=None):
        """Initialize the responsive view with settings and storage."""
        super().__init__(parent)
        self.settings = settings
        self.storage = storage
        self.logger = get_logger(self.__class__.__name__)
        
        # Responsive state
        self.is_compact_mode = False
        self.is_fullscreen = False
        self.current_width = 0
        self.current_height = 0
        
        # Set size policy for the view
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Store references to all layouts to prevent garbage collection
        self._layout_references = []
    
    def handle_resize(self, width, height):
        """
        Handle parent window resize to adjust layout dynamically.
        Override this method in subclasses to implement specific resizing behavior.
        """
        self.current_width = width
        self.current_height = height
        
        # Default implementation checks for compact mode
        if width < 800 and not self.is_compact_mode:
            self.switch_to_compact_mode()
        elif width >= 800 and self.is_compact_mode:
            self.switch_to_normal_mode()
    
    def handle_maximized(self):
        """
        Handle window being maximized.
        Override this method in subclasses to implement specific maximized behavior.
        """
        self.is_fullscreen = True
        self.logger.debug("View is now in maximized state")
    
    def handle_normal(self):
        """
        Handle window returning to normal size.
        Override this method in subclasses to implement specific normal window behavior.
        """
        self.is_fullscreen = False
        self.logger.debug("View is now in normal state")
    
    def switch_to_compact_mode(self):
        """
        Switch to compact layout for smaller screens.
        Override this method in subclasses to implement specific compact mode behavior.
        """
        self.is_compact_mode = True
        self.logger.debug("Switching to compact mode")
    
    def switch_to_normal_mode(self):
        """
        Switch to normal layout for larger screens.
        Override this method in subclasses to implement specific normal mode behavior.
        """
        self.is_compact_mode = False
        self.logger.debug("Switching to normal mode")
    
    def update_settings(self):
        """
        Update view based on changed settings.
        Override this method in subclasses to implement settings update behavior.
        """
        pass
        
    def keep_reference(self, obj):
        """
        Stores a reference to a layout or widget to prevent garbage collection.
        
        Args:
            obj: The layout or widget to keep a reference to
        """
        self._layout_references.append(obj)
        return obj
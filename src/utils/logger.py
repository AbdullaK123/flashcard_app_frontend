import os
import logging
from logging.handlers import RotatingFileHandler

def get_log_path():
    """Get the path to the log file directory."""
    # Create logs directory in user's home folder
    log_dir = os.path.join(os.path.expanduser("~"), ".flashcards", "logs")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, "flashcards.log")

def setup_logger():
    """Set up and configure the application logger."""
    # Create logger
    logger = logging.getLogger("flashcards")
    logger.setLevel(logging.DEBUG)
    
    # Only add handlers if they haven't been added already
    if not logger.handlers:
        # Create console handler for INFO+ messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_format)
        
        # Create file handler for DEBUG+ messages with rotation
        file_handler = RotatingFileHandler(
            get_log_path(),
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3  # Keep 3 backup copies
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        
        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name=None):
    """Get a named logger for a specific module."""
    if name:
        return logging.getLogger(f"flashcards.{name}")
    return logging.getLogger("flashcards")
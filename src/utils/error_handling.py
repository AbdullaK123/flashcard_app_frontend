import traceback
import functools
from PyQt6.QtWidgets import QMessageBox
from src.utils.logger import get_logger

logger = get_logger("error_handler")

def handle_errors(show_dialog=True, dialog_title="Error", log_exception=True):
    """
    Decorator for centralized error handling.
    
    Args:
        show_dialog (bool): Whether to show an error dialog to the user
        dialog_title (str): Title for the error dialog
        log_exception (bool): Whether to log the exception details
    
    Usage:
        @handle_errors()
        def some_function():
            # code that might raise exceptions
            
        @handle_errors(show_dialog=False)  # Just log, don't show dialog
        def background_task():
            # background processing
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get detailed exception information
                error_msg = str(e)
                error_type = type(e).__name__
                stack_trace = traceback.format_exc()
                
                # Log the exception if requested
                if log_exception:
                    logger.error(f"Error in {func.__name__}: {error_type}: {error_msg}")
                    logger.debug(f"Stack trace:\n{stack_trace}")
                
                # Show dialog if requested
                if show_dialog:
                    QMessageBox.critical(
                        None,
                        dialog_title,
                        f"An error occurred: {error_msg}\n\n"
                        f"Please try again or check the application logs."
                    )
                
                # Re-raise certain exceptions that should not be swallowed
                if isinstance(e, (KeyboardInterrupt, SystemExit)):
                    raise
                
                # Return None to indicate failure
                return None
        return wrapper
    return decorator


def handle_api_errors(func):
    """
    Specialized decorator for API call functions.
    Handles API-specific errors and provides appropriate messages.
    """
    @functools.wraps(func)
    @handle_errors(show_dialog=False, log_exception=True)  # First log but don't show dialog
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ConnectionError:
            logger.error("API connection error")
            QMessageBox.critical(
                None,
                "Connection Error",
                "Could not connect to the flashcard API server.\n\n"
                "Please check that the server is running and your network connection is active."
            )
        except TimeoutError:
            logger.error("API request timeout")
            QMessageBox.critical(
                None,
                "Request Timeout",
                "The request to the API server timed out.\n\n"
                "This might be due to network issues or high server load."
            )
        except Exception as e:
            # This will catch any exceptions not handled by the outer decorator
            logger.error(f"Unhandled API error: {str(e)}")
            QMessageBox.critical(
                None,
                "API Error",
                f"An error occurred while communicating with the server: {str(e)}"
            )
        return None
    return wrapper
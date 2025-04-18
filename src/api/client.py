# src/api/client.py
import httpx
from typing import Optional
from urllib.parse import urljoin
import asyncio
from src.api.models import FlashCardRequest, FlashCardResponse
from src.utils.logger import get_logger
from src.utils.error_handling import handle_errors

class APIClient:
    """Client for communicating with the backend flashcard API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.logger = get_logger(__name__)
        # Longer timeout since generation can take time
        self.timeout = 60.0
    
    @handle_errors(show_dialog=False, log_exception=True)
    async def generate_flashcards(self, topic: str, num_questions: int = 10) -> Optional[FlashCardResponse]:
        """
        Generate flashcards for a topic using the API.
        
        Args:
            topic: The topic to generate flashcards for
            num_questions: Number of flashcards to generate (1-50)
            
        Returns:
            FlashCardResponse object containing the generated flashcards
        """
        self.logger.info(f"Generating flashcards for topic: {topic}")
        
        # Create request
        request = FlashCardRequest(topic=topic, num_questions=num_questions)
        url = urljoin(self.base_url, "/generate_flashcards")
        
        # Make the API call
        async with httpx.AsyncClient() as client:
            self.logger.debug(f"Making API request to {url}")
            
            response = await client.post(
                url,
                json=request.to_dict(),
                timeout=self.timeout
            )
            
            # Raise an exception for HTTP errors
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            self.logger.info(f"Received response with {len(data.get('cards', []))} cards")
            
            # Convert to model
            return FlashCardResponse.from_dict(data)
    
    @handle_errors(show_dialog=False, log_exception=True)
    async def test_connection(self) -> bool:
        """
        Test the connection to the API server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            url = urljoin(self.base_url, "/docs")  # FastAPI docs page is always available
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=5.0)
                return response.status_code == 200
        except Exception as e:
            self.logger.error(f"API connection test failed: {str(e)}")
            return False
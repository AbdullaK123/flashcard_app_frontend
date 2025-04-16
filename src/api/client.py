import httpx
import json
from typing import Dict, List, Optional, Any
import asyncio
from urllib.parse import urljoin
from src.api.models import FlashCardRequest, FlashCardResponse, FlashCardPair
from src.utils.logger import get_logger
from src.utils.error_handling import handle_api_errors

class APIClient:
    """Client for interacting with the flashcard generation API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.logger = get_logger("api_client")
        self.timeout = 60.0  # 60 second timeout for API calls (generation can take time)
        
        self.logger.info(f"API client initialized with base URL: {self.base_url}")
    
    @handle_api_errors
    async def generate_flashcards(self, topic: str, num_questions: int = 10) -> Optional[FlashCardResponse]:
        """
        Generate flashcards for a given topic using the API.
        
        Args:
            topic: The topic to generate flashcards for
            num_questions: Number of flashcards to generate (1-50)
            
        Returns:
            FlashCardResponse object if successful, None otherwise
        """
        self.logger.info(f"Generating flashcards for topic: {topic}, count: {num_questions}")
        
        # Create request
        request = FlashCardRequest(topic=topic, num_questions=num_questions)
        url = urljoin(self.base_url, "/generate_flashcards")
        
        # Make API call
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=request.to_dict(),
                timeout=self.timeout
            )
            
            # Raise exception for HTTP errors
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            self.logger.info(f"Received response with {len(data.get('cards', []))} flashcards")
            
            # Convert to model
            result = FlashCardResponse.from_dict(data)
            return result
    
    @handle_api_errors
    async def health_check(self) -> bool:
        """
        Check if the API is available and responding.
        
        Returns:
            True if API is responsive, False otherwise
        """
        url = urljoin(self.base_url, "/health")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=5.0)
                return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False
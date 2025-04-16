from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class FlashCardPair:
    """Represents a question-answer flashcard pair from the API."""
    question: str
    answer: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FlashCardPair':
        """Create a FlashCardPair from a dictionary."""
        return cls(
            question=data['question'],
            answer=data['answer']
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'question': self.question,
            'answer': self.answer
        }

@dataclass
class FlashCardRequest:
    """Represents a request to generate flashcards."""
    topic: str
    num_questions: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'topic': self.topic,
            'num_questions': self.num_questions
        }

@dataclass
class FlashCardResponse:
    """Represents a response containing generated flashcards."""
    topic: str
    cards: List[FlashCardPair]
    source_info: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FlashCardResponse':
        """Create a FlashCardResponse from a dictionary."""
        cards = [FlashCardPair.from_dict(card_data) for card_data in data.get('cards', [])]
        
        return cls(
            topic=data['topic'],
            cards=cards,
            source_info=data.get('source_info')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'topic': self.topic,
            'cards': [card.to_dict() for card in self.cards],
            'source_info': self.source_info
        }
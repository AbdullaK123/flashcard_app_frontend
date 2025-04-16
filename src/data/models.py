from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import datetime
import uuid

@dataclass
class Flashcard:
    """Represents a single flashcard with question, answer, and metadata."""
    id: str
    question: str
    answer: str
    topic: str
    created_at: datetime.datetime
    last_reviewed: Optional[datetime.datetime] = None
    
    @classmethod
    def create(cls, question: str, answer: str, topic: str) -> 'Flashcard':
        """Factory method to create a new flashcard with generated ID and timestamp."""
        return cls(
            id=str(uuid.uuid4()),
            question=question,
            answer=answer,
            topic=topic,
            created_at=datetime.datetime.now()
        )
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Flashcard':
        """Create a flashcard from a dictionary (e.g., from database)."""
        # Convert string timestamps to datetime objects if needed
        created_at = data['created_at']
        if isinstance(created_at, str):
            created_at = datetime.datetime.fromisoformat(created_at)
            
        last_reviewed = data.get('last_reviewed')
        if isinstance(last_reviewed, str) and last_reviewed:
            last_reviewed = datetime.datetime.fromisoformat(last_reviewed)
        
        return cls(
            id=data['id'],
            question=data['question'],
            answer=data['answer'],
            topic=data['topic'],
            created_at=created_at,
            last_reviewed=last_reviewed
        )
    
    def to_dict(self) -> Dict:
        """Convert flashcard to dictionary for storage."""
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'topic': self.topic,
            'created_at': self.created_at.isoformat(),
            'last_reviewed': self.last_reviewed.isoformat() if self.last_reviewed else None
        }
    
    def mark_reviewed(self) -> None:
        """Mark the card as reviewed now."""
        self.last_reviewed = datetime.datetime.now()


@dataclass
class FlashcardDeck:
    """Represents a collection of flashcards with metadata."""
    id: str
    name: str
    description: str
    created_at: datetime.datetime
    cards: List[Flashcard] = field(default_factory=list)
    last_studied: Optional[datetime.datetime] = None
    
    @classmethod
    def create(cls, name: str, description: str, cards: List[Flashcard] = None) -> 'FlashcardDeck':
        """Factory method to create a new deck with generated ID and timestamp."""
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            created_at=datetime.datetime.now(),
            cards=cards or []
        )
    
    @classmethod
    def from_dict(cls, data: Dict, cards: List[Flashcard] = None) -> 'FlashcardDeck':
        """Create a deck from a dictionary (e.g., from database)."""
        # Convert string timestamps to datetime objects if needed
        created_at = data['created_at']
        if isinstance(created_at, str):
            created_at = datetime.datetime.fromisoformat(created_at)
            
        last_studied = data.get('last_studied')
        if isinstance(last_studied, str) and last_studied:
            last_studied = datetime.datetime.fromisoformat(last_studied)
        
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            created_at=created_at,
            cards=cards or [],
            last_studied=last_studied
        )
    
    def to_dict(self) -> Dict:
        """Convert deck to dictionary for storage (without cards)."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'last_studied': self.last_studied.isoformat() if self.last_studied else None,
        }
    
    def add_card(self, card: Flashcard) -> None:
        """Add a card to the deck."""
        self.cards.append(card)
    
    def remove_card(self, card_id: str) -> bool:
        """Remove a card from the deck by ID."""
        for i, card in enumerate(self.cards):
            if card.id == card_id:
                self.cards.pop(i)
                return True
        return False
    
    def update_last_studied(self) -> None:
        """Update the last studied timestamp."""
        self.last_studied = datetime.datetime.now()
    
    @property
    def card_count(self) -> int:
        """Get the number of cards in the deck."""
        return len(self.cards)


@dataclass
class StudySession:
    """Represents a flashcard study session with performance metrics."""
    id: str
    deck_id: str
    start_time: datetime.datetime
    end_time: Optional[datetime.datetime] = None
    cards_studied: int = 0
    cards_correct: int = 0
    
    @classmethod
    def create(cls, deck_id: str) -> 'StudySession':
        """Factory method to start a new study session."""
        return cls(
            id=str(uuid.uuid4()),
            deck_id=deck_id,
            start_time=datetime.datetime.now()
        )
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StudySession':
        """Create a study session from a dictionary (e.g., from database)."""
        # Convert string timestamps to datetime objects if needed
        start_time = data['start_time']
        if isinstance(start_time, str):
            start_time = datetime.datetime.fromisoformat(start_time)
            
        end_time = data.get('end_time')
        if isinstance(end_time, str) and end_time:
            end_time = datetime.datetime.fromisoformat(end_time)
        
        return cls(
            id=data['id'],
            deck_id=data['deck_id'],
            start_time=start_time,
            end_time=end_time,
            cards_studied=data.get('cards_studied', 0),
            cards_correct=data.get('cards_correct', 0)
        )
    
    def to_dict(self) -> Dict:
        """Convert study session to dictionary for storage."""
        return {
            'id': self.id,
            'deck_id': self.deck_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'cards_studied': self.cards_studied,
            'cards_correct': self.cards_correct
        }
    
    def complete(self, cards_studied: int, cards_correct: int) -> None:
        """Complete the study session with results."""
        self.end_time = datetime.datetime.now()
        self.cards_studied = cards_studied
        self.cards_correct = cards_correct
    
    @property
    def duration(self) -> Optional[datetime.timedelta]:
        """Get the duration of the study session."""
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def accuracy(self) -> float:
        """Get the accuracy percentage (correct/studied)."""
        if self.cards_studied > 0:
            return (self.cards_correct / self.cards_studied) * 100
        return 0.0
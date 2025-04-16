import os
import sqlite3
from typing import List, Dict, Optional, Any, Tuple
import datetime
from contextlib import contextmanager
from src.data.models import Flashcard, FlashcardDeck, StudySession
from src.utils.logger import get_logger
from src.utils.error_handling import handle_errors

class SQLiteStorage:
    """SQLite storage implementation for the flashcard application."""
    
    def __init__(self, db_path: str = None):
        self.logger = get_logger("storage")
        
        # Set default database path if not provided
        if db_path is None:
            data_dir = os.path.join(os.path.expanduser("~"), ".flashcards", "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "flashcards.db")
        
        self.db_path = db_path
        self.logger.debug(f"Database path: {self.db_path}")
        
        # Initialize database schema
        self._init_db()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        connection = sqlite3.connect(self.db_path)
        # Enable foreign keys support
        connection.execute("PRAGMA foreign_keys = ON")
        # Return dictionary-like rows
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()
    
    @handle_errors(show_dialog=False, log_exception=True)
    def _init_db(self) -> None:
        """Initialize the database schema if it doesn't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create decks table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS decks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                last_studied TEXT
            )
            ''')
            
            # Create flashcards table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS flashcards (
                id TEXT PRIMARY KEY,
                deck_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                topic TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_reviewed TEXT,
                FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
            )
            ''')
            
            # Create study sessions table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_sessions (
                id TEXT PRIMARY KEY,
                deck_id TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                cards_studied INTEGER DEFAULT 0,
                cards_correct INTEGER DEFAULT 0,
                FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
            )
            ''')
            
            conn.commit()
            self.logger.info("Database initialized")
    
    # ===== Deck Operations =====
    
    @handle_errors(show_dialog=False, log_exception=True)
    def get_all_decks(self) -> List[FlashcardDeck]:
        """Get all flashcard decks (without cards)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decks ORDER BY created_at DESC")
            rows = cursor.fetchall()
            
            decks = []
            for row in rows:
                deck_dict = dict(row)
                deck = FlashcardDeck.from_dict(deck_dict)
                decks.append(deck)
            
            return decks
    
    @handle_errors(show_dialog=False, log_exception=True)
    def get_deck(self, deck_id: str) -> Optional[FlashcardDeck]:
        """Get a specific deck by ID, including its cards."""
        with self._get_connection() as conn:
            # First get the deck
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decks WHERE id = ?", (deck_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            deck_dict = dict(row)
            
            # Now get all cards for this deck
            cursor.execute("SELECT * FROM flashcards WHERE deck_id = ? ORDER BY created_at", (deck_id,))
            card_rows = cursor.fetchall()
            
            cards = [Flashcard.from_dict(dict(card_row)) for card_row in card_rows]
            
            # Create and return the deck with its cards
            return FlashcardDeck.from_dict(deck_dict, cards)
    
    @handle_errors(show_dialog=False, log_exception=True)
    def save_deck(self, deck: FlashcardDeck) -> bool:
        """Save a deck and its cards to the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if deck already exists
            cursor.execute("SELECT 1 FROM decks WHERE id = ?", (deck.id,))
            exists = cursor.fetchone() is not None
            
            deck_dict = deck.to_dict()
            
            if exists:
                # Update existing deck
                cursor.execute('''
                UPDATE decks 
                SET name = ?, description = ?, last_studied = ?
                WHERE id = ?
                ''', (
                    deck_dict['name'],
                    deck_dict['description'],
                    deck_dict['last_studied'],
                    deck_dict['id']
                ))
            else:
                # Insert new deck
                cursor.execute('''
                INSERT INTO decks (id, name, description, created_at, last_studied)
                VALUES (?, ?, ?, ?, ?)
                ''', (
                    deck_dict['id'],
                    deck_dict['name'],
                    deck_dict['description'],
                    deck_dict['created_at'],
                    deck_dict['last_studied']
                ))
            
            # Save cards
            for card in deck.cards:
                self.save_card(card, deck.id, conn)
            
            conn.commit()
            return True
    
    @handle_errors(show_dialog=False, log_exception=True)
    def delete_deck(self, deck_id: str) -> bool:
        """Delete a deck and all its cards."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM decks WHERE id = ?", (deck_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # ===== Card Operations =====
    
    @handle_errors(show_dialog=False, log_exception=True)
    def save_card(self, card: Flashcard, deck_id: str, connection=None) -> bool:
        """Save a card to the database."""
        # Use provided connection or create a new one
        close_conn = False
        if connection is None:
            connection = sqlite3.connect(self.db_path)
            close_conn = True
        
        try:
            cursor = connection.cursor()
            
            # Check if card already exists
            cursor.execute("SELECT 1 FROM flashcards WHERE id = ?", (card.id,))
            exists = cursor.fetchone() is not None
            
            card_dict = card.to_dict()
            
            if exists:
                # Update existing card
                cursor.execute('''
                UPDATE flashcards 
                SET question = ?, answer = ?, last_reviewed = ?
                WHERE id = ?
                ''', (
                    card_dict['question'],
                    card_dict['answer'],
                    card_dict['last_reviewed'],
                    card_dict['id']
                ))
            else:
                # Insert new card
                cursor.execute('''
                INSERT INTO flashcards (id, deck_id, question, answer, topic, created_at, last_reviewed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    card_dict['id'],
                    deck_id,
                    card_dict['question'],
                    card_dict['answer'],
                    card_dict['topic'],
                    card_dict['created_at'],
                    card_dict['last_reviewed']
                ))
            
            # Only commit if we created our own connection
            if close_conn:
                connection.commit()
            
            return True
        finally:
            # Only close if we created our own connection
            if close_conn and connection:
                connection.close()
    
    @handle_errors(show_dialog=False, log_exception=True)
    def delete_card(self, card_id: str) -> bool:
        """Delete a card from the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM flashcards WHERE id = ?", (card_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # ===== Study Session Operations =====
    
    @handle_errors(show_dialog=False, log_exception=True)
    def save_study_session(self, session: StudySession) -> bool:
        """Save a study session to the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if session already exists
            cursor.execute("SELECT 1 FROM study_sessions WHERE id = ?", (session.id,))
            exists = cursor.fetchone() is not None
            
            session_dict = session.to_dict()
            
            if exists:
                # Update existing session
                cursor.execute('''
                UPDATE study_sessions 
                SET end_time = ?, cards_studied = ?, cards_correct = ?
                WHERE id = ?
                ''', (
                    session_dict['end_time'],
                    session_dict['cards_studied'],
                    session_dict['cards_correct'],
                    session_dict['id']
                ))
            else:
                # Insert new session
                cursor.execute('''
                INSERT INTO study_sessions (id, deck_id, start_time, end_time, cards_studied, cards_correct)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    session_dict['id'],
                    session_dict['deck_id'],
                    session_dict['start_time'],
                    session_dict['end_time'],
                    session_dict['cards_studied'],
                    session_dict['cards_correct']
                ))
            
            # If session is complete, update the deck's last_studied timestamp
            if session.end_time:
                cursor.execute(
                    "UPDATE decks SET last_studied = ? WHERE id = ?", 
                    (session.end_time.isoformat(), session.deck_id)
                )
            
            conn.commit()
            return True
    
    @handle_errors(show_dialog=False, log_exception=True)
    def get_study_sessions(self, deck_id: Optional[str] = None) -> List[StudySession]:
        """Get all study sessions, optionally filtered by deck ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if deck_id:
                cursor.execute('''
                SELECT * FROM study_sessions 
                WHERE deck_id = ? 
                ORDER BY start_time DESC
                ''', (deck_id,))
            else:
                cursor.execute("SELECT * FROM study_sessions ORDER BY start_time DESC")
                
            rows = cursor.fetchall()
            
            return [StudySession.from_dict(dict(row)) for row in rows]
    
    @handle_errors(show_dialog=False, log_exception=True)
    def get_deck_stats(self, deck_id: str) -> Dict:
        """Get study statistics for a deck."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get total number of cards
            cursor.execute("SELECT COUNT(*) FROM flashcards WHERE deck_id = ?", (deck_id,))
            total_cards = cursor.fetchone()[0]
            
            # Get cards reviewed
            cursor.execute(
                "SELECT COUNT(*) FROM flashcards WHERE deck_id = ? AND last_reviewed IS NOT NULL", 
                (deck_id,)
            )
            reviewed_cards = cursor.fetchone()[0]
            
            # Get study sessions
            cursor.execute('''
            SELECT COUNT(*), SUM(cards_studied), SUM(cards_correct)
            FROM study_sessions 
            WHERE deck_id = ? AND end_time IS NOT NULL
            ''', (deck_id,))
            
            row = cursor.fetchone()
            if row and row[0] > 0:
                session_count = row[0]
                total_studied = row[1] or 0
                total_correct = row[2] or 0
                accuracy = (total_correct / total_studied * 100) if total_studied > 0 else 0
            else:
                session_count = 0
                total_studied = 0
                total_correct = 0
                accuracy = 0
            
            return {
                'total_cards': total_cards,
                'reviewed_cards': reviewed_cards,
                'session_count': session_count,
                'total_studied': total_studied, 
                'total_correct': total_correct,
                'accuracy': accuracy
            }
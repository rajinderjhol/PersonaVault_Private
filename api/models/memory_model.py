from sqlalchemy import Column, Integer, String, Text, JSON, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from contextlib import contextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Define the base class for SQLAlchemy models
Base = declarative_base()

class Memory(Base):
    """
    Memory model representing a memory entry in the database.
    Each memory is associated with a user and contains metadata such as type, content, tags, and privacy level.
    """
    __tablename__ = 'memories'

    id = Column(Integer, primary_key=True)  # Unique identifier for the memory
    user_id = Column(String, ForeignKey('users.id'), nullable=False)  # Associate memories with a user
    memory_type = Column(String, nullable=False)  # Type of memory (e.g., "development", "general")
    content = Column(Text, nullable=False)  # The actual memory (e.g., code snippet, discussion)
    tags = Column(JSON)  # Tags for organizing memories (e.g., ["code", "goal", "bug"])
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # Timestamp for when the memory was created
    embedding = Column(JSON)  # Embedding for semantic search
    privacy_level = Column(String, nullable=False)  # Privacy level (e.g., "public", "private")
    expiry_days = Column(Integer)  # Number of days until the memory expires

    # Relationship to the User model (if you have one)
    user = relationship("User", back_populates="memories")

    def __init__(self, user_id, content, memory_type, tags=None, privacy_level="public", expiry_days=7):
        """
        Initialize a new Memory instance.

        :param user_id: The ID of the user associated with this memory.
        :param content: The content of the memory (e.g., code snippet, discussion).
        :param memory_type: The type of memory (e.g., "development", "general").
        :param tags: Optional tags for organizing memories (e.g., ["code", "goal", "bug"]).
        :param privacy_level: The privacy level of the memory (default is "public").
        :param expiry_days: The number of days until the memory expires (default is 7).
        """
        self.user_id = user_id
        self.content = content
        self.memory_type = memory_type
        self.tags = tags if tags else []
        self.privacy_level = privacy_level
        self.expiry_days = expiry_days
        logger.debug(f"Memory instance created for user_id: {user_id}, type: {memory_type}")

    def save(self, session):
        """
        Save the memory to the database using the provided SQLAlchemy session.

        :param session: The SQLAlchemy session to use for database operations.
        """
        try:
            session.add(self)
            session.commit()
            logger.info(f"Memory saved successfully: {self.id}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving memory: {e}")
            raise

    def delete(self, session):
        """
        Delete the memory from the database using the provided SQLAlchemy session.

        :param session: The SQLAlchemy session to use for database operations.
        """
        try:
            session.delete(self)
            session.commit()
            logger.info(f"Memory deleted successfully: {self.id}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting memory: {e}")
            raise

    @classmethod
    def get_by_id(cls, session, memory_id):
        """
        Retrieve a memory by its ID.

        :param session: The SQLAlchemy session to use for database operations.
        :param memory_id: The ID of the memory to retrieve.
        :return: The Memory instance if found, otherwise None.
        """
        try:
            memory = session.query(cls).filter_by(id=memory_id).first()
            if memory:
                logger.info(f"Memory retrieved successfully: {memory_id}")
            else:
                logger.warning(f"Memory not found: {memory_id}")
            return memory
        except Exception as e:
            logger.error(f"Error retrieving memory: {e}")
            raise

    @classmethod
    def get_by_user_id(cls, session, user_id):
        """
        Retrieve all memories associated with a specific user.

        :param session: The SQLAlchemy session to use for database operations.
        :param user_id: The ID of the user whose memories to retrieve.
        :return: A list of Memory instances.
        """
        try:
            memories = session.query(cls).filter_by(user_id=user_id).all()
            logger.info(f"Retrieved {len(memories)} memories for user: {user_id}")
            return memories
        except Exception as e:
            logger.error(f"Error retrieving memories for user {user_id}: {e}")
            raise

    @classmethod
    def search_by_tags(cls, session, tags):
        """
        Search for memories by tags.

        :param session: The SQLAlchemy session to use for database operations.
        :param tags: A list of tags to search for.
        :return: A list of Memory instances that match the tags.
        """
        try:
            memories = session.query(cls).filter(cls.tags.contains(tags)).all()
            logger.info(f"Found {len(memories)} memories with tags: {tags}")
            return memories
        except Exception as e:
            logger.error(f"Error searching memories by tags: {e}")
            raise

    @classmethod
    def delete_expired_memories(cls, session):
        """
        Delete memories that have expired.

        :param session: The SQLAlchemy session to use for database operations.
        """
        try:
            expired_memories = session.query(cls).filter(
                cls.created_at < datetime.utcnow() - timedelta(days=cls.expiry_days)
            ).all()

            for memory in expired_memories:
                session.delete(memory)

            session.commit()
            logger.info(f"Deleted {len(expired_memories)} expired memories.")
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting expired memories: {e}")
            raise

# Context manager for database sessions
@contextmanager
def get_db_session():
    """
    Context manager for handling SQLAlchemy database sessions.
    Ensures the session is properly closed after use, even if an error occurs.
    """
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()
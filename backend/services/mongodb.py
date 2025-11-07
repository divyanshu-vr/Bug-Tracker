"""MongoDB connection service with connection pooling and error handling."""

from typing import Optional, Protocol
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from pymongo.database import Database
from pymongo.collection import Collection
from abc import ABC, abstractmethod
import logging
import time

logger = logging.getLogger(__name__)


class DatabaseService(ABC):
    """Abstract interface for database operations."""

    @abstractmethod
    def connect(self) -> None:
        """Establish database connection."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if database is connected."""
        pass

    @property
    @abstractmethod
    def bugs(self) -> Collection:
        """Get bugs collection."""
        pass

    @property
    @abstractmethod
    def comments(self) -> Collection:
        """Get comments collection."""
        pass


class MongoDBService(DatabaseService):
    """Manages MongoDB Atlas connections and operations."""

    def __init__(
        self,
        uri: str,
        database_name: str = "bugtrackr",
        max_retries: int = 3,
        retry_delay: int = 2
    ):
        """Initialize MongoDB service with connection URI.
        
        Args:
            uri: MongoDB connection string
            database_name: Name of the database to use
            max_retries: Maximum connection retry attempts
            retry_delay: Delay between retries in seconds
        """
        self._uri = uri
        self._database_name = database_name
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    def connect(self) -> None:
        """Establish connection to MongoDB with retry logic.
        
        Raises:
            ConnectionFailure: If connection cannot be established after retries
        """
        for attempt in range(self._max_retries):
            try:
                self._client = MongoClient(
                    self._uri,
                    serverSelectionTimeoutMS=5000,
                    maxPoolSize=50,
                    minPoolSize=10,
                    retryWrites=True
                )
                # Verify connection
                self._client.admin.command('ping')
                self._db = self._client[self._database_name]
                self._initialize_collections()
                logger.info(f"Successfully connected to MongoDB database: {self._database_name}")
                return
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay)
                else:
                    logger.error("Failed to connect to MongoDB after all retries")
                    raise ConnectionFailure(f"Could not connect to MongoDB: {e}")

    def _initialize_collections(self) -> None:
        """Initialize database collections with indexes."""
        if self._db is None:
            raise RuntimeError("Database not connected")

        # Create bugs collection with indexes
        bugs_collection = self._db["bugs"]
        bugs_collection.create_index("projectId")
        bugs_collection.create_index("status")
        bugs_collection.create_index("assignedTo")
        bugs_collection.create_index("createdAt")

        # Create comments collection with indexes
        comments_collection = self._db["comments"]
        comments_collection.create_index("bugId")
        comments_collection.create_index("createdAt")

        logger.info("Database collections initialized with indexes")

    def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed")

    @property
    def bugs(self) -> Collection:
        """Get bugs collection.
        
        Returns:
            Bugs collection instance
            
        Raises:
            RuntimeError: If database is not connected
        """
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db["bugs"]

    @property
    def comments(self) -> Collection:
        """Get comments collection.
        
        Returns:
            Comments collection instance
            
        Raises:
            RuntimeError: If database is not connected
        """
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db["comments"]

    def is_connected(self) -> bool:
        """Check if database connection is active.
        
        Returns:
            True if connected, False otherwise
        """
        if self._client is None:
            return False
        try:
            self._client.admin.command('ping')
            return True
        except Exception:
            return False


def create_mongodb_service(uri: str, database_name: str = "bugtrackr") -> MongoDBService:
    """Factory function to create MongoDB service instance.
    
    Args:
        uri: MongoDB connection string
        database_name: Name of the database to use
        
    Returns:
        MongoDBService instance
    """
    return MongoDBService(uri, database_name)

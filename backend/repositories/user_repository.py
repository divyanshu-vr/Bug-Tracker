"""Repository for User entity data access."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging
import json

from backend.models.bug_model import User
from backend.services.collection_db import CollectionDBService

logger = logging.getLogger(__name__)

class UserRepository:
    """Repository for user data access using AppFlyte Collection DB.
    
    Note: Users are predefined in Collection DB. This repository
    only provides read operations for validation purposes.
    No user creation or modification is supported.
    """

    def __init__(self, collection_service: CollectionDBService):
        """Initialize user repository.
        
        Args:
            collection_service: CollectionDBService instance for data operations
        """
        self._service = collection_service
        self._collection = ""  # Use base collection (ameya_tests)
        self._entity_type = "user"

    def _collection_item_to_user(self, item: Dict[str, Any]) -> User:
        """Transform collection item to User model.
        
        Args:
            item: Collection item dictionary
            
        Returns:
            User model instance
        """
        
        # Handle __auto_id__ from AppFlyte
        user_id = item.get("__auto_id__")
        
        # Parse JSON from description field (workaround for limited schema)
        description = item.get("description", "{}")
        try:
            data = json.loads(description) if isinstance(description, str) else {}
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse description as JSON for user {user_id}")
            data = {}
        
        # Parse created_at with robust type checking
        created_at = item.get("created_at")
        if created_at is None:
            created_at = datetime.now(timezone.utc)  # Fallback to aware datetime
        elif isinstance(created_at, datetime):
            pass  # Already a datetime, no parsing needed
        elif isinstance(created_at, str):
            try:
                # Parse ISO format string (preserves timezone info)
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                # Fallback for invalid format or legacy format with space instead of T
                try:
                    created_at = datetime.fromisoformat(created_at.replace(" ", "T"))
                except ValueError:
                    logger.warning(f"Invalid datetime format for user {user_id}, using current time")
                    created_at = datetime.now(timezone.utc)
        else:
            # Fallback for unexpected types
            logger.warning(
                f"Unexpected type for created_at in user {user_id}: {type(created_at).__name__}, "
                f"using current time"
            )
            created_at = datetime.now(timezone.utc)
        
        return User(
            _id=user_id,
            name=item.get("name", ""),
            email=data.get("email", ""),
            role=data.get("role", ""),
            createdAt=created_at
        )

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve user by ID for validation.
        
        Args:
            user_id: User ID (__auto_id__)
            
        Returns:
            User model or None if not found
        """
        logger.info(f"Retrieving user by ID: {user_id}")
        
        item = await self._service.get_item_by_id(self._collection, user_id)
        
        if item is None:
            logger.warning(f"User not found: {user_id}")
            return None
        
        return self._collection_item_to_user(item)

    async def get_all(self) -> List[User]:
        """Retrieve all predefined users.
        
        Returns:
            List of User models
        """
        import json
        
        logger.info("Retrieving all users")
        
        # Fetch all items from collection
        items = await self._service.get_all_items(self._collection)
        
        # Filter by type (stored in JSON description) and transform to User models
        users = []
        for item in items:
            item_id = item.get("__auto_id__", "unknown")
            description = item.get("description", "")
            
            # Skip empty descriptions
            if not description:
                continue
            
            # Always attempt JSON parsing
            try:
                data = json.loads(description)
                
                # Only process items with matching type
                if data.get("type") == self._entity_type:
                    try:
                        users.append(self._collection_item_to_user(item))
                    except ValueError as e:
                        # Skip malformed user data but log the error
                        logger.warning(f"Skipping malformed user data for item {item_id}: {e}")
                        continue
                        
            except json.JSONDecodeError as e:
                # Log parsing failures with context
                logger.warning(
                    f"Failed to parse description as JSON for item {item_id}: {e}. "
                    f"Description: {description[:100]}..."
                )
                continue
        
        logger.info(f"Retrieved {len(users)} valid users")
        return users

    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve user by email.
        
        Filters in-memory since Collection DB doesn't support query filters.
        
        Args:
            email: User email address
            
        Returns:
            User model or None if not found
        """
        logger.info(f"Retrieving user by email: {email}")
        
        # Fetch all users and filter in-memory
        users = await self.get_all()
        
        for user in users:
            if user.email == email:
                logger.info(f"Found user with email: {email}")
                return user
        
        logger.warning(f"User not found with email: {email}")
        return None

    async def get_by_role(self, role: str) -> List[User]:
        """Retrieve users by role.
        
        Filters in-memory since Collection DB doesn't support query filters.
        
        Args:
            role: User role (e.g., "admin", "developer", "tester")
            
        Returns:
            List of User models with the specified role
        """
        logger.info(f"Retrieving users with role: {role}")
        
        # Fetch all users and filter in-memory
        users = await self.get_all()
        
        # Filter by role
        filtered_users = [user for user in users if user.role == role]
        
        logger.info(f"Retrieved {len(filtered_users)} users with role '{role}'")
        return filtered_users

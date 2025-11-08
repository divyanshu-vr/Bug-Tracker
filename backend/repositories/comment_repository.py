"""Repository for Comment entity data access."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

from backend.models.bug_model import Comment
from backend.services.collection_db import CollectionDBService

logger = logging.getLogger(__name__)


class CommentRepository:
    """Repository for comment data access using AppFlyte Collection DB.
    
    Handles transformation between Comment models and collection items,
    including datetime serialization.
    """

    def __init__(self, collection_service: CollectionDBService):
        """Initialize comment repository.
        
        Args:
            collection_service: CollectionDBService instance for data operations
        """
        self._service = collection_service
        self._collection = ""  # Use base collection (ameya_tests)
        self._entity_type = "comment"

    def _comment_to_collection_item(self, comment: Comment) -> Dict[str, Any]:
        """Transform Comment model to collection item format.
        
        Args:
            comment: Comment model instance
            
        Returns:
            Dictionary in collection item format
        """
        return {
            "type": self._entity_type,
            "bugId": comment.bugId,
            "authorId": comment.authorId,
            "message": comment.message,
            "createdAt": comment.createdAt.isoformat()
        }

    def _collection_item_to_comment(self, item: Dict[str, Any]) -> Comment:
        """Transform collection item to Comment model.
        
        Args:
            item: Collection item dictionary
            
        Returns:
            Comment model instance
        """
        # Handle __auto_id__ from AppFlyte
        if "__auto_id__" in item:
            item["_id"] = item.pop("__auto_id__")
        
        # Parse datetime string
        if isinstance(item.get("createdAt"), str):
            item["createdAt"] = datetime.fromisoformat(item["createdAt"])
        
        return Comment(**item)

    async def create(self, comment: Comment) -> Comment:
        """Create a new comment.
        
        Args:
            comment: Comment model instance (without ID)
            
        Returns:
            Comment model with generated ID
            
        Raises:
            ValueError: If comment creation fails
        """
        logger.info(f"Creating comment for bug: {comment.bugId}")
        
        # Transform to collection item format
        item_data = self._comment_to_collection_item(comment)
        
        # Create in collection DB
        created_item = await self._service.create_item(self._collection, item_data)
        
        # Transform back to Comment model
        return self._collection_item_to_comment(created_item)

    async def get_by_id(self, comment_id: str) -> Optional[Comment]:
        """Retrieve comment by ID.
        
        Args:
            comment_id: Comment ID (__auto_id__)
            
        Returns:
            Comment model or None if not found
        """
        logger.info(f"Retrieving comment by ID: {comment_id}")
        
        item = await self._service.get_item_by_id(self._collection, comment_id)
        
        if item is None:
            logger.warning(f"Comment not found: {comment_id}")
            return None
        
        return self._collection_item_to_comment(item)

    async def get_by_bug_id(self, bug_id: str) -> List[Comment]:
        """Retrieve all comments for a bug.
        
        Filters in-memory and sorts by createdAt.
        
        Args:
            bug_id: Bug ID to filter comments
            
        Returns:
            List of Comment models sorted by createdAt
        """
        logger.info(f"Retrieving comments for bug: {bug_id}")
        
        # Fetch all items from collection
        items = await self._service.get_all_items(self._collection)
        
        # Filter by type and transform to Comment models
        comments = [
            self._collection_item_to_comment(item) 
            for item in items 
            if item.get("type") == self._entity_type
        ]
        
        # Filter by bug ID
        comments = [comment for comment in comments if comment.bugId == bug_id]
        
        # Sort by createdAt
        comments.sort(key=lambda c: c.createdAt)
        
        logger.info(f"Retrieved {len(comments)} comments for bug {bug_id}")
        return comments

"""Repository for ActivityLog entity data access."""

from typing import List, Dict, Any
from datetime import datetime, timezone
import logging

from backend.models.bug_model import ActivityLog
from backend.services.collection_db import CollectionDBService

logger = logging.getLogger(__name__)


class ActivityLogRepository:
    """Repository for activity log data access using AppFlyte Collection DB.
    
    Handles transformation between ActivityLog models and collection items,
    including datetime serialization.
    """

    def __init__(self, collection_service: CollectionDBService):
        """Initialize activity log repository.
        
        Args:
            collection_service: CollectionDBService instance for data operations
        """
        self._service = collection_service
        self._collection = ""  # Use base collection (ameya_tests)
        self._entity_type = "activity_log"

    def _activity_log_to_collection_item(self, activity_log: ActivityLog) -> Dict[str, Any]:
        """Transform ActivityLog model to collection item format.
        
        Args:
            activity_log: ActivityLog model instance
            
        Returns:
            Dictionary in collection item format
        """
        return {
            "type": self._entity_type,
            "bugId": activity_log.bugId,
            "action": activity_log.action,
            "performedBy": activity_log.performedBy,
            "timestamp": activity_log.timestamp.isoformat()
        }

    def _collection_item_to_activity_log(self, item: Dict[str, Any]) -> ActivityLog:
        """Transform collection item to ActivityLog model.
        
        Args:
            item: Collection item dictionary
            
        Returns:
            ActivityLog model instance
        """
        # Handle __auto_id__ from AppFlyte
        if "__auto_id__" in item:
            item["_id"] = item.pop("__auto_id__")
        
        # Parse datetime string
        if isinstance(item.get("timestamp"), str):
            item["timestamp"] = datetime.fromisoformat(item["timestamp"])
        
        return ActivityLog(**item)

    async def create(self, activity_log: ActivityLog) -> ActivityLog:
        """Create a new activity log entry.
        
        Args:
            activity_log: ActivityLog model instance (without ID)
            
        Returns:
            ActivityLog model with generated ID
            
        Raises:
            ValueError: If activity log creation fails
        """
        logger.info(f"Creating activity log for bug: {activity_log.bugId} - {activity_log.action}")
        
        # Transform to collection item format
        item_data = self._activity_log_to_collection_item(activity_log)
        
        # Create in collection DB
        created_item = await self._service.create_item(self._collection, item_data)
        
        # Transform back to ActivityLog model
        return self._collection_item_to_activity_log(created_item)

    async def get_by_bug_id(self, bug_id: str) -> List[ActivityLog]:
        """Retrieve activity logs for a bug.
        
        Filters in-memory and sorts by timestamp (descending).
        
        Args:
            bug_id: Bug ID to filter activity logs
            
        Returns:
            List of ActivityLog models sorted by timestamp (newest first)
        """
        logger.info(f"Retrieving activity logs for bug: {bug_id}")
        
        # Fetch all items from collection
        items = await self._service.get_all_items(self._collection)
        
        # Filter by type and transform to ActivityLog models
        logs = [
            self._collection_item_to_activity_log(item) 
            for item in items 
            if item.get("type") == self._entity_type
        ]
        
        # Filter by bug ID
        logs = [log for log in logs if log.bugId == bug_id]
        
        # Sort by timestamp (newest first)
        logs.sort(key=lambda l: l.timestamp, reverse=True)
        
        logger.info(f"Retrieved {len(logs)} activity logs for bug {bug_id}")
        return logs

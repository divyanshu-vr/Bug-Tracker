"""Repository for Bug entity data access."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

from backend.models.bug_model import Bug, BugStatus, BugPriority, BugSeverity
from backend.services.collection_db import CollectionDBService

logger = logging.getLogger(__name__)


class BugRepository:
    """Repository for bug data access using AppFlyte Collection DB.
    
    Handles transformation between Bug models and collection items,
    including datetime serialization and enum conversions.
    """

    def __init__(self, collection_service: CollectionDBService):
        """Initialize bug repository.
        
        Args:
            collection_service: CollectionDBService instance for data operations
        """
        self._service = collection_service
        self._collection = ""  # Use base collection (ameya_tests)
        self._entity_type = "bug"

    def _bug_to_collection_item(self, bug: Bug) -> Dict[str, Any]:
        """Transform Bug model to collection item format.
        
        Args:
            bug: Bug model instance
            
        Returns:
            Dictionary in collection item format
        """
        return {
            "type": self._entity_type,
            "title": bug.title,
            "description": bug.description,
            "status": bug.status.value,
            "priority": bug.priority.value,
            "severity": bug.severity.value,
            "projectId": bug.projectId,
            "reportedBy": bug.reportedBy,
            "assignedTo": bug.assignedTo,
            "tags": bug.tags,
            "validated": bug.validated,
            "createdAt": bug.createdAt.isoformat(),
            "updatedAt": bug.updatedAt.isoformat()
        }

    def _collection_item_to_bug(self, item: Dict[str, Any]) -> Bug:
        """Transform collection item to Bug model.
        
        Args:
            item: Collection item dictionary
            
        Returns:
            Bug model instance
            
        Raises:
            ValueError: If datetime fields have unexpected types
        """
        # Handle __auto_id__ from AppFlyte
        if "__auto_id__" in item and "_id" not in item:
            item["_id"] = item["__auto_id__"]
        
        # Parse createdAt with robust type checking
        created_at = item.get("createdAt")
        if created_at is None:
            pass  # Leave as None
        elif isinstance(created_at, datetime):
            pass  # Already a datetime, no parsing needed
        elif isinstance(created_at, str):
            item["createdAt"] = datetime.fromisoformat(created_at)
        else:
            raise ValueError(
                f"Invalid type for createdAt: expected str, datetime, or None, "
                f"got {type(created_at).__name__}"
            )
        
        # Parse updatedAt with robust type checking
        updated_at = item.get("updatedAt")
        if updated_at is None:
            pass  # Leave as None
        elif isinstance(updated_at, datetime):
            pass  # Already a datetime, no parsing needed
        elif isinstance(updated_at, str):
            item["updatedAt"] = datetime.fromisoformat(updated_at)
        else:
            raise ValueError(
                f"Invalid type for updatedAt: expected str, datetime, or None, "
                f"got {type(updated_at).__name__}"
            )
        
        return Bug(**item)

    async def create(self, bug: Bug) -> Bug:
        """Create a new bug.
        
        Args:
            bug: Bug model instance (without ID)
            
        Returns:
            Bug model with generated ID
            
        Raises:
            ValueError: If bug creation fails
        """
        logger.info(f"Creating bug: {bug.title}")
        
        # Transform to collection item format
        item_data = self._bug_to_collection_item(bug)
        
        # Create in collection DB
        created_item = await self._service.create_item(self._collection, item_data)
        
        # Transform back to Bug model
        return self._collection_item_to_bug(created_item)

    async def get_by_id(self, bug_id: str) -> Optional[Bug]:
        """Retrieve bug by ID.
        
        Args:
            bug_id: Bug ID (__auto_id__)
            
        Returns:
            Bug model or None if not found
        """
        logger.info(f"Retrieving bug by ID: {bug_id}")
        
        item = await self._service.get_item_by_id(self._collection, bug_id)
        
        if item is None:
            logger.warning(f"Bug not found: {bug_id}")
            return None
        
        return self._collection_item_to_bug(item)

    async def get_all(
        self,
        project_id: Optional[str] = None,
        status: Optional[BugStatus] = None,
        assigned_to: Optional[str] = None
    ) -> List[Bug]:
        """Retrieve bugs with optional filtering.
        
        Note: Filtering is done in-memory after fetching all items.
        
        Args:
            project_id: Filter by project ID
            status: Filter by bug status
            assigned_to: Filter by assigned user
            
        Returns:
            List of Bug models
        """
        logger.info(f"Retrieving all bugs (filters: projectId={project_id}, status={status}, assignedTo={assigned_to})")
        
        # Fetch all items from collection
        items = await self._service.get_all_items(self._collection)
        
        # Filter by type and transform to Bug models
        bugs = [
            self._collection_item_to_bug(item) 
            for item in items 
            if item.get("type") == self._entity_type
        ]
        
        # Apply in-memory filters
        if project_id is not None:
            bugs = [bug for bug in bugs if bug.projectId == project_id]
        
        if status is not None:
            bugs = [bug for bug in bugs if bug.status == status]
        
        if assigned_to is not None:
            bugs = [bug for bug in bugs if bug.assignedTo == assigned_to]
        
        logger.info(f"Retrieved {len(bugs)} bugs after filtering")
        return bugs

    async def update_status(
        self,
        bug_id: str,
        status: BugStatus,
        updated_at: datetime
    ) -> Bug:
        """Update bug status.
        
        Args:
            bug_id: Bug ID
            status: New status
            updated_at: Update timestamp
            
        Returns:
            Updated Bug model
            
        Raises:
            ValueError: If bug not found
        """
        logger.info(f"Updating bug status: {bug_id} -> {status.value}")
        
        updates = {
            "status": status.value,
            "updatedAt": updated_at.isoformat()
        }
        
        updated_item = await self._service.update_item(self._collection, bug_id, updates)
        return self._collection_item_to_bug(updated_item)

    async def update_assignment(
        self,
        bug_id: str,
        assigned_to: str,
        updated_at: datetime
    ) -> Bug:
        """Update bug assignment.
        
        Args:
            bug_id: Bug ID
            assigned_to: User ID to assign to
            updated_at: Update timestamp
            
        Returns:
            Updated Bug model
            
        Raises:
            ValueError: If bug not found
        """
        logger.info(f"Updating bug assignment: {bug_id} -> {assigned_to}")
        
        updates = {
            "assignedTo": assigned_to,
            "updatedAt": updated_at.isoformat()
        }
        
        updated_item = await self._service.update_item(self._collection, bug_id, updates)
        return self._collection_item_to_bug(updated_item)

    async def update_validation(
        self,
        bug_id: str,
        validated: bool,
        updated_at: datetime
    ) -> Bug:
        """Update bug validation status.
        
        Args:
            bug_id: Bug ID
            validated: Validation status
            updated_at: Update timestamp
            
        Returns:
            Updated Bug model
            
        Raises:
            ValueError: If bug not found
        """
        logger.info(f"Updating bug validation: {bug_id} -> {validated}")
        
        updates = {
            "validated": validated,
            "updatedAt": updated_at.isoformat()
        }
        
        updated_item = await self._service.update_item(self._collection, bug_id, updates)
        return self._collection_item_to_bug(updated_item)

    async def update_fields(
        self,
        bug_id: str,
        updates: Dict[str, Any]
    ) -> Bug:
        """Update multiple bug fields.
        
        Args:
            bug_id: Bug ID
            updates: Dictionary of field names to new values
            
        Returns:
            Updated Bug model
            
        Raises:
            ValueError: If bug not found or updates is empty
        """
        logger.info(f"Updating bug fields: {bug_id} with {len(updates)} field(s)")
        
        # Validate updates is not empty (fail-fast)
        if not updates:
            raise ValueError("updates cannot be empty")
        
        # Serialize datetime and enum values
        serialized_updates = {}
        for key, value in updates.items():
            if isinstance(value, datetime):
                serialized_updates[key] = value.isoformat()
            elif hasattr(value, 'value'):  # Enum
                serialized_updates[key] = value.value
            else:
                serialized_updates[key] = value
        
        updated_item = await self._service.update_item(self._collection, bug_id, serialized_updates)
        return self._collection_item_to_bug(updated_item)

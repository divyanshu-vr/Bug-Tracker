"""Repository for Project entity data access."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging
import json

from backend.models.bug_model import Project
from backend.services.collection_db import CollectionDBService

logger = logging.getLogger(__name__)


class ProjectRepository:
    """Repository for project data access using AppFlyte Collection DB.
    
    Handles transformation between Project models and collection items,
    including datetime serialization.
    """

    def __init__(self, collection_service: CollectionDBService):
        """Initialize project repository.
        
        Args:
            collection_service: CollectionDBService instance for data operations
        """
        self._service = collection_service
        self._collection = ""  # Use base collection (ameya_tests)
        self._entity_type = "project"

    def _project_to_collection_item(self, project: Project) -> Dict[str, Any]:
        """Transform Project model to collection item format.
        
        Args:
            project: Project model instance
            
        Returns:
            Dictionary in collection item format
        """
        
        # Store structured data as JSON in description field
        data = {
            "type": self._entity_type,
            "description": project.description,
            "createdBy": project.createdBy
        }
        
        return {
            "name": project.name,
            "description": json.dumps(data),
            "created_at": project.createdAt.isoformat()  # Preserves timezone info
        }

    def _collection_item_to_project(self, item: Dict[str, Any]) -> Project:
        """Transform collection item to Project model.
        
        Args:
            item: Collection item dictionary
            
        Returns:
            Project model instance
            
        Raises:
            ValueError: If description field is malformed or required fields are missing
        """
        import json
        from datetime import timezone
        
        # Handle __auto_id__ from AppFlyte
        project_id = item.get("__auto_id__")
        
        # Parse JSON from description field (workaround for limited schema)
        description_field = item.get("description", "{}")
        try:
            data = json.loads(description_field) if isinstance(description_field, str) else {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse description as JSON for project {project_id}: {e}")
            raise ValueError(
                f"Invalid project data for project_id '{project_id}': "
                f"description field contains malformed JSON - {str(e)}"
            )
        
        # Validate required fields exist
        description = data.get("description")
        created_by = data.get("createdBy")
        
        if not description:
            raise ValueError(
                f"Invalid project data for project_id '{project_id}': "
                f"missing required field 'description' in description JSON"
            )
        
        if not created_by:
            raise ValueError(
                f"Invalid project data for project_id '{project_id}': "
                f"missing required field 'createdBy' in description JSON"
            )
        
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
                # Fallback for invalid format
                logger.warning(f"Invalid datetime format for project {project_id}, using current time")
                created_at = datetime.now(timezone.utc)
        else:
            # Fallback for unexpected types
            logger.warning(
                f"Unexpected type for created_at in project {project_id}: {type(created_at).__name__}, "
                f"using current time"
            )
            created_at = datetime.now(timezone.utc)
        
        return Project(
            _id=project_id,
            name=item.get("name", ""),
            description=description,
            createdBy=created_by,
            createdAt=created_at
        )

    async def create(self, project: Project) -> Project:
        """Create a new project.
        
        Args:
            project: Project model instance (without ID)
            
        Returns:
            Project model with generated ID
            
        Raises:
            ValueError: If project creation fails
        """
        logger.info(f"Creating project: {project.name}")
        
        # Transform to collection item format
        item_data = self._project_to_collection_item(project)
        
        # Create in collection DB
        created_item = await self._service.create_item(self._collection, item_data)
        
        # Transform back to Project model
        return self._collection_item_to_project(created_item)

    async def get_by_id(self, project_id: str) -> Optional[Project]:
        """Retrieve project by ID.
        
        Args:
            project_id: Project ID (__auto_id__)
            
        Returns:
            Project model or None if not found or data is malformed
        """
        logger.info(f"Retrieving project by ID: {project_id}")
        
        item = await self._service.get_item_by_id(self._collection, project_id)
        
        if item is None:
            logger.warning(f"Project not found: {project_id}")
            return None
        
        try:
            return self._collection_item_to_project(item)
        except ValueError as e:
            logger.error(f"Failed to parse project {project_id}: {e}")
            return None

    async def get_all(self) -> List[Project]:
        """Retrieve all projects.
        
        Returns:
            List of Project models
        """
        import json
        
        logger.info("Retrieving all projects")
        
        # Fetch all items from collection
        items = await self._service.get_all_items(self._collection)
        
        # Filter by type (stored in JSON description) and transform to Project models
        projects = []
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
                        projects.append(self._collection_item_to_project(item))
                    except ValueError as e:
                        # Skip malformed project data but log the error
                        logger.warning(f"Skipping malformed project data for item {item_id}: {e}")
                        continue
                        
            except json.JSONDecodeError as e:
                # Log parsing failures with context
                logger.warning(
                    f"Failed to parse description as JSON for item {item_id}: {e}. "
                    f"Description: {description[:100]}..."
                )
                continue
        
        logger.info(f"Retrieved {len(projects)} valid projects")
        return projects

    async def update(
        self,
        project_id: str,
        updates: Dict[str, Any]
    ) -> Project:
        """Update project fields.
        
        Args:
            project_id: Project ID
            updates: Dictionary of field names to new values
            
        Returns:
            Updated Project model
            
        Raises:
            ValueError: If project not found or updates is empty
        """
        logger.info(f"Updating project: {project_id} with {len(updates)} field(s)")
        
        # Validate updates is not empty (fail-fast)
        if not updates:
            raise ValueError("updates cannot be empty")
        
        # Serialize datetime values
        serialized_updates = {}
        for key, value in updates.items():
            if isinstance(value, datetime):
                serialized_updates[key] = value.isoformat()
            else:
                serialized_updates[key] = value
        
        updated_item = await self._service.update_item(self._collection, project_id, serialized_updates)
        return self._collection_item_to_project(updated_item)

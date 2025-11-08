"""Repository for Project entity data access."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

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
        import json
        
        # Store structured data as JSON in description field
        data = {
            "type": self._entity_type,
            "description": project.description,
            "createdBy": project.createdBy
        }
        
        return {
            "name": project.name,
            "description": json.dumps(data),
            "created_at": project.createdAt.strftime("%Y-%m-%d %H:%M:%S")
        }

    def _collection_item_to_project(self, item: Dict[str, Any]) -> Project:
        """Transform collection item to Project model.
        
        Args:
            item: Collection item dictionary
            
        Returns:
            Project model instance
        """
        import json
        
        # Handle __auto_id__ from AppFlyte
        project_id = item.get("__auto_id__")
        
        # Parse JSON from description field (workaround for limited schema)
        description_field = item.get("description", "{}")
        try:
            data = json.loads(description_field) if isinstance(description_field, str) else {}
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse description as JSON for project {project_id}")
            data = {}
        
        # Parse datetime
        created_at = item.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace(" ", "T"))
        else:
            created_at = datetime.now(timezone.utc)
        
        return Project(
            _id=project_id,
            name=item.get("name", ""),
            description=data.get("description", ""),
            createdBy=data.get("createdBy", ""),
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
            Project model or None if not found
        """
        logger.info(f"Retrieving project by ID: {project_id}")
        
        item = await self._service.get_item_by_id(self._collection, project_id)
        
        if item is None:
            logger.warning(f"Project not found: {project_id}")
            return None
        
        return self._collection_item_to_project(item)

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
            description = item.get("description", "")
            try:
                if description and description.startswith("{"):
                    data = json.loads(description)
                    if data.get("type") == self._entity_type:
                        projects.append(self._collection_item_to_project(item))
            except json.JSONDecodeError:
                continue
        
        logger.info(f"Retrieved {len(projects)} projects")
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
        
        # Serialize datetime values
        serialized_updates = {}
        for key, value in updates.items():
            if isinstance(value, datetime):
                serialized_updates[key] = value.isoformat()
            else:
                serialized_updates[key] = value
        
        updated_item = await self._service.update_item(self._collection, project_id, serialized_updates)
        return self._collection_item_to_project(updated_item)

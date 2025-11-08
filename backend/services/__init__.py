"""Services package for external integrations."""

from dataclasses import dataclass
from .collection_db import (
    CollectionDBService,
    AppFlyteCollectionDB,
    create_collection_db_service
)

__all__ = [
    # Interfaces
    "CollectionDBService",
    # Implementations
    "AppFlyteCollectionDB",
    # Factory functions
    "create_collection_db_service",
    # Service container
    "ServiceContainer",
    "create_service_container",
]


@dataclass
class ServiceContainer:
    """Container for all application services.
    
    Encapsulates service dependencies for dependency injection.
    """
    
    # Data persistence (AppFlyte Collection DB)
    collection_db: CollectionDBService
    
    # Repositories
    bug_repository: 'BugRepository'
    comment_repository: 'CommentRepository'
    project_repository: 'ProjectRepository'
    activity_log_repository: 'ActivityLogRepository'
    user_repository: 'UserRepository'
    
    async def close(self) -> None:
        """Close all service connections.
        
        Ensures all resources are cleaned up even if individual cleanup operations fail.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Close Collection DB client
        try:
            await self.collection_db.close()
        except Exception as e:
            logger.error(f"Error closing Collection DB client: {e}")


def create_service_container(
    appflyte_collection_base_url: str,
    appflyte_collection_api_key: str
) -> ServiceContainer:
    """Create and initialize service container with all dependencies.
    
    This function performs synchronous initialization and should be called
    during application startup (e.g., in FastAPI lifespan context).
    
    Args:
        appflyte_collection_base_url: AppFlyte Collection DB base URL (for data storage)
        appflyte_collection_api_key: AppFlyte Collection DB Bearer token
        
    Returns:
        ServiceContainer with initialized services
        
    Raises:
        ValueError: If any service initialization fails
    """
    # Import repositories here to avoid circular imports
    from backend.repositories.bug_repository import BugRepository
    from backend.repositories.comment_repository import CommentRepository
    from backend.repositories.project_repository import ProjectRepository
    from backend.repositories.activity_log_repository import ActivityLogRepository
    from backend.repositories.user_repository import UserRepository
    
    # Create Collection DB service (for data storage)
    collection_db = create_collection_db_service(
        base_url=appflyte_collection_base_url,
        api_key=appflyte_collection_api_key
    )
    
    # Instantiate repositories with collection_db
    bug_repository = BugRepository(collection_db)
    comment_repository = CommentRepository(collection_db)
    project_repository = ProjectRepository(collection_db)
    activity_log_repository = ActivityLogRepository(collection_db)
    user_repository = UserRepository(collection_db)
    
    return ServiceContainer(
        collection_db=collection_db,
        bug_repository=bug_repository,
        comment_repository=comment_repository,
        project_repository=project_repository,
        activity_log_repository=activity_log_repository,
        user_repository=user_repository
    )

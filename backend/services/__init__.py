"""Services package for external integrations."""

from dataclasses import dataclass
from .mongodb import (
    DatabaseService,
    MongoDBService,
    create_mongodb_service
)
from .appflyte_client import (
    ProjectAPIClient,
    AppFlyteClient,
    create_appflyte_client
)
from .cloudinary_service import (
    ImageStorageService,
    CloudinaryService,
    create_cloudinary_service
)
from .collection_db import (
    CollectionDBService,
    AppFlyteCollectionDB,
    create_collection_db_service
)

__all__ = [
    # Interfaces
    "DatabaseService",
    "ProjectAPIClient",
    "ImageStorageService",
    "CollectionDBService",
    # Implementations
    "MongoDBService",
    "AppFlyteClient",
    "CloudinaryService",
    "AppFlyteCollectionDB",
    # Factory functions
    "create_mongodb_service",
    "create_appflyte_client",
    "create_cloudinary_service",
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
    
    database: DatabaseService
    project_api: ProjectAPIClient
    image_storage: ImageStorageService
    collection_db: CollectionDBService
    
    async def close(self) -> None:
        """Close all service connections.
        
        Ensures all resources are cleaned up even if individual cleanup operations fail.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Close database connection
        try:
            self.database.disconnect()
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")
        
        # Close API client
        try:
            await self.project_api.close()
        except Exception as e:
            logger.error(f"Error closing API client: {e}")
        
        # Close Collection DB client
        try:
            await self.collection_db.close()
        except Exception as e:
            logger.error(f"Error closing Collection DB client: {e}")


def create_service_container(
    mongodb_uri: str,
    mongodb_database: str,
    appflyte_base_url: str,
    appflyte_api_key: str,
    collection_db_base_url: str,
    collection_db_api_key: str,
    cloudinary_cloud_name: str,
    cloudinary_api_key: str,
    cloudinary_api_secret: str
) -> ServiceContainer:
    """Create and initialize service container with all dependencies.
    
    This function performs synchronous initialization and should be called
    during application startup (e.g., in FastAPI lifespan context).
    
    Args:
        mongodb_uri: MongoDB connection string
        mongodb_database: MongoDB database name
        appflyte_base_url: AppFlyte API base URL
        appflyte_api_key: AppFlyte API key
        collection_db_base_url: Collection DB base URL
        collection_db_api_key: Collection DB Bearer token
        cloudinary_cloud_name: Cloudinary cloud name
        cloudinary_api_key: Cloudinary API key
        cloudinary_api_secret: Cloudinary API secret
        
    Returns:
        ServiceContainer with initialized services
        
    Raises:
        ConnectionFailure: If MongoDB connection fails
        ValueError: If any service initialization fails
    """
    # Create MongoDB service
    database = create_mongodb_service(
        uri=mongodb_uri,
        database_name=mongodb_database
    )
    database.connect()
    
    # Create AppFlyte client
    project_api = create_appflyte_client(
        base_url=appflyte_base_url,
        api_key=appflyte_api_key
    )
    
    # Create Collection DB service
    collection_db = create_collection_db_service(
        base_url=collection_db_base_url,
        api_key=collection_db_api_key
    )
    
    # Create Cloudinary service
    image_storage = create_cloudinary_service(
        cloud_name=cloudinary_cloud_name,
        api_key=cloudinary_api_key,
        api_secret=cloudinary_api_secret
    )
    
    return ServiceContainer(
        database=database,
        project_api=project_api,
        image_storage=image_storage,
        collection_db=collection_db
    )

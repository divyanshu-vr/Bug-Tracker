"""FastAPI application entry point."""

from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import logging

from .services import ServiceContainer, create_service_container
from .config import Config

logger = logging.getLogger(__name__)


def create_app(config: Config) -> FastAPI:
    """Create and configure FastAPI application.
    
    Args:
        config: Application configuration
        
    Returns:
        Configured FastAPI application
    """
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if config.debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Service container will be stored in app state
    services: ServiceContainer | None = None
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan manager for startup and shutdown events."""
        nonlocal services
        
        # Startup
        logger.info("Starting BugTrackr application...")
        try:
            services = create_service_container(
                mongodb_uri=config.mongodb_uri,
                mongodb_database=config.mongodb_database,
                appflyte_base_url=config.appflyte_base_url,
                appflyte_api_key=config.appflyte_api_key,
                cloudinary_cloud_name=config.cloudinary_cloud_name,
                cloudinary_api_key=config.cloudinary_api_key,
                cloudinary_api_secret=config.cloudinary_api_secret
            )
            app.state.services = services
            logger.info("All services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            if services is not None:
                try:
                    await services.close()
                except Exception as cleanup_error:
                    logger.error(f"Error during cleanup of services: {cleanup_error}")
            raise
        
        yield
        
        # Shutdown
        logger.info("Shutting down BugTrackr application...")
        if services:
            await services.close()
        logger.info("All services closed")
    
    # Create FastAPI application
    app = FastAPI(
        title="BugTrackr API",
        description="Bug tracking system with MongoDB, AppFlyte, and Cloudinary integration",
        version="1.0.0",
        lifespan=lifespan
    )
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {"message": "BugTrackr API is running"}
    
    @app.get("/health")
    async def health_check(request: Request):
        """Health check endpoint."""
        services: ServiceContainer = request.app.state.services
        db_connected = services.database.is_connected()
        
        return {
            "status": "healthy" if db_connected else "degraded",
            "database": "connected" if db_connected else "disconnected"
        }
    
    return app

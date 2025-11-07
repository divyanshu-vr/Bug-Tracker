"""FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .services import ServiceContainer, create_service_container
from .config import Config
from .routes import bugs, comments, projects, uploads

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
                collection_db_base_url=config.collection_db_base_url,
                collection_db_api_key=config.collection_db_api_key,
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
    
    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    
    # Register routers
    app.include_router(bugs.router)
    app.include_router(comments.router)
    app.include_router(projects.router)
    app.include_router(uploads.router)
    
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


# Create app instance for uvicorn
config = Config.from_env()
app = create_app(config)

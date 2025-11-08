"""FastAPI application entry point."""

from typing import Any
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .services import ServiceContainer, create_service_container
from .config import Config
from .routes import bugs, comments, projects

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
                appflyte_collection_base_url=config.appflyte_collection_base_url,
                appflyte_collection_api_key=config.appflyte_collection_api_key
            )
            app.state.services = services
            logger.info("All services initialized successfully with AppFlyte Collection DB")
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
        description="Bug tracking system with AppFlyte Collection DB integration",
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
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {"message": "BugTrackr API is running"}
    
    @app.get("/health")
    async def health_check(request: Request):
        """Health check endpoint.
        
        Tests Collection DB connectivity with a lightweight API call.
        Returns detailed status information for monitoring.
        """
        services: ServiceContainer = request.app.state.services
        
        # Test Collection DB connectivity with a real API call
        collection_db_status: str = "unavailable"
        collection_db_error: str | None = None
        
        try:
            # Perform lightweight connectivity test
            # get_all_items will raise httpx.HTTPError if API is unreachable
            await services.collection_db.get_all_items("")
            collection_db_status = "connected"
        except Exception as e:
            collection_db_status = "error"
            collection_db_error = str(e)
            logger.error(f"Collection DB health check failed: {e}")
        
        is_healthy: bool = collection_db_status == "connected"
        
        response: dict[str, Any] = {
            "status": "healthy" if is_healthy else "unhealthy",
            "services": {
                "collection_db": {
                    "status": collection_db_status,
                    "type": "AppFlyte Collection Database"
                }
            }
        }
        
        if collection_db_error:
            response["services"]["collection_db"]["error"] = collection_db_error
        
        return response
    
    return app


# Create app instance for uvicorn
config = Config.from_env()
app = create_app(config)

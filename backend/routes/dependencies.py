"""Shared dependencies for route handlers."""

from typing import Annotated
from fastapi import Depends, Request

from ..services import ServiceContainer


def get_services(request: Request) -> ServiceContainer:
    """Dependency to get service container from app state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        ServiceContainer instance
    """
    return request.app.state.services


# Type aliases for dependency injection
Services = Annotated[ServiceContainer, Depends(get_services)]

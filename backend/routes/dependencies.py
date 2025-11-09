"""Shared dependencies for route handlers."""

from typing import Annotated
from fastapi import Depends, Request

from ..services import ServiceContainer
from ..repositories.user_repository import UserRepository


def get_services(request: Request) -> ServiceContainer:
    """Dependency to get service container from app state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        ServiceContainer instance
    """
    return request.app.state.services


def get_user_repository(services: ServiceContainer = Depends(get_services)) -> UserRepository:
    """Dependency to get user repository.
    
    Args:
        services: ServiceContainer instance
        
    Returns:
        UserRepository instance
    """
    return services.user_repository


# Type aliases for dependency injection
Services = Annotated[ServiceContainer, Depends(get_services)]

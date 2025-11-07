"""Shared dependencies for route handlers."""

from typing import Annotated
from fastapi import Depends, Request, HTTPException
from bson import ObjectId
from bson.errors import InvalidId

from ..services import ServiceContainer


def get_services(request: Request) -> ServiceContainer:
    """Dependency to get service container from app state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        ServiceContainer instance
    """
    return request.app.state.services


def validate_object_id(id_str: str) -> ObjectId:
    """Validate and convert string to MongoDB ObjectId.
    
    Args:
        id_str: String representation of ObjectId
        
    Returns:
        Valid ObjectId
        
    Raises:
        HTTPException: If ID format is invalid
    """
    try:
        return ObjectId(id_str)
    except InvalidId as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ObjectId format: '{id_str}'. {str(e)}"
        )


# Type aliases for dependency injection
Services = Annotated[ServiceContainer, Depends(get_services)]

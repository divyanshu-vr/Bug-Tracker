"""User routes for BugTrackr API."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
import logging

from backend.models.bug_model import User
from backend.repositories.user_repository import UserRepository
from backend.routes.dependencies import get_user_repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=List[User])
async def get_all_users(
    user_repo: UserRepository = Depends(get_user_repository)
) -> List[User]:
    """
    Retrieve all predefined users from Collection DB.
    
    Returns:
        List of User models
    """
    logger.info("GET /api/users - Retrieving all users")
    
    try:
        users = await user_repo.get_all()
        logger.info(f"Successfully retrieved {len(users)} users")
        return users
    except Exception as e:
        logger.error(f"Error retrieving users: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve users: {str(e)}")


@router.get("/{user_id}", response_model=User)
async def get_user_by_id(
    user_id: str,
    user_repo: UserRepository = Depends(get_user_repository)
) -> User:
    """
    Retrieve a specific user by ID.
    
    Args:
        user_id: User ID (__auto_id__)
        
    Returns:
        User model
        
    Raises:
        HTTPException: 404 if user not found
    """
    logger.info(f"GET /api/users/{user_id} - Retrieving user")
    
    try:
        user = await user_repo.get_by_id(user_id)
        
        if user is None:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail=f"User not found: {user_id}")
        
        logger.info(f"Successfully retrieved user: {user_id}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user: {str(e)}")

"""Comment management API endpoints."""

from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, timezone
import logging

from ..models.bug_model import (
    Comment,
    CommentCreateRequest,
    CommentResponse
)
from .dependencies import Services, validate_object_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/comments", tags=["comments"])


@router.post("", response_model=CommentResponse, status_code=201)
async def create_comment(
    comment_request: CommentCreateRequest,
    services: Services
) -> CommentResponse:
    """Create a new comment linked to a bug.
    
    Creates comments linked to specific bugs.
    Updates parent bug timestamp when comments are added.
    Validates comment author through AppFlyte API.
    
    Args:
        comment_request: Comment creation request with bugId, authorId, and message
        services: Injected service container
        
    Returns:
        Created comment data
        
    Raises:
        HTTPException: If validation fails or bug doesn't exist
    """
    try:
        # Validate bug exists
        bug_obj_id = validate_object_id(comment_request.bugId)
        bug_doc = services.database.bugs.find_one({"_id": bug_obj_id})
        
        if not bug_doc:
            raise HTTPException(
                status_code=404,
                detail=f"Bug with ID {comment_request.bugId} not found"
            )
        
        # Validate author exists in AppFlyte
        author = await services.project_api.get_user(comment_request.authorId)
        if not author:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {comment_request.authorId} not found"
            )
        
        # Create comment entity
        comment = Comment(
            bugId=comment_request.bugId,
            authorId=comment_request.authorId,
            message=comment_request.message,
            createdAt=datetime.now(timezone.utc)
        )
        
        # Insert comment into MongoDB
        comment_dict = comment.model_dump(by_alias=True, exclude={"id"})
        result = services.database.comments.insert_one(comment_dict)
        comment_dict["_id"] = str(result.inserted_id)
        
        # Update parent bug timestamp
        services.database.bugs.update_one(
            {"_id": bug_obj_id},
            {"$set": {"updatedAt": datetime.now(timezone.utc)}}
        )
        
        logger.info(
            f"Comment created: {comment_dict['_id']} for bug {comment_request.bugId} "
            f"by {comment_request.authorId}"
        )
        
        return CommentResponse(**comment_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to create comment")


@router.get("/bug/{bug_id}", response_model=List[CommentResponse])
async def get_bug_comments(
    bug_id: str,
    services: Services
) -> List[CommentResponse]:
    """Retrieve all comments for a specific bug.
    
    Args:
        bug_id: Bug identifier
        services: Injected service container
        
    Returns:
        List of comments in chronological order
        
    Raises:
        HTTPException: If bug not found or retrieval fails
    """
    try:
        # Validate bug exists
        bug_obj_id = validate_object_id(bug_id)
        bug_doc = services.database.bugs.find_one({"_id": bug_obj_id})
        
        if not bug_doc:
            raise HTTPException(
                status_code=404,
                detail=f"Bug with ID {bug_id} not found"
            )
        
        # Retrieve comments for this bug
        comments_cursor = services.database.comments.find({"bugId": bug_id})
        comments = []
        
        for comment_doc in comments_cursor:
            comment_doc["_id"] = str(comment_doc["_id"])
            comments.append(CommentResponse(**comment_doc))
        
        # Sort comments by creation time
        comments.sort(key=lambda c: c.createdAt)
        
        logger.info(f"Retrieved {len(comments)} comments for bug {bug_id}")
        
        return comments
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving comments for bug {bug_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve comments")

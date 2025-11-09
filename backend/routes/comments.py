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
from .dependencies import Services

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
    Validates comment author through user repository.
    
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
        bug = await services.bug_repository.get_by_id(comment_request.bugId)
        if not bug:
            raise HTTPException(
                status_code=404,
                detail=f"Bug with ID {comment_request.bugId} not found"
            )
        
        # Validate author exists
        author = await services.user_repository.get_by_id(comment_request.authorId)
        if not author:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {comment_request.authorId} not found"
            )
        
        # Get single timestamp for consistency
        now = datetime.now(timezone.utc)
        
        # Create comment entity
        comment = Comment(
            bugId=comment_request.bugId,
            authorId=comment_request.authorId,
            message=comment_request.message,
            createdAt=now
        )
        
        # Create comment in repository
        created_comment = await services.comment_repository.create(comment)
        
        # Attempt to update parent bug timestamp with compensating rollback
        try:
            await services.bug_repository.update_fields(
                comment_request.bugId,
                {"updatedAt": now}
            )
        except Exception as bug_update_error:
            # Rollback: Delete the created comment to maintain consistency
            logger.error(
                f"Failed to update bug timestamp after comment creation. "
                f"Rolling back comment {created_comment.id}: {bug_update_error}"
            )
            try:
                await services.comment_repository.delete(created_comment.id)
                logger.info(f"Successfully rolled back comment {created_comment.id}")
            except Exception as rollback_error:
                logger.critical(
                    f"CRITICAL: Failed to rollback comment {created_comment.id} "
                    f"after bug update failure. Manual cleanup required. "
                    f"Rollback error: {rollback_error}"
                )
            
            # Re-raise with clear error message
            raise HTTPException(
                status_code=500,
                detail="Failed to create comment: bug timestamp update failed"
            )
        
        logger.info(
            f"Comment created: {created_comment.id} for bug {comment_request.bugId} "
            f"by {comment_request.authorId}"
        )
        
        # Convert to response model
        comment_dict = created_comment.model_dump(by_alias=True)
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
        bug = await services.bug_repository.get_by_id(bug_id)
        if not bug:
            raise HTTPException(
                status_code=404,
                detail=f"Bug with ID {bug_id} not found"
            )
        
        # Retrieve comments for this bug (already sorted by createdAt)
        comments = await services.comment_repository.get_by_bug_id(bug_id)
        
        # Convert to response models
        comment_responses = [
            CommentResponse(**comment.model_dump(by_alias=True))
            for comment in comments
        ]
        
        logger.info(f"Retrieved {len(comment_responses)} comments for bug {bug_id}")
        
        return comment_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving comments for bug {bug_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve comments")

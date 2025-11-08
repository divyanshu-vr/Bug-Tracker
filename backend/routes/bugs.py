"""Bug management API endpoints."""

from fastapi import APIRouter, HTTPException, Form
from typing import Annotated, List
from datetime import datetime, timezone
import logging

from ..models.bug_model import (
    Bug,
    BugStatusUpdateRequest,
    BugAssignRequest,
    BugResponse,
    BugWithCommentsResponse,
    CommentResponse,
    StatusUpdateResponse,
    AssignmentResponse,
    BugStatus,
    BugPriority,
    BugSeverity
)
from .dependencies import Services

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bugs", tags=["bugs"])


def _bug_to_response(bug: Bug) -> BugResponse:
    """Transform Bug model to BugResponse.
    
    Centralizes the transformation logic to follow DRY principle.
    
    Args:
        bug: Bug model instance
        
    Returns:
        BugResponse model
    """
    return BugResponse(
        _id=bug.id,
        title=bug.title,
        description=bug.description,
        projectId=bug.projectId,
        reportedBy=bug.reportedBy,
        assignedTo=bug.assignedTo,
        status=bug.status.value,
        priority=bug.priority.value,
        severity=bug.severity.value,
        tags=bug.tags,
        validated=bug.validated,
        createdAt=bug.createdAt,
        updatedAt=bug.updatedAt
    )


def _comment_to_response(comment) -> CommentResponse:
    """Transform Comment model to CommentResponse.
    
    Centralizes the transformation logic to follow DRY principle.
    
    Args:
        comment: Comment model instance
        
    Returns:
        CommentResponse model
    """
    return CommentResponse(
        _id=comment.id,
        bugId=comment.bugId,
        authorId=comment.authorId,
        message=comment.message,
        createdAt=comment.createdAt
    )


@router.post("", response_model=BugResponse, status_code=201)
async def create_bug(
    services: Services,
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    projectId: Annotated[str, Form()],
    reportedBy: Annotated[str, Form()],
    priority: Annotated[str, Form()],
    severity: Annotated[str, Form()]
) -> BugResponse:
    """Create a new bug.
    
    Validates project existence through Collection DB.
    Sets initial bug status and validation flags.
    
    Args:
        services: Injected service container
        title: Bug title
        description: Bug description
        projectId: Associated project ID
        reportedBy: User ID who reported the bug
        priority: Bug priority level
        severity: Bug severity level
        
    Returns:
        Created bug data
        
    Raises:
        HTTPException: If validation fails or project doesn't exist
    """
    
    try:
        # Validate project exists in Collection DB
        project = await services.project_repository.get_by_id(projectId)
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project with ID {projectId} not found"
            )
        
        # Validate enum values
        try:
            priority_enum = BugPriority(priority)
            severity_enum = BugSeverity(severity)
        except ValueError as e:
            valid_priorities = [p.value for p in BugPriority]
            valid_severities = [s.value for s in BugSeverity]
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid priority or severity value. "
                    f"Received priority='{priority}', severity='{severity}'. "
                    f"Valid priorities: {valid_priorities}. "
                    f"Valid severities: {valid_severities}."
                )
            )
        
        # Create bug entity
        bug = Bug(
            title=title,
            description=description,
            projectId=projectId,
            reportedBy=reportedBy,
            priority=priority_enum,
            severity=severity_enum,
            status=BugStatus.OPEN,
            validated=False,
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc)
        )
        
        # Create bug using repository
        created_bug = await services.bug_repository.create(bug)
        
        logger.info(f"Bug created: {created_bug.id} for project {projectId}")
        
        # Return response
        return _bug_to_response(created_bug)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bug: {e}")
        raise HTTPException(status_code=500, detail="Failed to create bug")



@router.get("", response_model=List[BugResponse])
async def get_all_bugs(services: Services) -> List[BugResponse]:
    """Retrieve all bugs.
    
    Lists all bugs from Collection DB.
    
    Args:
        services: Injected service container
        
    Returns:
        List of bug data
        
    Raises:
        HTTPException: If retrieval fails
    """
    
    try:
        # Retrieve all bugs using repository
        bugs = await services.bug_repository.get_all()
        
        # Transform to response models
        bug_responses = [_bug_to_response(bug) for bug in bugs]
        
        logger.info(f"Retrieved {len(bug_responses)} bugs")
        return bug_responses
        
    except Exception as e:
        logger.error(f"Error retrieving bugs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve bugs")


@router.get("/{bug_id}", response_model=BugWithCommentsResponse)
async def get_bug_by_id(bug_id: str, services: Services) -> BugWithCommentsResponse:
    """Retrieve detailed bug view with comments.
    
    Gets specific bug details and associated comments from Collection DB.
    
    Args:
        bug_id: Bug identifier
        services: Injected service container
        
    Returns:
        Bug data with comments
        
    Raises:
        HTTPException: If bug not found or retrieval fails
    """
    try:
        # Retrieve bug using repository
        bug = await services.bug_repository.get_by_id(bug_id)
        if not bug:
            raise HTTPException(status_code=404, detail=f"Bug with ID {bug_id} not found")
        
        # Retrieve comments for this bug using repository
        comments = await services.comment_repository.get_by_bug_id(bug_id)
        
        # Transform to response models
        bug_response = _bug_to_response(bug)
        comment_responses = [_comment_to_response(comment) for comment in comments]
        
        logger.info(f"Retrieved bug {bug_id} with {len(comment_responses)} comments")
        
        return BugWithCommentsResponse(bug=bug_response, comments=comment_responses)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving bug {bug_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve bug")



@router.patch("/{bug_id}/status", response_model=StatusUpdateResponse)
async def update_bug_status(
    bug_id: str,
    status_update: BugStatusUpdateRequest,
    services: Services
) -> StatusUpdateResponse:
    """Update bug status with role-based validation.
    
    Validates role-based permissions for status changes.
    Implements tester validation and closure logic.
    Logs status changes to Collection DB activity logs.
    
    Args:
        bug_id: Bug identifier
        status_update: Status update request with user info
        services: Injected service container
        
    Returns:
        Status update response with updated bug data
        
    Raises:
        HTTPException: If validation fails or unauthorized
    """
    try:
        # Retrieve current bug using repository
        bug = await services.bug_repository.get_by_id(bug_id)
        if not bug:
            raise HTTPException(status_code=404, detail=f"Bug with ID {bug_id} not found")
        
        current_status = bug.status.value
        new_status = status_update.status.value
        user_role = status_update.userRole.lower()
        
        # Role-based validation for status changes
        
        # Only Admin can change status of closed bugs
        if current_status == BugStatus.CLOSED.value and user_role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Only Admin can modify closed bugs"
            )
        
        # Tester-specific validation for closing bugs
        if new_status == BugStatus.CLOSED.value:
            if user_role not in ["tester", "admin"]:
                raise HTTPException(
                    status_code=403,
                    detail="Only Testers can close bugs"
                )
            
            # Bug must be validated before closing
            if not bug.validated:
                raise HTTPException(
                    status_code=400,
                    detail="Bug must be validated before closing"
                )
        
        # Update bug status using repository
        updated_bug = await services.bug_repository.update_status(
            bug_id=bug_id,
            status=status_update.status,
            updated_at=datetime.now(timezone.utc)
        )
        
        # Log activity to Collection DB
        from backend.models.bug_model import ActivityLog
        activity_log = ActivityLog(
            bugId=bug_id,
            action="status_changed",
            performedBy=status_update.userId,
            timestamp=datetime.now(timezone.utc)
        )
        await services.activity_log_repository.create(activity_log)
        
        logger.info(f"Bug {bug_id} status updated: {current_status} -> {new_status} by {status_update.userId}")
        
        return StatusUpdateResponse(
            success=True,
            message=f"Bug status updated to {new_status}",
            bug=_bug_to_response(updated_bug)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating bug status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update bug status")


@router.patch("/{bug_id}/validate", response_model=StatusUpdateResponse)
async def validate_bug(
    bug_id: str,
    services: Services,
    userId: Annotated[str, Form()],
    userRole: Annotated[str, Form()]
) -> StatusUpdateResponse:
    """Mark bug as validated by tester.
    
    Only testers can validate bugs. This is required before closing.
    
    Args:
        bug_id: Bug identifier
        services: Injected service container
        userId: User ID performing validation
        userRole: User role for authorization
        
    Returns:
        Status update response
        
    Raises:
        HTTPException: If unauthorized or validation fails
    """
    try:
        # Check role authorization
        if userRole.lower() not in ["tester", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="Only Testers can validate bugs"
            )
        
        # Retrieve bug using repository
        bug = await services.bug_repository.get_by_id(bug_id)
        if not bug:
            raise HTTPException(status_code=404, detail=f"Bug with ID {bug_id} not found")
        
        # Update validated flag using repository
        updated_bug = await services.bug_repository.update_validation(
            bug_id=bug_id,
            validated=True,
            updated_at=datetime.now(timezone.utc)
        )
        
        # Log activity to Collection DB
        from backend.models.bug_model import ActivityLog
        activity_log = ActivityLog(
            bugId=bug_id,
            action="bug_validated",
            performedBy=userId,
            timestamp=datetime.now(timezone.utc)
        )
        await services.activity_log_repository.create(activity_log)
        
        logger.info(f"Bug {bug_id} validated by {userId}")
        
        return StatusUpdateResponse(
            success=True,
            message="Bug validated successfully",
            bug=_bug_to_response(updated_bug)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating bug: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate bug")



@router.patch("/{bug_id}/assign", response_model=AssignmentResponse)
async def assign_bug(
    bug_id: str,
    assignment: BugAssignRequest,
    services: Services
) -> AssignmentResponse:
    """Assign bug to a user.
    
    Allows developers to assign bugs to users.
    Validates assignee exists in Collection DB user system.
    Updates bug timestamp on assignment changes.
    
    Args:
        bug_id: Bug identifier
        assignment: Assignment request with assignee info
        services: Injected service container
        
    Returns:
        Assignment response with updated bug data
        
    Raises:
        HTTPException: If validation fails or user not found
    """
    try:
        # Retrieve bug using repository
        bug = await services.bug_repository.get_by_id(bug_id)
        if not bug:
            raise HTTPException(status_code=404, detail=f"Bug with ID {bug_id} not found")
        
        # Validate assignee exists in Collection DB
        assignee = await services.user_repository.get_by_id(assignment.assignedTo)
        if not assignee:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {assignment.assignedTo} not found"
            )
        
        assignee_name = assignee.name
        
        # Update bug assignment using repository
        updated_bug = await services.bug_repository.update_assignment(
            bug_id=bug_id,
            assigned_to=assignment.assignedTo,
            updated_at=datetime.now(timezone.utc)
        )
        
        # Log activity to Collection DB
        from backend.models.bug_model import ActivityLog
        activity_log = ActivityLog(
            bugId=bug_id,
            action="bug_assigned",
            performedBy=assignment.assignedBy,
            timestamp=datetime.now(timezone.utc)
        )
        await services.activity_log_repository.create(activity_log)
        
        logger.info(f"Bug {bug_id} assigned to {assignment.assignedTo} by {assignment.assignedBy}")
        
        return AssignmentResponse(
            success=True,
            message=f"Bug assigned to {assignee_name}",
            bug=_bug_to_response(updated_bug)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning bug: {e}")
        raise HTTPException(status_code=500, detail="Failed to assign bug")

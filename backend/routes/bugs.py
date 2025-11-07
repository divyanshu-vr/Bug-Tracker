"""Bug management API endpoints."""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Annotated, List
from datetime import datetime, timezone
import logging
import os

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
from .dependencies import Services, validate_object_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bugs", tags=["bugs"])

# Development mode flag - set to True to skip external API validations
DEV_MODE = os.getenv("DEV_MODE", "true").lower() == "true"


@router.post("", response_model=BugResponse, status_code=201)
async def create_bug(
    services: Services,
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    projectId: Annotated[str, Form()],
    reportedBy: Annotated[str, Form()],
    priority: Annotated[str, Form()],
    severity: Annotated[str, Form()],
    files: Annotated[List[UploadFile] | None, File()] = None
) -> BugResponse:
    """Create a new bug with optional file attachments.
    
    Handles multipart form data for bug details and file attachments.
    Validates project existence through AppFlyte API.
    Uploads attachments to Cloudinary and stores URLs in MongoDB.
    Sets initial bug status and validation flags.
    
    Args:
        services: Injected service container
        title: Bug title
        description: Bug description
        projectId: Associated project ID
        reportedBy: User ID who reported the bug
        priority: Bug priority level
        severity: Bug severity level
        files: Optional list of image file attachments (List[UploadFile] | None). Each file should be an image in JPEG, PNG, or GIF format, up to 10MB per file. Non-image files will be rejected.
        
    Returns:
        Created bug data
        
    Raises:
        HTTPException: If validation fails or project doesn't exist
    """
    
    try:
        # Validate project exists in AppFlyte (skip in dev mode)
        if not DEV_MODE:
            project_exists = await services.project_api.validate_project_exists(projectId)
            if not project_exists:
                raise HTTPException(
                    status_code=404,
                    detail=f"Project with ID {projectId} not found"
                )
        else:
            logger.info(f"DEV_MODE: Skipping AppFlyte project validation for {projectId}")
        
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
        
        # Upload attachments to Cloudinary with validation
        attachment_urls = []
        if files:
            for file in files:
                try:
                    # Validate file before upload
                    if not file.filename:
                        raise HTTPException(status_code=400, detail="File must have a filename")
                    
                    # Validate file using Cloudinary service validation
                    is_valid, error_message = services.image_storage.validate_file(
                        filename=file.filename,
                        file_size=None  # No local file size calculation; let upload_image handle it
                    )
                    
                    if not is_valid:
                        raise HTTPException(status_code=400, detail=error_message)
                    
                    # Upload to Cloudinary
                    upload_result = await services.image_storage.upload_image(
                        file=file.file,
                        filename=file.filename,
                        folder="bugtrackr/attachments"
                    )
                    attachment_urls.append(upload_result["url"])
                    
                except HTTPException:
                    raise
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=str(e))
                except Exception as e:
                    logger.error(f"Failed to upload file {file.filename}: {e}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to upload file: {file.filename}. Error: {str(e)}"
                    )
        
        # Create bug entity
        bug = Bug(
            title=title,
            description=description,
            projectId=projectId,
            reportedBy=reportedBy,
            priority=priority_enum,
            severity=severity_enum,
            attachments=attachment_urls,
            status=BugStatus.OPEN,
            validated=False,
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc)
        )
        
        # Insert into MongoDB
        bug_dict = bug.model_dump(by_alias=True, exclude={"id"})
        result = services.database.bugs.insert_one(bug_dict)
        bug_dict["_id"] = str(result.inserted_id)
        
        logger.info(f"Bug created: {bug_dict['_id']} for project {projectId}")
        
        # Return response
        return BugResponse(**bug_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bug: {e}")
        raise HTTPException(status_code=500, detail="Failed to create bug")



@router.get("", response_model=List[BugResponse])
async def get_all_bugs(services: Services) -> List[BugResponse]:
    """Retrieve all bugs with project information.
    
    Lists all bugs and merges with project data from AppFlyte API.
    
    Args:
        services: Injected service container
        
    Returns:
        List of bug data with project information
        
    Raises:
        HTTPException: If retrieval fails
    """
    
    try:
        # Retrieve all bugs from MongoDB
        bugs_cursor = services.database.bugs.find()
        bugs = []
        
        for bug_doc in bugs_cursor:
            bug_doc["_id"] = str(bug_doc["_id"])
            bugs.append(BugResponse(**bug_doc))
        
        logger.info(f"Retrieved {len(bugs)} bugs")
        return bugs
        
    except Exception as e:
        logger.error(f"Error retrieving bugs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve bugs")


@router.get("/{bug_id}", response_model=BugWithCommentsResponse)
async def get_bug_by_id(bug_id: str, services: Services) -> BugWithCommentsResponse:
    """Retrieve detailed bug view with comments.
    
    Gets specific bug details and associated comments.
    Merges bug data with project information from AppFlyte API.
    
    Args:
        bug_id: Bug identifier
        services: Injected service container
        
    Returns:
        Bug data with comments
        
    Raises:
        HTTPException: If bug not found or retrieval fails
    """
    try:
        # Validate ObjectId format
        obj_id = validate_object_id(bug_id)
        
        # Retrieve bug from MongoDB
        bug_doc = services.database.bugs.find_one({"_id": obj_id})
        if not bug_doc:
            raise HTTPException(status_code=404, detail=f"Bug with ID {bug_id} not found")
        
        bug_doc["_id"] = str(bug_doc["_id"])
        bug = BugResponse(**bug_doc)
        
        # Retrieve comments for this bug
        comments_cursor = services.database.comments.find({"bugId": bug_id})
        comments = []
        
        for comment_doc in comments_cursor:
            comment_doc["_id"] = str(comment_doc["_id"])
            comments.append(CommentResponse(**comment_doc))
        
        # Sort comments by creation time
        comments.sort(key=lambda c: c.createdAt)
        
        logger.info(f"Retrieved bug {bug_id} with {len(comments)} comments")
        
        return BugWithCommentsResponse(bug=bug, comments=comments)
        
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
    Logs status changes to AppFlyte activity logs.
    
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
        # Validate ObjectId format
        obj_id = validate_object_id(bug_id)
        
        # Retrieve current bug
        bug_doc = services.database.bugs.find_one({"_id": obj_id})
        if not bug_doc:
            raise HTTPException(status_code=404, detail=f"Bug with ID {bug_id} not found")
        
        current_status = bug_doc.get("status")
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
            if not bug_doc.get("validated", False):
                raise HTTPException(
                    status_code=400,
                    detail="Bug must be validated before closing"
                )
        
        # Update bug status and timestamp
        update_data = {
            "status": new_status,
            "updatedAt": datetime.now(timezone.utc)
        }
        
        services.database.bugs.update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )
        
        # Log activity to AppFlyte
        await services.project_api.log_activity(
            user_id=status_update.userId,
            action="status_changed",
            resource_type="bug",
            resource_id=bug_id,
            details={
                "old_status": current_status,
                "new_status": new_status,
                "user_role": user_role
            }
        )
        
        # Retrieve updated bug
        updated_bug_doc = services.database.bugs.find_one({"_id": obj_id})
        updated_bug_doc["_id"] = str(updated_bug_doc["_id"])
        
        logger.info(f"Bug {bug_id} status updated: {current_status} -> {new_status} by {status_update.userId}")
        
        return StatusUpdateResponse(
            success=True,
            message=f"Bug status updated to {new_status}",
            bug=BugResponse(**updated_bug_doc)
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
        # Validate ObjectId format
        obj_id = validate_object_id(bug_id)
        
        # Check role authorization
        if userRole.lower() not in ["tester", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="Only Testers can validate bugs"
            )
        
        # Retrieve bug
        bug_doc = services.database.bugs.find_one({"_id": obj_id})
        if not bug_doc:
            raise HTTPException(status_code=404, detail=f"Bug with ID {bug_id} not found")
        
        # Update validated flag
        services.database.bugs.update_one(
            {"_id": obj_id},
            {"$set": {
                "validated": True,
                "updatedAt": datetime.now(timezone.utc)
            }}
        )
        
        # Log activity to AppFlyte
        await services.project_api.log_activity(
            user_id=userId,
            action="bug_validated",
            resource_type="bug",
            resource_id=bug_id,
            details={"validated_by": userId}
        )
        
        # Retrieve updated bug
        updated_bug_doc = services.database.bugs.find_one({"_id": obj_id})
        updated_bug_doc["_id"] = str(updated_bug_doc["_id"])
        
        logger.info(f"Bug {bug_id} validated by {userId}")
        
        return StatusUpdateResponse(
            success=True,
            message="Bug validated successfully",
            bug=BugResponse(**updated_bug_doc)
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
    Validates assignee exists in AppFlyte user system.
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
        # Validate ObjectId format
        obj_id = validate_object_id(bug_id)
        
        # Retrieve bug
        bug_doc = services.database.bugs.find_one({"_id": obj_id})
        if not bug_doc:
            raise HTTPException(status_code=404, detail=f"Bug with ID {bug_id} not found")
        
        # Validate assignee exists in AppFlyte
        assignee = await services.project_api.get_user(assignment.assignedTo)
        if not assignee:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {assignment.assignedTo} not found"
            )
        
        # Update bug assignment
        services.database.bugs.update_one(
            {"_id": obj_id},
            {"$set": {
                "assignedTo": assignment.assignedTo,
                "updatedAt": datetime.now(timezone.utc)
            }}
        )
        
        # Log activity to AppFlyte
        await services.project_api.log_activity(
            user_id=assignment.assignedBy,
            action="bug_assigned",
            resource_type="bug",
            resource_id=bug_id,
            details={
                "assigned_to": assignment.assignedTo,
                "assigned_by": assignment.assignedBy
            }
        )
        
        # Retrieve updated bug
        updated_bug_doc = services.database.bugs.find_one({"_id": obj_id})
        updated_bug_doc["_id"] = str(updated_bug_doc["_id"])
        
        logger.info(f"Bug {bug_id} assigned to {assignment.assignedTo} by {assignment.assignedBy}")
        
        return AssignmentResponse(
            success=True,
            message=f"Bug assigned to {assignee.get('name', assignment.assignedTo)}",
            bug=BugResponse(**updated_bug_doc)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning bug: {e}")
        raise HTTPException(status_code=500, detail="Failed to assign bug")

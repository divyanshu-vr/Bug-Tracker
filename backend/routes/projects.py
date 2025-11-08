"""Project management API endpoints."""

from fastapi import APIRouter, HTTPException
from typing import List
import logging

from ..models.bug_model import Project, ProjectResponse
from .dependencies import Services

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _project_to_response(project: Project) -> ProjectResponse:
    """Transform Project model to ProjectResponse.
    
    Centralizes the transformation logic to follow DRY principle.
    
    Args:
        project: Project model instance
        
    Returns:
        ProjectResponse model
    """
    return ProjectResponse(
        _id=project.id,
        name=project.name,
        description=project.description,
        createdBy=project.createdBy,
        createdAt=project.createdAt
    )


@router.get("", response_model=List[ProjectResponse])
async def get_projects(services: Services) -> List[ProjectResponse]:
    """Retrieve all projects from Collection DB.
    
    Lists all predefined projects from Collection DB.
    
    Args:
        services: Injected service container
        
    Returns:
        List of project data
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # Retrieve all projects using repository
        projects = await services.project_repository.get_all()
        
        # Transform to response models
        project_responses = [_project_to_response(project) for project in projects]
        
        logger.info(f"Retrieved {len(project_responses)} projects")
        
        return project_responses
        
    except Exception as e:
        logger.error(f"Error retrieving projects: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve projects"
        )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project_details(
    project_id: str,
    services: Services
) -> ProjectResponse:
    """Retrieve project details from Collection DB.
    
    Gets specific project details from Collection DB.
    Note: Project members are not included in the collection schema.
    
    Args:
        project_id: Project identifier
        services: Injected service container
        
    Returns:
        Project data
        
    Raises:
        HTTPException: If project not found or retrieval fails
    """
    try:
        # Retrieve project using repository
        project = await services.project_repository.get_by_id(project_id)
        
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project with ID {project_id} not found"
            )
        
        logger.info(f"Retrieved project {project_id}")
        
        return _project_to_response(project)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving project {project_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve project"
        )

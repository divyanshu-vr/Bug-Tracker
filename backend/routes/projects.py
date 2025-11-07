"""Project proxy API endpoints."""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import httpx

from .dependencies import Services

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=List[Dict[str, Any]])
async def get_projects(services: Services) -> List[Dict[str, Any]]:
    """Retrieve all projects from AppFlyte API.
    
    Proxies request to AppFlyte to retrieve project list.
    Handles AppFlyte API errors gracefully.
    
    Args:
        services: Injected service container
        
    Returns:
        List of project data dictionaries
        
    Raises:
        HTTPException: If AppFlyte API request fails
    """
    try:
        projects = await services.project_api.get_projects()
        
        logger.info(f"Retrieved {len(projects)} projects from AppFlyte")
        
        return projects
        
    except httpx.HTTPError as e:
        logger.error(f"AppFlyte API error retrieving projects: {e}")
        raise HTTPException(
            status_code=502,
            detail="Failed to retrieve projects from external API"
        )
    except Exception as e:
        logger.error(f"Error retrieving projects: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve projects"
        )


@router.get("/{project_id}", response_model=Dict[str, Any])
async def get_project_details(
    project_id: str,
    services: Services
) -> Dict[str, Any]:
    """Retrieve project details with members from AppFlyte API.
    
    Proxies request to AppFlyte to get project details and member information.
    Handles AppFlyte API errors gracefully.
    
    Args:
        project_id: Project identifier
        services: Injected service container
        
    Returns:
        Project data dictionary with members
        
    Raises:
        HTTPException: If project not found or API request fails
    """
    try:
        # Get project details
        project = await services.project_api.get_project(project_id)
        
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project with ID {project_id} not found"
            )
        
        # Get project members
        try:
            members = await services.project_api.get_project_members(project_id)
            project["members"] = members
        except httpx.HTTPError as e:
            logger.warning(
                f"Failed to retrieve members for project {project_id}: {e}. "
                "Returning project without member details."
            )
            project["members"] = []
        
        logger.info(
            f"Retrieved project {project_id} with {len(project.get('members', []))} members"
        )
        
        return project
        
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        logger.error(f"AppFlyte API error retrieving project {project_id}: {e}")
        raise HTTPException(
            status_code=502,
            detail="Failed to retrieve project from external API"
        )
    except Exception as e:
        logger.error(f"Error retrieving project {project_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve project"
        )

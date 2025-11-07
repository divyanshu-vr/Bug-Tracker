"""AppFlyte API client for user, project, and activity log management."""

from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import httpx
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ProjectAPIClient(ABC):
    """Abstract interface for project and user API operations."""

    @abstractmethod
    async def close(self) -> None:
        """Close client and cleanup resources."""
        pass

    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by ID."""
        pass

    @abstractmethod
    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve project by ID."""
        pass

    @abstractmethod
    async def get_projects(self) -> List[Dict[str, Any]]:
        """Retrieve all projects."""
        pass

    @abstractmethod
    async def validate_project_exists(self, project_id: str) -> bool:
        """Validate project exists."""
        pass

    @abstractmethod
    async def log_activity(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log activity for audit trail."""
        pass


class AppFlyteClient(ProjectAPIClient):
    """HTTP client for AppFlyte Collection DB API integration."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0):
        """Initialize AppFlyte API client.
        
        Args:
            base_url: Base URL for AppFlyte API
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self._base_url = base_url.rstrip('/')
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers=self._headers
        )

    async def close(self) -> None:
        """Close the HTTP client and cleanup resources."""
        await self._client.aclose()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to AppFlyte API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            httpx.HTTPError: If request fails
        """
        url = f"{self._base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = await self._client.request(
                method=method,
                url=url,
                json=data,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"AppFlyte API request failed: {method} {url} - {e}")
            raise

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user information by ID.
        
        Args:
            user_id: User identifier
            
        Returns:
            User data dictionary or None if not found
        """
        try:
            return await self._make_request("GET", f"/users/{user_id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"User not found: {user_id}")
                return None
            raise

    async def get_users(self, user_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Retrieve multiple users.
        
        Args:
            user_ids: Optional list of user IDs to filter
            
        Returns:
            List of user data dictionaries
        """
        params = {"ids": ",".join(user_ids)} if user_ids else None
        try:
            response = await self._make_request("GET", "/users", params=params)
            return response.get("users", [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to retrieve users: {e}")
            return []

    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve project information by ID.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Project data dictionary or None if not found
        """
        try:
            return await self._make_request("GET", f"/projects/{project_id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Project not found: {project_id}")
                return None
            raise

    async def get_projects(self) -> List[Dict[str, Any]]:
        """Retrieve all projects.
        
        Returns:
            List of project data dictionaries
        """
        try:
            response = await self._make_request("GET", "/projects")
            return response.get("projects", [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to retrieve projects: {e}")
            return []

    async def get_project_members(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieve project members.
        
        Args:
            project_id: Project identifier
            
        Returns:
            List of user data dictionaries for project members
        """
        try:
            response = await self._make_request("GET", f"/projects/{project_id}/members")
            return response.get("members", [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to retrieve project members: {e}")
            return []

    async def validate_project_exists(self, project_id: str) -> bool:
        """Validate that a project exists.
        
        Args:
            project_id: Project identifier
            
        Returns:
            True if project exists, False otherwise
        """
        project = await self.get_project(project_id)
        return project is not None

    async def log_activity(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log activity to AppFlyte audit trail.
        
        Args:
            user_id: User who performed the action
            action: Action performed (e.g., "status_changed", "bug_closed")
            resource_type: Type of resource (e.g., "bug", "comment")
            resource_id: ID of the resource
            details: Additional details about the activity
            
        Returns:
            True if logging succeeded, False otherwise
        """
        activity_data = {
            "userId": user_id,
            "action": action,
            "resourceType": resource_type,
            "resourceId": resource_id,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }
        
        try:
            await self._make_request("POST", "/activities", data=activity_data)
            logger.info(f"Activity logged: {action} on {resource_type} {resource_id}")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to log activity: {e}")
            return False


def create_appflyte_client(base_url: str, api_key: str, timeout: float = 30.0) -> AppFlyteClient:
    """Factory function to create AppFlyte client instance.
    
    Args:
        base_url: Base URL for AppFlyte API
        api_key: API key for authentication
        timeout: Request timeout in seconds
        
    Returns:
        AppFlyteClient instance
    """
    return AppFlyteClient(base_url, api_key, timeout)

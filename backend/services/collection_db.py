"""AppFlyte Collection Database service for data persistence."""

from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import httpx
import logging

logger: logging.Logger = logging.getLogger(__name__)


class CollectionDBService(ABC):
    """Abstract interface for Collection DB operations."""

    @abstractmethod
    async def close(self) -> None:
        """Close client and cleanup resources."""
        pass

    @abstractmethod
    async def create_item(
        self,
        collection_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new item in collection."""
        pass

    @abstractmethod
    async def get_all_items(
        self,
        collection_name: str
    ) -> List[Dict[str, Any]]:
        """Get all items from collection."""
        pass

    @abstractmethod
    async def get_item_by_id(
        self,
        collection_name: str,
        item_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get single item by ID."""
        pass

    @abstractmethod
    async def update_item(
        self,
        collection_name: str,
        item_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update item fields."""
        pass

    @abstractmethod
    async def delete_item(
        self,
        collection_name: str,
        item_id: str
    ) -> bool:
        """Delete item by ID."""
        pass


class AppFlyteCollectionDB(CollectionDBService):
    """HTTP client for AppFlyte Collection Database API.
    
    Implements CRUD operations for AppFlyte Collection DB using the
    Collection Operations API format with Bearer token authentication.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0
    ):
        """Initialize Collection DB service.
        
        Args:
            base_url: Full base URL from Collection Operations.txt
                     (e.g., "https://appflyte-backend.ameya.ai/.../ameya_appflyte")
            api_key: Bearer token for authentication (from Collection Operations.txt)
            timeout: Request timeout in seconds (default: 30.0 for safe operation)
            
        Raises:
            ValueError: If base_url or api_key is empty
        """
        # Validate inputs immediately (fail-fast)
        if not base_url or not base_url.strip():
            raise ValueError("base_url cannot be empty")
        if not api_key or not api_key.strip():
            raise ValueError("api_key cannot be empty")
        
        self._base_url = base_url.rstrip('/')
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers=self._headers
        )
        # Log without exposing sensitive URL details
        logger.info("Initialized CollectionDB service")

    async def close(self) -> None:
        """Close the HTTP client and cleanup resources."""
        await self._client.aclose()
        logger.info("CollectionDB service closed")

    async def _make_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request with error handling.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Full URL for the request
            data: Request body data
            
        Returns:
            Response data as dictionary or None for 404
            
        Raises:
            httpx.HTTPError: For non-404 HTTP errors
        """
        try:
            # Log without exposing full URL (may contain sensitive paths)
            logger.debug(f"{method} request to Collection DB")
            response = await self._client.request(
                method=method,
                url=url,
                json=data
            )
            response.raise_for_status()
            
            # Handle empty responses (e.g., DELETE)
            if response.status_code == 204 or not response.content:
                return {}
                
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Resource not found (404)")
                return None
            logger.error(f"HTTP error {e.response.status_code}: {method} request failed")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error: {method} request failed - {type(e).__name__}")
            raise

    async def create_item(
        self,
        collection_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new item in collection.
        
        POST {base_url}/{collection_name}
        Body: {"collection_item": {data}}
        
        Args:
            collection_name: Name of the collection (e.g., "bugs", "comments")
                           Empty string uses base collection
            data: Item data to create
            
        Returns:
            Created item with __auto_id__
            
        Raises:
            ValueError: If data is None
            httpx.HTTPError: If request fails
        """
        # Validate inputs (fail-fast)
        if data is None:
            raise ValueError("data cannot be None")
        
        # Build URL - empty collection_name uses base URL
        url = f"{self._base_url}/{collection_name}" if collection_name else self._base_url
        request_body = {"collection_item": data}
        
        logger.info(f"Creating item in collection '{collection_name or 'base'}'")
        result = await self._make_request("POST", url, request_body)
        
        if result is None:
            raise ValueError(f"Failed to create item: collection '{collection_name or 'base'}' not found")

        item_id = result.get("__auto_id__", "unknown")
        logger.info(f"Created item in collection '{collection_name or 'base'}' with id '{item_id}'")
        return result
    async def get_all_items(
        self,
        collection_name: str
    ) -> List[Dict[str, Any]]:
        """Get all items from collection.
        
        GET {base_url}/{collection_name}
        
        Args:
            collection_name: Name of the collection
                           Empty string uses base collection
            
        Returns:
            List of items (empty list if collection not found)
            
        Raises:
            httpx.HTTPError: If request fails
        """
        # Build URL - empty collection_name uses base URL
        url = f"{self._base_url}/{collection_name}" if collection_name else self._base_url
        
        logger.info(f"Retrieving all items from collection '{collection_name or 'base'}'")
        result = await self._make_request("GET", url)
        
        # Handle different response formats
        if result is None:
            logger.warning(f"Collection '{collection_name}' not found or empty")
            return []
        
        # If result is a list, return it directly
        if isinstance(result, list):
            logger.info(f"Retrieved {len(result)} items from collection '{collection_name}'")
            return result
        
        # If result is a dict with items key, return the items
        if isinstance(result, dict) and "items" in result:
            items = result["items"]
            logger.info(f"Retrieved {len(items)} items from collection '{collection_name or 'base'}'")
            return items
        
        # If result is a dict, it might be the items directly or contain collection data
        if isinstance(result, dict):
            logger.debug(f"Response is dict with keys: {list(result.keys())}")
            
            # AppFlyte Collection DB returns items nested by collection_definition_id
            # Extract all items from nested structure
            all_items = []
            for key, value in result.items():
                if isinstance(value, list):
                    # Found a list of items
                    for item in value:
                        if isinstance(item, dict) and "payload" in item:
                            # Extract payload which contains the actual data
                            all_items.append(item["payload"])
                        elif isinstance(item, dict):
                            all_items.append(item)
            
            if all_items:
                logger.info(f"Retrieved {len(all_items)} items from collection '{collection_name or 'base'}'")
                return all_items
            
            # Return as single-item list if it's an object
            logger.info(f"Retrieved 1 item from collection '{collection_name or 'base'}'")
            return [result]
        
        # Otherwise return empty list (safe default)
        logger.warning(f"Unexpected response format from collection '{collection_name or 'base'}': {type(result)}")
        return []

    async def get_item_by_id(
        self,
        collection_name: str,
        item_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get single item by ID.
        
        GET {base_url}/{collection_name}/{item_id}
        
        Args:
            collection_name: Name of the collection
                           Empty string uses base collection
            item_id: Item ID (__auto_id__)
            
        Returns:
            Item data or None if not found
            
        Raises:
            ValueError: If item_id is empty
        """
        # Validate inputs (fail-fast)
        if not item_id or not item_id.strip():
            raise ValueError("item_id cannot be empty")
        
        # Build URL - empty collection_name uses base URL
        url = f"{self._base_url}/{collection_name}/{item_id}" if collection_name else f"{self._base_url}/{item_id}"
        
        logger.info(f"Retrieving item from collection '{collection_name or 'base'}'")
        result = await self._make_request("GET", url)
        
        if result:
            logger.info(f"Retrieved item from collection '{collection_name or 'base'}'")
        else:
            logger.warning(f"Item not found in collection '{collection_name or 'base'}'")
        
        return result
        
    async def update_item(
        self,
        collection_name: str,
        item_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update item fields.
        
        PUT {base_url}/{collection_name}/{item_id}
        Body: {
            "id": item_id,
            "fields": [
                {"path": "$.field_name", "value": new_value}
            ]
        }
        
        Args:
            collection_name: Name of the collection
                           Empty string uses base collection
            item_id: Item ID (__auto_id__)
            updates: Dictionary of field names to new values
            
        Returns:
            Updated item
            
        Raises:
            ValueError: If item_id is empty or updates is None/empty
            httpx.HTTPError: If request fails
        """
        # Validate inputs (fail-fast)
        if not item_id or not item_id.strip():
            raise ValueError("item_id cannot be empty")
        if updates is None or not updates:
            raise ValueError("updates cannot be None or empty")
        
        # Build URL - empty collection_name uses base URL
        url = f"{self._base_url}/{collection_name}/{item_id}" if collection_name else f"{self._base_url}/{item_id}"
        
        # Convert updates dict to fields array with JSON path syntax
        fields: List[Dict[str, Any]] = []
        for key, value in updates.items():
            fields.append({
                "path": f"$.{key}",
                "value": value
            })
        
        request_body = {
            "id": item_id,
            "fields": fields
        }
        
        logger.info(f"Updating item in collection '{collection_name or 'base'}' with {len(fields)} field(s)")
        result = await self._make_request("PUT", url, request_body)
        
        if result is None:
            raise ValueError(f"Failed to update item: item '{item_id}' not found in collection '{collection_name or 'base'}'")
        
        logger.info(f"Updated item in collection '{collection_name or 'base'}'")
        
        return result

    async def delete_item(
        self,
        collection_name: str,
        item_id: str
    ) -> bool:
        """Delete item by ID.
        
        DELETE {base_url}/{collection_name}/{item_id}
        
        Args:
            collection_name: Name of the collection
                           Empty string uses base collection
            item_id: Item ID (__auto_id__)
            
        Returns:
            True if successful, False if item not found
            
        Raises:
            ValueError: If item_id is empty
            httpx.HTTPError: If request fails
        """
        # Validate inputs (fail-fast)
        if not item_id or not item_id.strip():
            raise ValueError("item_id cannot be empty")
        
        # Build URL - empty collection_name uses base URL
        url = f"{self._base_url}/{collection_name}/{item_id}" if collection_name else f"{self._base_url}/{item_id}"
        
        logger.info(f"Deleting item from collection '{collection_name or 'base'}'")
        result = await self._make_request("DELETE", url)
        
        # DELETE returns None for 404, {} for success, or error
        success = result is not None
        
        if success:
            logger.info(f"Deleted item from collection '{collection_name or 'base'}'")
        else:
            logger.warning(f"Failed to delete item from collection '{collection_name or 'base'}'")
        
        return success


def create_collection_db_service(
    base_url: str,
    api_key: str,
    timeout: float = 30.0
) -> AppFlyteCollectionDB:
    """Factory function to create Collection DB service instance.
    
    Args:
        base_url: Full base URL for the collection database service API
        api_key: Bearer token for authentication
        timeout: Request timeout in seconds
        
    Returns:
        AppFlyteCollectionDB instance
    """
    return AppFlyteCollectionDB(base_url, api_key, timeout)

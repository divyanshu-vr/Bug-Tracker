"""Configuration management using environment variables."""

from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables from .env file using pathlib for portability
env_path: Path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


@dataclass(frozen=True)
class Config:
    """Application configuration from environment variables.
    
    Immutable configuration loaded from environment variables.
    """

    # AppFlyte Collection DB Configuration (for data storage)
    appflyte_collection_base_url: str
    appflyte_collection_api_key: str

    # Server Configuration
    port: int
    debug: bool

    @staticmethod
    def from_env() -> 'Config':
        """Create configuration from environment variables.
        
        Returns:
            Config instance
            
        Raises:
            RuntimeError: If required environment variables are missing
        """
        # Required variables
        appflyte_collection_base_url = os.getenv("APPFLYTE_COLLECTION_BASE_URL", "")
        appflyte_collection_api_key = os.getenv("APPFLYTE_COLLECTION_API_KEY", "")

        # Validate required variables
        required = {
            "APPFLYTE_COLLECTION_BASE_URL": appflyte_collection_base_url,
            "APPFLYTE_COLLECTION_API_KEY": appflyte_collection_api_key,
        }

        missing = [key for key, value in required.items() if not value]
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        # Optional variables with defaults
        port = int(os.getenv("PORT", "8000"))
        debug = os.getenv("DEBUG", "false").lower() == "true"

        return Config(
            appflyte_collection_base_url=appflyte_collection_base_url,
            appflyte_collection_api_key=appflyte_collection_api_key,
            port=port,
            debug=debug
        )

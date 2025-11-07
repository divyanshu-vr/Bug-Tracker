"""Configuration management using environment variables."""

from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


@dataclass(frozen=True)
class Config:
    """Application configuration from environment variables.
    
    Immutable configuration loaded from environment variables.
    """

    # MongoDB Configuration
    mongodb_uri: str
    mongodb_database: str

    # AppFlyte Configuration
    appflyte_base_url: str
    appflyte_api_key: str

    # Cloudinary Configuration
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str

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
        mongodb_uri = os.getenv("MONGODB_URI", "")
        appflyte_base_url = os.getenv("APPFLYTE_BASE_URL", "")
        appflyte_api_key = os.getenv("APPFLYTE_API_KEY", "")
        cloudinary_cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "")
        cloudinary_api_key = os.getenv("CLOUDINARY_API_KEY", "")
        cloudinary_api_secret = os.getenv("CLOUDINARY_API_SECRET", "")

        # Validate required variables
        required = {
            "MONGODB_URI": mongodb_uri,
            "APPFLYTE_BASE_URL": appflyte_base_url,
            "APPFLYTE_API_KEY": appflyte_api_key,
            "CLOUDINARY_CLOUD_NAME": cloudinary_cloud_name,
            "CLOUDINARY_API_KEY": cloudinary_api_key,
            "CLOUDINARY_API_SECRET": cloudinary_api_secret,
        }

        missing = [key for key, value in required.items() if not value]
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        # Optional variables with defaults
        mongodb_database = os.getenv("MONGODB_DATABASE", "bugtrackr")
        port = int(os.getenv("PORT", "8000"))
        debug = os.getenv("DEBUG", "false").lower() == "true"

        return Config(
            mongodb_uri=mongodb_uri,
            mongodb_database=mongodb_database,
            appflyte_base_url=appflyte_base_url,
            appflyte_api_key=appflyte_api_key,
            cloudinary_cloud_name=cloudinary_cloud_name,
            cloudinary_api_key=cloudinary_api_key,
            cloudinary_api_secret=cloudinary_api_secret,
            port=port,
            debug=debug
        )

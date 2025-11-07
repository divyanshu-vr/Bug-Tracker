"""Application entry point for running with uvicorn."""

from .config import Config
from .main import create_app

# Load configuration from environment
config = Config.from_env()

# Create application instance
app = create_app(config)

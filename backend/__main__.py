"""Application entry point for running with uvicorn."""

import uvicorn
from .config import Config
from .main import create_app

if __name__ == "__main__":
    # Load configuration from environment
    config = Config.from_env()

    # Run with uvicorn using the app factory
    uvicorn.run(
        "backend.main:create_app",
        factory=True,
        host="0.0.0.0",
        port=config.port,
        log_level="debug" if config.debug else "info",
        kwargs={"config": config}
    )

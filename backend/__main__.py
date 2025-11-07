"""Application entry point for running with uvicorn."""

import uvicorn
from .config import Config
from .main import create_app

if __name__ == "__main__":
    # Load configuration from environment
    config = Config.from_env()

    # Create application instance
    app = create_app(config)
    
    # Run with uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.port,
        log_level="debug" if config.debug else "info"
    )

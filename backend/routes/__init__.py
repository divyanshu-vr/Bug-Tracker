"""API routes package.

This package contains all API route modules for the BugTrackr application.
Each module defines a FastAPI router with related endpoints.
"""

from . import bugs, comments, projects

__all__ = ["bugs", "comments", "projects"]

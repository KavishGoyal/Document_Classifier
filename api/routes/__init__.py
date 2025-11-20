"""
API Routes Package
"""

from fastapi import APIRouter
from . import documents, batch, statistics

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(documents.router)
api_router.include_router(batch.router)
api_router.include_router(statistics.router)

__all__ = ["api_router", "documents", "batch", "statistics"]
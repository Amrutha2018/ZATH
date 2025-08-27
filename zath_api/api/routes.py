"""
API Routes Aggregator
All API routes are included here, keeping main.py clean
"""
from fastapi import APIRouter
from .jobs import router as jobs_router

# Create main API router with /api prefix
api_router = APIRouter(prefix="/api")

# Include all API routes (jobs router has /jobs prefix)
api_router.include_router(jobs_router)

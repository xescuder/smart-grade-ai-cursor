"""
System router for root, health, and debug endpoints
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/")
def root():
    return {"message": "Smart Grade AI API with PostgreSQL", "status": "active"}

@router.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "database": "postgresql"}

@router.get("/debug-early")
def debug_early():
    return {"message": "Early debug endpoint works"}


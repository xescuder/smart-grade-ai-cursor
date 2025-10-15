"""
Classroom management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import get_db
from crud import (
    get_classrooms,
    get_classroom,
    create_classroom,
    update_classroom,
    delete_classroom,
    ClassroomCreate,
    ClassroomUpdate,
    ClassroomResponse
)

router = APIRouter()

# Error messages
CLASSROOM_NOT_FOUND = "Classroom not found"


@router.get("/", response_model=List[ClassroomResponse])
async def list_classrooms(db: AsyncSession = Depends(get_db)):
    """Get all classrooms"""
    classrooms = await get_classrooms(db)
    return classrooms


@router.get("/{classroom_id}", response_model=ClassroomResponse)
async def get_classroom_by_id(
    classroom_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific classroom by ID"""
    classroom = await get_classroom(db, classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail=CLASSROOM_NOT_FOUND)
    return classroom


@router.post("/", response_model=ClassroomResponse)
async def create_new_classroom(
    classroom: ClassroomCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new classroom"""
    # For now, use a default created_by user ID (1)
    # In a real application, this would come from authentication
    db_classroom = await create_classroom(db, classroom, created_by=1)
    return db_classroom


@router.put("/{classroom_id}", response_model=ClassroomResponse)
async def update_classroom_by_id(
    classroom_id: int,
    classroom: ClassroomUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a classroom"""
    db_classroom = await get_classroom(db, classroom_id)
    if not db_classroom:
        raise HTTPException(status_code=404, detail=CLASSROOM_NOT_FOUND)
    
    updated_classroom = await update_classroom(db, classroom_id, classroom)
    return updated_classroom


@router.delete("/{classroom_id}")
async def delete_classroom_by_id(
    classroom_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a classroom"""
    classroom = await get_classroom(db, classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail=CLASSROOM_NOT_FOUND)
    
    await delete_classroom(db, classroom_id)
    return {"message": "Classroom deleted successfully"}
